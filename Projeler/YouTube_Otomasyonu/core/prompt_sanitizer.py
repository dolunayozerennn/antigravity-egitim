"""
Prompt Sanitizer — İçerik Güvenliği Katmanı.

Kie AI (Seedance 2.0 / Veo 3.1) modellerinin content safety filtresini
tetikleyebilecek ifadeleri prompt gönderilmeden ÖNCE yumuşatır.

3 Katmanlı Savunma:
  1. Regex — Bilinen tehlikeli terimleri hızlıca yakalar (sync, <1ms)
  2. GPT Pre-flight — Prompt'u GPT'ye "bu reddedilir mi?" diye sorar (async, ~2s)
     → Reddedilecekse GPT aynı anda güvenli versiyonunu da yazar
     → 4.5 dakika Kie AI bekleme süresini kurtarır
  3. GPT Retry Rewrite — Reddedildikten sonra rejection reason ile GPT'ye
     "aynı konuyu güvenli şekilde yeniden yaz" komutu verir

Neden regex yetmiyor:
  - "steal" yakaladık ama "pilfer", "swipe", "loot" yakalanamıyor
  - Bağlam-duyarsız — "dog stole the show" güvenli ama "dog stole meat" tehlikeli
  - GPT ise anlamı anlıyor ve yaratıcılığı koruyarak yeniden yazıyor
"""
import re
import json
import logging

log = logging.getLogger("PromptSanitizer")

# ── Tehlikeli terim → güvenli alternatif eşlemeleri ──
# Her tuple: (regex pattern, replacement, açıklama)
REPLACEMENT_RULES = [
    # Hırsızlık / suç
    (r"\bsteal(?:s|ing)?\b", "grab", "hırsızlık→alma"),
    (r"\bstole\b", "grabbed", "hırsızlık→alma"),
    (r"\btheft\b", "prank", "hırsızlık→şaka"),
    (r"\bthief\b", "prankster", "hırsız→şakacı"),
    (r"\brob(?:s|bing|bed)?\b", "take", "soygun→alma"),
    (r"\brobbery\b", "commotion", "soygun→kargaşa"),
    (r"\bcrime\b", "mischief", "suç→yaramazlık"),
    (r"\bcriminal\b", "troublemaker", "suçlu→belalı"),

    # Polis / yasal otorite
    (r"\bpolice officer\b", "security guard", "polis→güvenlik"),
    (r"\bcop(?:s)?\b", "security guard", "polis→güvenlik"),
    (r"\bpolice\b", "security", "polis→güvenlik"),
    (r"\barrest(?:s|ed|ing)?\b", "catch", "tutuklama→yakalama"),
    (r"\bpulled over\b", "stopped", "çevirme→durdurma"),
    (r"\bchased by (?:a )?(?:police|cop|officer)\b", "chased by the owner", "polis kovalamacası→sahibi kovalıyor"),

    # Silah / şiddet
    (r"\bgun(?:s)?\b", "water gun", "silah→su tabancası"),
    (r"\bweapon(?:s)?\b", "toy", "silah→oyuncak"),
    (r"\bknife\b", "spatula", "bıçak→spatula"),
    (r"\bknives\b", "utensils", "bıçaklar→mutfak aletleri"),
    (r"\bblood(?:y)?\b", "red paint", "kan→kırmızı boya"),
    (r"\bviolence\b", "chaos", "şiddet→kaos"),
    (r"\bviolent\b", "chaotic", "şiddetli→kaotik"),
    (r"\bfight(?:s|ing)?\b", "wrestle", "kavga→güreş"),
    (r"\battack(?:s|ing|ed)?\b", "approach", "saldırı→yaklaşma"),
    (r"\bsmash(?:es|ed|ing)?\b", "push through", "kırma→itme"),
    (r"\bkill(?:s|ing|ed)?\b", "scare away", "öldürme→korkutma"),
    (r"\bdestroy(?:s|ed|ing)?\b", "mess up", "yıkma→dağıtma"),
    (r"\bexplod(?:e|es|ed|ing)?\b", "pop", "patlama→patlama (güvenli)"),

    # Tehlikeli hayvan etkileşimleri (çocuk bağlamında)
    (r"\bbaby .{0,30}crocodile\b", "baby and a friendly turtle", "bebek+timsah→bebek+kaplumbağa"),
    (r"\bcrocodile .{0,30}baby\b", "friendly turtle near the baby", "timsah+bebek→kaplumbağa+bebek"),
    (r"\bchild .{0,30}crocodile\b", "child and a friendly turtle", "çocuk+timsah→çocuk+kaplumbağa"),
    (r"\bkid .{0,30}crocodile\b", "kid and a friendly turtle", "çocuk+timsah→çocuk+kaplumbağa"),
    (r"\bkid .{0,30}(?:lion|tiger|shark|wolf)\b", "kid and a friendly puppy", "çocuk+yırtıcı→çocuk+köpek"),
    (r"\bbaby .{0,30}(?:lion|tiger|shark|wolf)\b", "baby and a friendly puppy", "bebek+yırtıcı→bebek+köpek"),
    (r"\b(?:bear|lion|tiger|shark) .{0,30}(?:baby|child|kid|toddler)\b", "friendly dog near the family", "yırtıcı+çocuk→köpek+aile"),

    # Trafik / araç tehlikesi
    (r"\bfloors it\b", "honks the horn", "gaza basma→korna çalma"),
    (r"\bspeeds? (?:off|away)\b", "drives slowly away", "hızla kaçma→yavaşça uzaklaşma"),
    (r"\bruns? from\b", "walks away from", "kaçma→uzaklaşma"),

    # Kaza / acil durum
    (r"\bcrash(?:es|ed|ing)?\b", "tumble", "kaza→düşme"),
    (r"\baccident\b", "incident", "kaza→olay"),
    (r"\bdrown(?:s|ed|ing)?\b", "splash", "boğulma→sıçrama"),

    # Uyuşturucu
    (r"\bdrug(?:s)?\b", "candy", "uyuşturucu→şeker"),
]

# ── Yüksek riskli pattern'ler (sadece uyarı — çıkartamıyoruz) ──
HIGH_RISK_PATTERNS = [
    (r"\bchild(?:ren)? .{0,30}(?:danger|harm|hurt|injur)", "Çocuk+tehlike"),
    (r"\bbaby .{0,30}(?:danger|harm|hurt|fall)", "Bebek+tehlike"),
    (r"\bkid .{0,30}(?:electr|outlet|socket|window)", "Çocuk+elektrik/pencere"),
    (r"\btornado .{0,20}(?:child|baby|kid)", "Doğal afet+çocuk"),
]

# ── GPT Pre-flight System Prompt ──
_PREFLIGHT_SYSTEM = """You are a content safety evaluator for AI video generation models.

Your job: Evaluate if a video prompt would be REJECTED by an AI model's safety filter.

AI video models (Seedance 2.0, Veo 3.1) reject prompts containing:
- Theft, robbery, shoplifting (even if animals are doing it)
- Police chases, arrests, criminal activity
- Weapons, guns, knives, violence, blood
- Children in dangerous situations (near predators, heights, traffic, electricity)
- Drug references
- Explicit or sexual content
- Death, killing, drowning
- Natural disasters harming people/animals

IMPORTANT: The models are VERY strict. Even playful/humorous versions of these themes get rejected.
For example: "Dog stealing meat" gets rejected even though it's cute/funny.

Respond in JSON:
{
  "safe": true/false,
  "risk_score": 1-10 (1=completely safe, 10=definitely rejected),
  "risk_reasons": ["reason1", "reason2"],
  "rewritten_prompt": "only if safe=false: rewrite preserving the SAME creative concept but making it safe. Keep camera style, keep the humor, keep the action — just replace dangerous elements with safe alternatives."
}

REWRITE RULES:
- "stealing X" -> "grabbing X" or "snatching X playfully"
- "chased by police" -> "chased by everyone" or "chased by the owner"
- "gun/weapon" -> remove entirely or replace with harmless object
- "child near danger" -> change child to adult or change danger to safe animal
- Keep the SAME energy, humor, and viral potential
- Keep the SAME camera style (bodycam, ring camera, etc.)
- The rewrite must be 40-100 words"""

# ── GPT Retry Rewrite System Prompt ──
_RETRY_REWRITE_SYSTEM = """You are a prompt repair specialist for AI video generation.

A video prompt was REJECTED by the AI model's content safety filter.
The model returned this rejection reason: "{rejection_reason}"

Your job: Rewrite the prompt to tell the SAME story but with ZERO content safety risks.

AGGRESSIVE RULES:
- Remove ALL potentially dangerous words/concepts entirely
- Replace violence with slapstick humor
- Replace crime with innocent mischief
- Replace danger with surprise
- If an animal was "stealing" -> it's "playfully grabbing" or "accidentally knocking over"
- If someone was "chased by police" -> they're "chased by a confused tourist" or "chased by a flock of geese"
- Add "family-friendly" and "wholesome" and "smooth motion" to the end
- Keep the same camera angle/style
- Keep the humor and viral potential
- Output ONLY the rewritten prompt text (40-100 words), no JSON, no explanation"""


def sanitize_prompt(prompt: str) -> tuple[str, list[str]]:
    """
    Video prompt'unu içerik güvenliği açısından temizler (SYNC — regex tabanlı).

    Hızlı birinci katman: bilinen tehlikeli kelimeleri yakalar.
    GPT pre-flight'tan ÖNCE çalışır.

    Args:
        prompt: Orijinal video generation prompt'u

    Returns:
        (sanitized_prompt, changes_made): Temizlenmiş prompt ve yapılan değişiklikler listesi
    """
    changes = []
    sanitized = prompt

    for pattern, replacement, description in REPLACEMENT_RULES:
        matches = re.findall(pattern, sanitized, flags=re.IGNORECASE)
        if matches:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            changes.append(f"{description}: '{matches[0]}' -> '{replacement}'")

    # Yüksek riskli pattern uyarıları
    for pattern, risk_name in HIGH_RISK_PATTERNS:
        if re.search(pattern, sanitized, flags=re.IGNORECASE):
            log.warning(f"⚠️ Yüksek riskli pattern tespit edildi: {risk_name}")
            changes.append(f"⚠️ UYARI: {risk_name} (manuel düzeltme gerekebilir)")

    if changes:
        log.info(f"🛡️ Prompt sanitize edildi — {len(changes)} değişiklik:")
        for change in changes:
            log.info(f"   • {change}")
    else:
        log.info("✅ Prompt güvenli — değişiklik gerekmedi")

    return sanitized, changes


def create_softened_prompt(original_prompt: str) -> str:
    """
    Content filter tarafından reddedilen bir prompt'un
    yumuşatılmış versiyonunu üretir (regex tabanlı — fallback).

    sanitize_prompt'tan daha agresif — tüm potansiyel tehlikeli
    ifadeleri tamamen yeniden yazar.
    """
    # Önce standart sanitize uygula
    softened, _ = sanitize_prompt(original_prompt)

    # Ek agresif yumuşatma — tüm olumsuz fiilleri pozitifle değiştir
    aggressive_replacements = [
        (r"\bchase[sd]?\b", "follow"),
        (r"\bchasing\b", "following"),
        (r"\bscream(?:s|ing|ed)?\b", "call out"),
        (r"\bpanic(?:s|king|ked)?\b", "surprise"),
        (r"\bfreak(?:s|ing|ed)? out\b", "react with surprise"),
        (r"\bdesperate\b", "eager"),
        (r"\bchaos\b", "excitement"),
        (r"\bchaotic\b", "lively"),
        (r"\bscare[sd]?\b", "startle"),
        (r"\bscary\b", "surprising"),
        (r"\bterrifl?(?:ied|ying)\b", "surprised"),
        (r"\baggressiv(?:e|ely)\b", "energetic"),
    ]

    for pattern, replacement in aggressive_replacements:
        softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)

    # "smooth motion" eklenmemişse ekle (model kalitesini artırır)
    if "smooth motion" not in softened.lower():
        softened += " Smooth motion, natural physics, family-friendly content."

    log.info("🛡️ Agresif yumuşatma uygulandı (regex fallback)")
    return softened


# ════════════════════════════════════════════════════════════
# GPT-POWERED SAFETY (Katman 2 + 3) — Async, Akıllı, Bağlam-Duyarlı
# ════════════════════════════════════════════════════════════

async def gpt_preflight_check(prompt: str) -> tuple[str, bool, dict]:
    """
    GPT Pre-flight Safety Check — Kie AI'a göndermeden ÖNCE prompt'u değerlendirir.

    Neden gerekli:
      - Kie AI reddedince 4.5 dakika boşa gidiyor
      - GPT aynı değerlendirmeyi 2 saniyede yapıyor
      - GPT bilinmeyen tehlikeli kelimeleri de yakalıyor (regex yakalayamaz)

    Args:
        prompt: Değerlendirilecek video prompt'u

    Returns:
        (final_prompt, was_rewritten, metadata):
          - final_prompt: Güvenli prompt (orijinal veya yeniden yazılmış)
          - was_rewritten: GPT yeniden yazdı mı?
          - metadata: {risk_score, risk_reasons, ...} — telemetri için
    """
    from config import settings

    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: GPT pre-flight atlanıyor")
        return prompt, False, {"risk_score": 0, "risk_reasons": [], "dry_run": True}

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": _PREFLIGHT_SYSTEM},
                {"role": "user", "content": f"Evaluate this video prompt:\n\n{prompt}"},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        risk_score = result.get("risk_score", 1)
        is_safe = result.get("safe", True)
        risk_reasons = result.get("risk_reasons", [])

        metadata = {
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "preflight_passed": is_safe,
        }

        if is_safe or risk_score <= 4:
            log.info(f"✅ GPT Pre-flight: GÜVENLİ (skor: {risk_score}/10)")
            return prompt, False, metadata

        # ── Riskli — GPT'nin yeniden yazmasını kullan ──
        rewritten = result.get("rewritten_prompt", "")
        if rewritten and len(rewritten) > 20:
            log.warning(
                f"🛡️ GPT Pre-flight: RİSKLİ (skor: {risk_score}/10) — "
                f"Sebepler: {', '.join(risk_reasons)}"
            )
            log.info(f"   ✏️ GPT yeniden yazdı: {rewritten[:100]}...")
            metadata["rewritten"] = True
            return rewritten, True, metadata

        # GPT rewrite başarısız — orijinali döndür, Kie AI denemesine bırak
        log.warning(f"⚠️ GPT Pre-flight: riskli ama rewrite üretemedi (skor: {risk_score})")
        return prompt, False, metadata

    except Exception as e:
        # GPT pre-flight başarısız → pipeline'ı durdurma, orijinal promptla devam et
        log.warning(f"⚠️ GPT Pre-flight hatası (atlanıyor): {e}")
        return prompt, False, {"risk_score": -1, "error": str(e)}


async def gpt_rewrite_rejected_prompt(
    original_prompt: str,
    rejection_reason: str,
) -> str:
    """
    GPT-Powered Retry Rewrite — Reddedilmiş prompt'u akıllıca yeniden yazar.

    Regex'ten farklı olarak:
      - Rejection reason'ı bağlam olarak kullanır
      - Bilinmeyen kelimeleri de halleder
      - Yaratıcılığı ve viral kaliteyi korur

    Args:
        original_prompt: Kie AI tarafından reddedilen prompt
        rejection_reason: Kie AI'ın döndürdüğü hata mesajı

    Returns:
        str: Güvenli şekilde yeniden yazılmış prompt
    """
    from config import settings

    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: GPT rewrite atlanıyor, regex fallback kullanılıyor")
        return create_softened_prompt(original_prompt)

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        system = _RETRY_REWRITE_SYSTEM.format(rejection_reason=rejection_reason)

        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Rewrite this rejected prompt:\n\n{original_prompt}"},
            ],
            temperature=0.7,
            max_tokens=300,
        )

        rewritten = response.choices[0].message.content.strip()

        # Çıktı kalite kontrolü
        if not rewritten or len(rewritten) < 20:
            log.warning("⚠️ GPT rewrite çok kısa — regex fallback kullanılıyor")
            return create_softened_prompt(original_prompt)

        # JSON wrapper'ı temizle (GPT bazen JSON döndürür)
        if rewritten.startswith("{") or rewritten.startswith('"'):
            try:
                parsed = json.loads(rewritten)
                if isinstance(parsed, dict):
                    rewritten = parsed.get("prompt", parsed.get("rewritten_prompt", rewritten))
                elif isinstance(parsed, str):
                    rewritten = parsed
            except json.JSONDecodeError:
                pass

        # Smooth motion eklenmemişse ekle
        if "smooth motion" not in rewritten.lower():
            rewritten += " Smooth motion, natural physics, family-friendly content."

        log.info(f"✏️ GPT Retry Rewrite başarılı: {rewritten[:100]}...")
        return rewritten

    except Exception as e:
        log.warning(f"⚠️ GPT rewrite hatası — regex fallback: {e}")
        return create_softened_prompt(original_prompt)

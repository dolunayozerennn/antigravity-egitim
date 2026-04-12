"""
Prompt Sanitizer — İçerik Güvenliği Katmanı.

Kie AI (Seedance 2.0 / Veo 3.1) modellerinin content safety filtresini
tetikleyebilecek ifadeleri prompt gönderilmeden ÖNCE yumuşatır.

Neden gerekli:
  - "steal", "police chase", "weapon" gibi kelimeler modellerin
    güvenlik filtresini tetikleyip 5+ dakika boşa harcıyor
  - Pipeline crash oluyor → kullanıcı deneyimi kötü
  - Auto mode (CronJob) çaresiz kalıyor

Strateji:
  1. Bilinen tehlikeli terimleri güvenli alternatifleriyle değiştir
  2. GPT'ye "yeniden yaz" komutu verip prompt'u yumuşattır
  3. Tamamen engellenememesi gereken durumlar için uyarı döndür
"""
import re
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


def sanitize_prompt(prompt: str) -> tuple[str, list[str]]:
    """
    Video prompt'unu içerik güvenliği açısından temizler.

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
            changes.append(f"{description}: '{matches[0]}' → '{replacement}'")

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
    yumuşatılmış versiyonunu üretir.

    sanitize_prompt'tan daha agresif — tüm potansiyel tehlikeli
    ifadeleri tamamen yeniden yazar.

    Args:
        original_prompt: Reddedilen orijinal prompt

    Returns:
        str: Agresif şekilde yumuşatılmış prompt
    """
    # Önce standart sanitize uygula
    softened, _ = sanitize_prompt(original_prompt)

    # Ek agresif yumuşatma — tüm olumsuz fiilleri pozitifle değiştir
    aggressive_replacements = [
        (r"\bchase[sd]?\b", "follow", ),
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

    log.info("🛡️ Agresif yumuşatma uygulandı (retry prompt)")
    return softened

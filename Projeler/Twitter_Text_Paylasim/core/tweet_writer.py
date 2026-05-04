"""Tweet Writer + Quality Scorer (v3 — kalite refactor'u).

Dolunay'ın 7 maddelik feedback'i bu prompt'lara işlendi:
  - Hook (vurucu açılış) zorunlu — somut sayı / ters köşe / tarihsel analoji / şaşırtıcı iddia.
  - Görsel-bağımlı dil yasağı — "bu video", "şu otomasyon", "yukarıdaki" kullanılamaz
    (Twitter'da görsel/video paylaşılmıyor; adı verilemeyen şey atlanır).
  - Somut adım zorunlu — numaralı liste, spesifik araç adı (Claude Desktop/Pro $20/ManyChat vs.),
    Türkçe örnek prompt, ölçülebilir sonuç.
  - Aşikar tavsiye yasağı — "AI sosyal medyayı kolaylaştırır", "geri bildirim önemlidir" gibi
    kitlenin zaten bildiği cümleler ≤6 skorla atılır.
  - Uzunluktan korkma — tek tweet sığmazsa thread.
  - Eşik 8 (config'de varsayılan).

Çıktı: structured JSON (response_format=json_object). Tek tweet veya thread.
"""

import json

from openai import OpenAI

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "TweetWriter")


SCORING_RUBRIC = """Sen Dolunay'ın X (Twitter) hesabı için içerik yazıyorsun.
Dolunay yapay zeka ve otomasyon konusunda eğitim veriyor. Hedef kitle: Türkçe konuşan,
AI'la ilgilenen herkes — yazılımcı olmayanlar dahil. Geniş bir kitle (~250K).

═══ KALİTE PUANLAMA (1-10) ═══

9-10 (mükemmel — yayınlanabilir):
  - Vurucu HOOK var (somut sayı / ters köşe / tarihsel analoji / şaşırtıcı iddia).
  - Numaralı somut adımlar var: spesifik araç adı + Türkçe örnek prompt + ölçülebilir sonuç.
  - Kitlenin BUGÜN uygulayabileceği bir şey öğretiyor.

7-8 (kabul edilebilir — eşik):
  - Hook iyi ama adımlar yumuşak, VEYA adımlar somut ama açılış yumuşak.

≤6 (otomatik düşük — atılır):
  - Görsel-bağımlı referans var: "bu video", "şu otomasyon", "yukarıdaki örnek", "şu üyemiz",
    "bu ekran". Twitter'da görsel/video paylaşılmıyor — adı verilemeyen şey atlanır.
  - Aşikar tavsiye: kitlenin zaten bildiği cümleler. Örn:
    "AI sosyal medyayı kolaylaştırır", "geri bildirim analizi önemlidir",
    "doğru yönlendirme önemli", "iletişim çok kritik".
  - Jenerik soru hook'u: "Şu sorunu yaşıyor musunuz?", "X mi zorlanıyorsunuz?".
  - Spesifik araç adı, sayı veya örnek prompt YOK.
  - Dolgu: "AI ile her şey kolay", "yapay zeka sayesinde…" tarzı içi boş övgü.
  - Promosyon/satış dili: "harika ürün", "mutlaka deneyin", marka satışı.

═══ HOOK ÖRNEKLERİ (Dolunay'ın gold-standard'ı) ═══

[Somut sayı + provoke]
"Instagram'ınızı personelinizin yönetme maliyeti ayda 10.000 TL."

[Ters köşe + sayı]
"10 dakikada bu yöntemle müşteri şikayetlerini 5 kat düşürün."

[Tarihsel analoji]
"Sanayi devriminde makine satın alan bir fabrikatörle hâlâ insan çalıştıran bir
fabrikatör yarışabilir mi? Bugün AI'da aynı kırılma noktasındayız."

[Şaşırtıcı iddia]
"Ekiplerinizin gerçekten çalışıp çalışmadığını bilmiyorsunuz."

═══ SOMUT ADIM ÖRNEĞİ (gold-standard) ═══

"10 dakikada bu yöntemle müşteri şikayetlerini 5 kat düşürün.

1. Claude Desktop uygulamasını indirin.
2. 20 dolarlık Pro paketi satın alın.
3. Code sekmesine gidin ve şu prompt'ı yazın:
   "Benim işletmemin adı [İŞLETME ADI]. İnternette hakkımda yapılan olumsuz
   bütün yorumların otomatik analiz edilip bana haftada bir mail atıldığı
   bir otomasyon kurmak istiyorum…"
4. Claude Code'un sizin yerinize otomasyonu inşa etmesini bekleyin."

═══ YAZIM KURALLARI ═══

- Sıradan biri anlasın. Teknik jargon YOK: "CI/CD", "deployment", "container", "API
  endpoint", "framework" yasak. Karşılığı: "kod yazmadan", "telefonundan", "tek tıkla",
  "otomatik çalışan akış", "yapay zekayı kendi sistemine bağlamak".
- AI yaygın kelimeleri (agent, MCP, LLM) gerekiyorsa kısa açıklama: "MCP (yapay zekayı
  dış sistemlere bağlayan protokol)".
- Türkçe, sade. Emoji YOK. Hashtag YOK.
- Görsel/video referansı YASAK (yukarıda detay).
- Tek tweet max ~270 karakter. SIĞMIYORSA thread'e böl — kalite > kısalık.
- Thread max 12 tweet. Her tweet 270 karakter sınırını aşmasın.
- Araç adlarını DOĞRU yaz (örn. "Claude Desktop", "ManyChat", "Make.com"). Emin değilsen
  jenerik anlat ("yapay zeka uygulaması") — yanlış araç adı uydurma.
- Promosyon/satış dili YASAK. Keşif/öğretme tonu.
"""


SINGLE_OR_THREAD_FORMAT = """═══ ÇIKTI FORMATI ═══

Tek tweet'e sığarsa "tweet_text" doldur, "thread_tweets" boş liste.
Sığmıyorsa "thread_tweets" doldur (her eleman bir tweet, max 270 char), "tweet_text" boş.
İkisini birden DOLDURMA.

JSON:
{
  "score": 1-10 arası int,
  "tweet_text": string (single tweet ise; aksi halde ""),
  "thread_tweets": [string, ...] (thread ise; aksi halde []),
  "skip_reason": string (skor < 7 ise nedeni; aksi halde "")
}"""


YOUTUBE_FORMAT = """═══ ÇIKTI FORMATI (YouTube) ═══

Skor >=7 ise:
  - "thread_tweets": dinamik uzunluk (4-12 tweet). Yapı: HOOK → problemi netleştirme
    → 1-2-3 numaralı adım (araç + örnek prompt + sonuç) → kapanış (video URL son tweet'te).
  - "standalone_tweets": 2-3 bağımsız tek tweet. Her biri tek başına anlamlı, somut taktik.
    Görsel-bağımlı dil YASAK — "bu videoda" diyemezsin.

JSON:
{
  "score": 1-10 arası int,
  "thread_tweets": [string, ...],
  "standalone_tweets": [string, ...],
  "skip_reason": string (skor düşükse)
}"""


def _split_to_thread(text: str, max_chars: int = 270) -> list[str]:
    """Uzun tek metni cümle bazında thread'e böler. Son çare helper'ı —
    LLM zaten thread döndürmesi gerekirken tek string verirse kullanılır."""
    if len(text) <= max_chars:
        return [text]
    parts = []
    buf = ""
    for sentence in text.replace("\n\n", " \n").split(". "):
        s = sentence.strip()
        if not s:
            continue
        candidate = (buf + " " + s + ".").strip() if buf else s + "."
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            if buf:
                parts.append(buf.strip())
            buf = s + "."
    if buf:
        parts.append(buf.strip())
    return parts[:12]


class TweetWriter:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WRITER_MODEL
        self.threshold = settings.QUALITY_THRESHOLD

    def write_for_github_repo(self, repo_data: dict) -> dict:
        user_msg = f"""KAYNAK TİPİ: GitHub repo (açık kaynak, ücretsiz)

REPO: {repo_data.get('full_name')}
URL: {repo_data.get('url')}
YILDIZ: {repo_data.get('stars')}
DİL: {repo_data.get('language', '?')}
AÇIKLAMA: {repo_data.get('description', '')}

README ÖZETİ:
{repo_data.get('readme_excerpt', '')[:3000]}

GÖREV:
- Önce reponun değerini puanla.
- Skor >={self.threshold} ise içerik üret. Yapı:
  HOOK (somut sayı / ters köşe / şaşırtıcı iddia — repo "X yapıyor" tonunda DEĞİL)
  → Repo ne yapıyor (sıradan dilde, 1-2 cümle)
  → 1 somut kullanım örneği veya "kim için faydalı + ne kazandırır"
  → Repo URL'sini son tweet'in sonuna ekle.
- "Mutlaka deneyin", "harika repo" gibi promosyon dili YASAK. Keşif tonu.
- Tek tweet sığarsa single, aksi halde thread (max 4 tweet beklenir bu kaynak için).
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\n" + SINGLE_OR_THREAD_FORMAT,
            user_msg=user_msg,
            mode="single_or_thread",
            source_url=repo_data.get('url', ''),
        )

    def write_for_ai_news(self, news_text: str) -> dict:
        user_msg = f"""KAYNAK TİPİ: AI haberi (Perplexity'den özet)

HABER:
{news_text[:4000]}

GÖREV:
- Önce haberin X kitlene değerini puanla.
- Aşikar haber ("yeni model çıktı", "X şirketi yeni özellik duyurdu") TEK BAŞINA yetmez —
  kitlenin günlük hayatına değen somut bir sonuç çıkarmıyorsa skor ≤6.
- Skor >={self.threshold} ise:
  HOOK (somut iddia / ters köşe — "yeni gelişme" değil)
  → Ne oldu, somut (1 cümle)
  → Bu, kitlenin işine ne yarar — 1-2 numaralı kullanım önerisi (araç adı + örnek prompt
    veya somut sonuç)
- Haber linki PAYLAŞMA — sadece özü ver.
- Tek tweet sığarsa single, aksi halde thread.
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\n" + SINGLE_OR_THREAD_FORMAT,
            user_msg=user_msg,
            mode="single_or_thread",
            source_url="",
        )

    def write_for_use_case(self, use_case: dict) -> dict:
        steps = use_case.get('steps') or []
        tools = use_case.get('tools') or []
        user_msg = f"""KAYNAK TİPİ: B2B AI Kullanım Senaryosu (Dolunay'ın kendi serisi)

SENARYO:
Başlık: {use_case.get('title', '')}
Hook (varsa): {use_case.get('hook', '')}
Problem: {use_case.get('problem', '') or use_case.get('scenario', '')}
Adımlar (varsa): {steps}
Araçlar: {tools}
Sonuç (outcome): {use_case.get('outcome', '') or use_case.get('takeaway', '')}

GÖREV:
- Bu senaryoyu X için içerik yap. KOBİ sahibi / yönetici / iş süreçleriyle uğraşan
  çalışan hedefli — yazılımcı DEĞİL.
- ÇOĞU USE CASE THREAD OLMALI (somut adımlar tek tweet'e sığmaz). Yapı:
  Tweet 1: HOOK (somut sayı / ters köşe / tarihsel analoji / şaşırtıcı iddia)
  Tweet 2: Problemi netleştir (kitlenin yaşadığı somut ağrı)
  Tweet 3-N: 1, 2, 3 numaralı adımlar — araç adı + Türkçe örnek prompt + sonuç
  Son tweet: Kapanış / kim için değerli (promosyon DEĞİL).
- Görsel-bağımlı dil YASAK ("bu videoda", "şu otomasyon") — adı verilemeyen şey yok.
- Aşikar tavsiye YASAK — kitlenin zaten bildiği cümleler skor ≤6.
- Marka satışı YASAK; araç adı bilgi olarak verilebilir.
- Skor >={self.threshold} olmalı; aksi halde skip_reason yaz.
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\n" + SINGLE_OR_THREAD_FORMAT,
            user_msg=user_msg,
            mode="single_or_thread",
            source_url="",
        )

    def write_for_youtube_video(self, video_data: dict) -> dict:
        user_msg = f"""KAYNAK TİPİ: Dolunay'ın YouTube videosu (script veya transkript)

BAŞLIK: {video_data.get('title')}
URL: {video_data.get('url')}
KAYNAK: {video_data.get('source', 'unknown')}  (notion=temiz script, rss=otomatik altyazı)

İÇERİK (script/transkript, kısaltılmış):
{video_data.get('transcript', '')[:8000]}

GÖREV:
- Önce videonun X kitlene değerini puanla.
- Skor >={self.threshold} ise:
  THREAD (4-12 tweet, içerik uzunluğuna göre dinamik):
    Tweet 1: HOOK (somut sayı / ters köşe / şaşırtıcı iddia — "videomda anlattım" YASAK)
    Tweet 2: Problemi netleştir
    Tweet 3-N: Ana noktaları somut anlat — araç adı + örnek prompt + sonuç
    Son tweet: Kapanış + video URL
  STANDALONE (2-3 bağımsız tweet):
    Videodan bağımsız tek başına anlamlı taktikler. "Bu videoda" YASAK — somut taktiği
    direkt anlat. Hook + 1 net adım veya iddia.
- Görsel/video referansı YASAK ("bu video", "şu klipte", "yukarıdaki").
- Aşikar tavsiye YASAK.
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\n" + YOUTUBE_FORMAT,
            user_msg=user_msg,
            mode="youtube",
            source_url=video_data.get('url', ''),
        )

    def _call_llm(self, system_msg: str, user_msg: str, mode: str, source_url: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2500,
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            data["source_url"] = source_url

            # Single_or_thread modunda: LLM yanlışlıkla tek string yazdıysa veya >270
            # karakter koyduysa thread'e otomatik böl.
            if mode == "single_or_thread":
                tt = (data.get("tweet_text") or "").strip()
                thread = data.get("thread_tweets") or []
                if not thread and tt and len(tt) > 270:
                    data["thread_tweets"] = _split_to_thread(tt)
                    data["tweet_text"] = ""
                # Thread cap (12)
                if data.get("thread_tweets") and len(data["thread_tweets"]) > 12:
                    ops.warning(f"Thread {len(data['thread_tweets'])} tweet — 12'ye kırpılıyor")
                    data["thread_tweets"] = data["thread_tweets"][:12]
            elif mode == "youtube":
                if data.get("thread_tweets") and len(data["thread_tweets"]) > 12:
                    ops.warning(f"YouTube thread {len(data['thread_tweets'])} — 12'ye kırpılıyor")
                    data["thread_tweets"] = data["thread_tweets"][:12]

            return data
        except Exception as e:
            ops.error("LLM çağrısı başarısız", exception=e)
            return {
                "score": 0,
                "skip_reason": f"LLM error: {e}",
                "source_url": source_url,
            }

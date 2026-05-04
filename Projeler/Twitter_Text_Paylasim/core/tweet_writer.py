"""Tweet Writer + Quality Scorer.

Üç tip girdi alır (GitHub repo, AI haberi, YouTube transcript) ve:
  1. 1-10 kalite skoru üretir (somut taktik / araç / sayı / TR X kitlesine değer)
  2. Skor eşik altıysa skip_reason döner, üst süzünden geçemez
  3. Skor eşik üstüyse: format'a uygun tweet (single) veya thread+adaylar üretir

Çıktı: structured JSON (OpenAI response_format=json_object).
"""

import json

from openai import OpenAI

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "TweetWriter")


SCORING_RUBRIC = """Sen bir Türk yapay zeka & otomasyon eğitmeni adına X (Twitter) için içerik yazıyorsun.
Hedef kitle: Türkçe konuşan AI/otomasyon öğrenmek isteyen geliştiriciler, indie hacker'lar, profesyoneller.

KALİTE PUANLAMA (1-10):
- 9-10: Somut taktik/araç/sayı içeriyor, hedef kitlenin BUGÜN kullanabileceği bir şey, eşsiz değer
- 7-8: Faydalı ama biraz daha jenerik veya zaten bilinen ama iyi anlatılmış
- 5-6: İlginç ama somut değer az, ya da çok niş
- 1-4: Jenerik haber, clickbait, "AI gelecek" tarzı boş, kopya içerik

YAZIM KURALLARI:
- Türkçe, sade dil. Jargon yok ama AI/otomasyon terimleri ("agent", "MCP", "LLM" vb.) doğal
- Emoji yok (X'te az kullanılıyor zaten, gereksiz)
- Hashtag yok
- Single tweet: max 270 karakter (link + soluk payı)
- Thread tweet'leri: her biri max 270 karakter
- Açılış cümlesi merak uyandırıcı, "Bunu yeni öğrendim" tarzı bilgiçlik yok
- Sonunda link varsa direkt link, "şuradan bak: " demeden
"""


class TweetWriter:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WRITER_MODEL
        self.threshold = settings.QUALITY_THRESHOLD

    def write_for_github_repo(self, repo_data: dict) -> dict:
        """repo_data: {full_name, description, url, stars, readme_excerpt, language}"""
        user_msg = f"""KAYNAK TİPİ: GitHub repo

REPO: {repo_data.get('full_name')}
URL: {repo_data.get('url')}
YILDIZ: {repo_data.get('stars')}
DİL: {repo_data.get('language', '?')}
AÇIKLAMA: {repo_data.get('description', '')}

README ÖZETİ:
{repo_data.get('readme_excerpt', '')[:3000]}

GÖREV: Bu repo benim hedef kitlem (Türkçe AI/otomasyon) için ne kadar değerli? Puanla.
Eğer skor >={self.threshold} ise, tek punchy tweet yaz: ne yapıyor + en kullanışlı tarafı + kim için + repo URL'si.
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\nFORMAT: Tek tweet (single).",
            user_msg=user_msg,
            mode="single",
            source_url=repo_data.get('url', ''),
        )

    def write_for_ai_news(self, news_text: str) -> dict:
        """news_text: Perplexity'den gelen haber özeti."""
        user_msg = f"""KAYNAK TİPİ: AI haberi

HABER:
{news_text[:4000]}

GÖREV: Bu haber X kitlem için yeterince değerli mi? Puanla.
Eğer skor >={self.threshold} ise, X-uygun tek tweet yaz: en somut nokta + bir takeaway/yorum.
LinkedIn'deki uzun versiyonun aksine X-native, kısa ve punchy olsun.
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\nFORMAT: Tek tweet (single).",
            user_msg=user_msg,
            mode="single",
            source_url="",
        )

    def write_for_youtube_video(self, video_data: dict) -> dict:
        """video_data: {title, url, transcript}"""
        user_msg = f"""KAYNAK TİPİ: YouTube videom

BAŞLIK: {video_data.get('title')}
URL: {video_data.get('url')}

TRANSKRİPT (kısaltılmış):
{video_data.get('transcript', '')[:6000]}

GÖREV: Bu videodan X için içerik çıkar. Önce videonun kalitesini puanla.
Eğer skor >={self.threshold} ise:
  1. 1 thread (5-7 tweet) yaz: video başlığını anons, sonra 3-5 ana noktayı tek tek aç, son tweet'te video URL'si
  2. Ek olarak 2-3 tek tweet adayı ("standalone") çıkar — videodan bağımsız tek başına anlamlı taktikler

JSON formatı:
{{
  "score": int,
  "thread_tweets": ["tweet1", "tweet2", ...],
  "standalone_tweets": ["tweet1", "tweet2", "tweet3"],
  "skip_reason": null
}}
"""
        return self._call_llm(
            system_msg=SCORING_RUBRIC + "\n\nFORMAT: Thread + standalone adaylar.",
            user_msg=user_msg,
            mode="youtube",
            source_url=video_data.get('url', ''),
        )

    def _call_llm(self, system_msg: str, user_msg: str, mode: str, source_url: str) -> dict:
        if mode == "single":
            schema_hint = """Çıktı JSON formatı:
{
  "score": int (1-10),
  "tweet_text": string (skor eşik altıysa boş),
  "skip_reason": string (skor eşik üstüyse boş)
}"""
        else:  # youtube
            schema_hint = """Çıktı JSON formatı:
{
  "score": int (1-10),
  "thread_tweets": [string, ...] (skor eşik altıysa boş liste),
  "standalone_tweets": [string, ...] (skor eşik altıysa boş liste),
  "skip_reason": string (skor eşik üstüyse boş)
}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg + "\n\n" + schema_hint},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            data["source_url"] = source_url
            return data
        except Exception as e:
            ops.error("LLM çağrısı başarısız", exception=e)
            return {
                "score": 0,
                "skip_reason": f"LLM error: {e}",
                "source_url": source_url,
            }

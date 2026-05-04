"""LinkedIn caption üretici + konu uygunluk filtresi (Groq LLM)."""

import json
import re
import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Video_Paylasim", "CaptionGenerator")
filter_ops = get_ops_logger("Twitter_Video_Paylasim", "SuitabilityFilter")


class SuitabilityFilter:
    """X (Twitter) için bariz uygunsuz içerikleri eler. Çok esnek — şüphede UYGUN der."""

    SYSTEM_PROMPT = (
        "Bir videonun X (Twitter) feed'i için uygun olup olmadığına karar veriyorsun. "
        "Dolunay Özeren'in profili: Dubai gayrimenkul + AI/teknoloji + iş otomasyonu içerik üreticisi. "
        "X kitlesi LinkedIn'den daha geniş ve günlük; kişisel görüş, mizah, yorum da kabul edilir. "
        "PRENSİP: ÇOK ESNEK ol. Şüphedeysen UYGUN de. Sadece BARİZ uygunsuzları ele. "
        "UYGUN olanlar: AI, otomasyon, iş, gayrimenkul, finans, kariyer, yazılım, üretkenlik, "
        "kişisel deneyim, görüş, hayat tarzı, gündem yorumu. "
        "UYGUN DEĞİL olanlar (yalnızca apaçık): hakaret/küfür içeren provokasyon, "
        "marka için zararlı içerik. "
        "Yanıtı SADECE şu JSON formatında ver: "
        '{"suitable": true|false, "reason": "kısa Türkçe gerekçe"}'
    )

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_BASE_URL
        self.model = settings.GROQ_MODEL

    def is_suitable(self, page: dict, body_text: str) -> tuple[bool, str]:
        if settings.IS_DRY_RUN:
            filter_ops.info("[DRY-RUN] Suitability check atlanıyor → uygun kabul")
            return True, "dry-run"

        source = (body_text or page.get("caption_property") or page.get("name") or "").strip()
        if not source:
            return True, "kaynak boş — varsayılan uygun"

        user_prompt = f"Video başlık: {page.get('name','')}\n\nVideo script/caption:\n{source[:2500]}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 150,
            "response_format": {"type": "json_object"},
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            data = json.loads(raw)
            suitable = bool(data.get("suitable", True))
            reason = str(data.get("reason", ""))[:200]
            filter_ops.info(f"Suitability: {'UYGUN' if suitable else 'ELENDI'} — {reason}")
            return suitable, reason
        except Exception as e:
            filter_ops.warning(f"Filter hatası ({e}) — varsayılan uygun (fail-open)")
            return True, f"filter hatası: {e}"


class CaptionGenerator:
    SYSTEM_PROMPT = (
        "Sen Dolunay Özeren'in (Dubai gayrimenkul + içerik üreticisi) X (Twitter) tweet yazarısın. "
        "Sana videonun script ham metni veriliyor. Görevin: o videoyu izlemek isteyecek TEK BİR CÜMLE üretmek. "
        "KURALLAR (hepsi zorunlu): "
        "1) Yalnızca tek cümle. İkinci cümle veya alt satır YOK. "
        "2) En fazla 280 karakter. "
        "3) 'yorumlara X yaz', 'profilimdeki link', 'etiketle' gibi closing/CTA İSTEME. "
        "4) Hashtag YOK. "
        "5) Konuyu açıklamaya çalışma — merak uyandır, ama spoiler verme. "
        "6) Türkçe, sade, samimi profesyonel ton. "
        "7) ASLA spesifik ürün/marka adı geçirme (örn. 'Rythmix', 'Suno', 'Midjourney', "
        "'LawChat' vb. — script'te bile geçse caption'a koyma). Yerine jenerik kategori "
        "kullan: 'AI müzik aracı', 'AI video üreticisi', 'AI hukuk asistanı' vb. "
        "Reklam/sponsorlu görünmesin; bilgi/tavsiye dili kullan. "
        "(İstisna: 'Claude', 'Notion', 'ChatGPT' gibi yaygın araçlar geçebilir.) "
        "Sadece cümleyi döndür, açıklama yapma, tırnak ekleme."
    )

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_BASE_URL
        self.model = settings.GROQ_MODEL

    def _call_groq(self, user_prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 200,
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            ops.error(f"Groq API hatası: {e}", exception=e)
            return ""

    @staticmethod
    def _strip_closings(body: str) -> str:
        if not body:
            return ""
        pattern = re.compile(r"\n\s*(instagram|tiktok|shorts)[\s/]*closing\s*[:：]?", re.IGNORECASE)
        m = pattern.search(body)
        return body[:m.start()].strip() if m else body.strip()

    @staticmethod
    def _enforce_single_sentence(text: str) -> str:
        if not text:
            return ""
        text = text.strip().strip('"').strip("'").strip("`").strip()
        text = text.split("\n", 1)[0].strip()
        m = re.search(r"[.!?]", text)
        if m:
            text = text[: m.end()].strip()
        if len(text) > 280:
            text = text[:277].rstrip() + "..."
        return text

    def generate(self, page: dict, body_text: str) -> str:
        if page.get("caption_property"):
            source = page["caption_property"]
            ops.info("Caption kaynağı: Notion 'Caption' property")
        elif body_text and body_text.strip():
            source = self._strip_closings(body_text)
            ops.info(f"Caption kaynağı: sayfa body ({len(source)} karakter, closing'ler hariç)")
        else:
            source = page.get("name", "")
            ops.info("Caption kaynağı: sayfa Name (fallback)")

        if not source.strip():
            return self._enforce_single_sentence(page.get("name", "Yeni içerik."))

        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Caption üretimi atlanıyor; kaynak: '{source[:80]}...'")
            return self._enforce_single_sentence(source) or "Yeni içerik."

        raw = self._call_groq(f"Video script:\n\n{source[:3000]}")
        if not raw:
            ops.warning("LLM caption boş döndü — sayfa adıyla fallback")
            return self._enforce_single_sentence(page.get("name", "Yeni içerik."))

        return self._enforce_single_sentence(raw)

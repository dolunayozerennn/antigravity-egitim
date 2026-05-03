"""LinkedIn caption üretici — Groq LLM, tek cümle hard rule."""

import re
import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("LinkedIn_Video_Paylasim", "CaptionGenerator")


class CaptionGenerator:
    SYSTEM_PROMPT = (
        "Sen Dolunay Özeren'in (Dubai gayrimenkul + içerik üreticisi) LinkedIn caption yazarısın. "
        "Sana videonun script ham metni veriliyor. Görevin: o videoyu izlemek isteyecek TEK BİR CÜMLE üretmek. "
        "KURALLAR (hepsi zorunlu): "
        "1) Yalnızca tek cümle. İkinci cümle veya alt satır YOK. "
        "2) En fazla 280 karakter. "
        "3) 'yorumlara X yaz', 'profilimdeki link', 'etiketle' gibi closing/CTA İSTEME. "
        "4) Hashtag YOK. "
        "5) Konuyu açıklamaya çalışma — merak uyandır, ama spoiler verme. "
        "6) Türkçe, sade, samimi profesyonel ton. "
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

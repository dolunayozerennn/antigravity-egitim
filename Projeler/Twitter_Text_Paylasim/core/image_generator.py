"""Kie AI ile görsel üretim — AI Use Case serisi için.

Model: gpt-image-2-text-to-image (memory: kie_ai_gpt_image_2.md — suffix gerekli)
Aspect ratio: 1:1 (X feed'de kare görsel single tweet'te en okunaklı)

Akış:
  1. GPT-4o-mini ile İngilizce görsel promptu üret
  2. Kie AI'ya task gönder
  3. Polling ile sonucu bekle, URL al
  4. Lokale indir (Typefully'ye upload için path lazım)
"""

import os
import tempfile
import time

import requests
from openai import OpenAI

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "ImageGenerator")

KIE_BASE = "https://api.kie.ai/api/v1"
# nano-banana-2 — Kie AI'da gpt-image-2-text-to-image 500 atıyor (eCom_Reklam_Otomasyonu notu)
KIE_MODEL = "nano-banana-2"


class ImageGenerator:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_image_for_use_case(self, tweet_text: str, takeaway: str = "") -> tuple[str, str]:
        """Tweet metninden görsel üret. Returns (local_path, kie_url) or ('', '')."""
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Görsel üretim atlandı")
            return ("", "")

        prompt = self._build_image_prompt(tweet_text, takeaway)
        if not prompt:
            return ("", "")

        kie_url = self._generate_via_kie(prompt)
        if not kie_url:
            return ("", "")

        local_path = self._download(kie_url)
        return (local_path, kie_url)

    def _build_image_prompt(self, tweet_text: str, takeaway: str) -> str:
        """Tweet'ten İngilizce minimal diagram-style görsel promptu üret."""
        system = (
            "You craft minimalist illustration prompts for Twitter/X visuals. "
            "Style: clean, modern, schematic / diagram-style infographic. "
            "Mood: professional but approachable, like a top tech newsletter cover. "
            "Output: ONLY the image generation prompt in English, no preamble."
        )
        user = (
            f"Tweet (Turkish): {tweet_text}\n"
            f"Takeaway (Turkish): {takeaway}\n\n"
            "Create a minimalist English image prompt that visualizes the core concept. "
            "Square 1:1 ratio. No text inside the image (or only 1-2 short English keywords). "
            "Limited color palette (2-3 colors). Soft gradients OK. White or off-white background. "
            "Suitable for B2B AI use-case content."
        )
        try:
            r = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            prompt = r.choices[0].message.content.strip()
            ops.info(f"Görsel prompt üretildi ({len(prompt)} char)")
            return prompt
        except Exception as e:
            ops.error("Görsel prompt üretme hatası", exception=e)
            return ""

    def _generate_via_kie(self, prompt: str) -> str:
        """Kie AI'a task gönder (jobs/createTask), recordInfo ile polling, image URL döner."""
        headers = {
            "Authorization": f"Bearer {settings.KIE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": KIE_MODEL,
            "input": {
                "prompt": prompt,
                "aspect_ratio": "1:1",
            },
        }
        try:
            r = requests.post(f"{KIE_BASE}/jobs/createTask", headers=headers,
                              json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            task_id = (data.get("data") or {}).get("taskId")
            if not task_id:
                ops.error("Kie AI taskId yok", message=str(data)[:300])
                return ""
            ops.info(f"Kie AI task: {task_id}")
        except Exception as e:
            ops.error("Kie AI createTask hatası", exception=e)
            return ""

        # Polling: GET jobs/recordInfo?taskId=...
        poll_url = f"{KIE_BASE}/jobs/recordInfo"
        for i in range(36):  # ~3 dk
            time.sleep(5)
            try:
                pr = requests.get(poll_url, headers=headers,
                                  params={"taskId": task_id}, timeout=15)
                pr.raise_for_status()
                pd = pr.json()
                d = pd.get("data") or {}
                state = (d.get("state") or "").lower()
                if state in ("success", "completed", "succeeded"):
                    result = d.get("resultJson") or d.get("result") or {}
                    if isinstance(result, str):
                        import json as _json
                        try: result = _json.loads(result)
                        except Exception: result = {}
                    urls = result.get("resultUrls") or result.get("urls") or []
                    if urls and isinstance(urls, list):
                        ops.info(f"Görsel URL hazır: {urls[0][:80]}…")
                        return urls[0]
                    ops.error("Kie AI tamam ama URL yok", message=str(pd)[:300])
                    return ""
                if state in ("failed", "error"):
                    ops.error(f"Kie AI task FAILED: {d.get('failMsg') or d.get('errorMsg','?')}")
                    return ""
            except Exception as e:
                ops.warning(f"Kie polling hatası: {e}")
        ops.error("Kie AI polling timeout (3dk)")
        return ""

    def _download(self, url: str) -> str:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            fd, path = tempfile.mkstemp(suffix=".png", prefix="usecase_")
            with os.fdopen(fd, "wb") as f:
                f.write(r.content)
            ops.info(f"Görsel indirildi: {path} ({len(r.content)//1024}KB)")
            return path
        except Exception as e:
            ops.error("Görsel indirme hatası", exception=e)
            return ""

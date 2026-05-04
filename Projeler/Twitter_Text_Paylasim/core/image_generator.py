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
        """Tweet'ten İngilizce ultra-realistic photography promptu üret."""
        system = (
            "You craft ULTRA-REALISTIC PHOTOGRAPHY prompts for Twitter/X visuals — "
            "real-world, dramatic, scroll-stopping editorial photography. NOT illustration, "
            "NOT diagram, NOT infographic, NOT minimal vector art. Think Magnum Photos / "
            "National Geographic / WSJ photo essay quality.\n\n"
            "ABSOLUTE RULES — your prompt MUST enforce these:\n"
            "  (a) PHOTOREALISTIC. The output must look like a real photograph captured by "
            "      a professional photographer with a high-end camera (e.g. 'shot on Canon "
            "      EOS R5, 35mm lens, natural light, shallow depth of field, photojournalistic'). "
            "      No illustration, no 3D render, no cartoon, no flat design.\n"
            "  (b) DRAMATIC + SCROLL-STOPPING. Choose a specific real-world moment that "
            "      visually captures the tweet's tension (e.g. for 'wasted inventory': "
            "      a real warehouse aisle with cardboard boxes spilling onto the floor, "
            "      one box mid-fall; for 'lost sales': empty store shelves with a single "
            "      'sold out' tag dangling; for 'manual work overload': a tired person at "
            "      desk surrounded by paper stacks at 2am with desk lamp glow). The metaphor "
            "      must be CONCRETE and PHYSICAL, not abstract.\n"
            "  (c) NO TEXT inside the image. No English words, no Turkish words, no numbers, "
            "      no signs with readable text, no labels, no logos. Any incidental writing "
            "      in the scene must be blurred or out of frame.\n"
            "  (d) Single focal subject. Editorial composition. Cinematic lighting.\n"
            "  (e) End your prompt with this negative-prompt line: "
            "'Avoid: illustration, cartoon, 3D render, flat design, vector art, infographic, "
            "diagram, icons, text, words, letters, numbers, labels, logos, watermarks, "
            "AI-generated artifacts, oversaturated colors, stock-photo cliché smiles.'\n\n"
            "Output: ONLY the image generation prompt in English, no preamble."
        )
        user = (
            f"Tweet (Turkish, source content): {tweet_text}\n"
            f"Takeaway (Turkish): {takeaway}\n\n"
            "Translate the core tension/metaphor of this tweet into a SPECIFIC real-world "
            "photographic moment. Be concrete: name the location, the object(s), the lighting, "
            "the time of day, the camera angle. Square 1:1 ratio. "
            "Photorealistic, editorial documentary style, cinematic. "
            "Remember: real photograph not illustration, zero text in image, single focal subject, "
            "dramatic and scroll-stopping."
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
        # Photorealistic prompt'lar nano-banana-2'de bazen 3dk'yı aşıyor — 6dk'ya çekildi.
        poll_url = f"{KIE_BASE}/jobs/recordInfo"
        for i in range(72):  # ~6 dk
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
        ops.error("Kie AI polling timeout (6dk)")
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

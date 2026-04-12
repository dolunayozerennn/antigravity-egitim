"""
Kie Client — Seedance 2.0 + Veo 3.1 Unified API Client.
İki modeli aynı interface ile yönetir,
farklı endpoint ve payload yapılarını soyutlar.
"""
import json
import asyncio
import logging
import httpx
from config import settings

log = logging.getLogger("KieClient")

# ── Model konfigürasyonları ──
MODEL_CONFIG = {
    "seedance-2": {
        "model_id": "bytedance/seedance-2",
        "create_url": "/jobs/createTask",
        "poll_url": "/jobs/recordInfo",
        "uses_input_wrapper": True,
    },
    "veo3.1": {
        "model_id": "veo3_fast",
        "create_url": "/veo/generate",
        "poll_url": "/veo/record-info",
        "uses_input_wrapper": False,  # Flat JSON
    },
}

# Orientation → aspect_ratio mapping
ORIENTATION_MAP = {
    "portrait": "9:16",
    "landscape": "16:9",
}


class KieClient:
    """Seedance 2.0 + Veo 3.1 unified API client."""

    def __init__(self):
        self._base_url = settings.KIE_BASE_URL
        self._api_key = settings.KIE_API_KEY

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def create_video(
        self,
        model: str,
        prompt: str,
        orientation: str = "portrait",
        duration: int = 10,
        audio: bool = True,
        resolution: str = "720p",
    ) -> str:
        """
        Tek bir video üretir.

        Args:
            model: "seedance-2" veya "veo3.1"
            prompt: Video prompt'u
            orientation: "portrait" veya "landscape"
            duration: Saniye (4-15 arası, Seedance)
            audio: Ses üretimi
            resolution: "480p" veya "720p" (sadece Seedance)

        Returns:
            str: Üretilen videonun CDN URL'si
        """
        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN: Mock video ({model}) üretiliyor...")
            await asyncio.sleep(2)
            return f"https://cdn.example.com/dry-run-{model}-mock.mp4"

        cfg = MODEL_CONFIG.get(model)
        if not cfg:
            raise ValueError(f"Bilinmeyen model: {model}. Geçerli: {list(MODEL_CONFIG.keys())}")

        aspect_ratio = ORIENTATION_MAP.get(orientation, "9:16")

        # ── Task oluştur ──
        task_id = await self._create_task(cfg, prompt, aspect_ratio, duration, audio, resolution)
        log.info(f"📋 Task oluşturuldu ({cfg['model_id']}): {task_id}")

        # ── İlk bekleme ──
        initial_wait = settings.POLL_INITIAL_WAIT
        log.info(f"⏳ İlk bekleme: {initial_wait} saniye...")
        await asyncio.sleep(initial_wait)

        # ── Polling ──
        video_url = await self._poll_for_result(cfg, task_id)
        return video_url

    async def create_videos_batch(
        self,
        model: str,
        scenes: list[dict],
        orientation: str = "portrait",
        audio: bool = True,
        resolution: str = "720p",
    ) -> list[str]:
        """
        Çoklu sahne üretimi — sıralı olarak üretir (paralel değil, rate limit'e uyar).

        Args:
            scenes: [{"prompt": "...", "duration": 10}, ...]

        Returns:
            list[str]: Video URL'leri listesi
        """
        video_urls = []
        total = len(scenes)

        for i, scene in enumerate(scenes, 1):
            log.info(f"🎬 Sahne {i}/{total} üretiliyor...")
            url = await self.create_video(
                model=model,
                prompt=scene["prompt"],
                orientation=orientation,
                duration=scene.get("duration", settings.DEFAULT_DURATION),
                audio=audio,
                resolution=resolution,
            )
            video_urls.append(url)
            log.info(f"✅ Sahne {i}/{total} tamamlandı: {url[:60]}...")

            # Sahneler arasında kısa bekleme (rate limit)
            if i < total:
                log.info("⏳ Sahneler arası 5s bekleme...")
                await asyncio.sleep(5)

        return video_urls

    async def _create_task(
        self,
        cfg: dict,
        prompt: str,
        aspect_ratio: str,
        duration: int,
        audio: bool,
        resolution: str,
    ) -> str:
        """Model'e göre doğru endpoint ve payload ile task oluşturur."""
        url = f"{self._base_url}{cfg['create_url']}"

        if cfg["uses_input_wrapper"]:
            # ── Seedance 2.0: input wrapper ──
            payload = {
                "model": cfg["model_id"],
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "duration": duration,
                    "generate_audio": audio,
                    "web_search": False,
                },
            }
        else:
            # ── Veo 3.1: flat JSON ──
            payload = {
                "model": cfg["model_id"],
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "mode": "TEXT_2_VIDEO",
            }

        log.info(f"🎬 {cfg['model_id']} task oluşturuluyor...")
        log.info(f"   Aspect: {aspect_ratio} | Duration: {duration}s | Audio: {audio}")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload, headers=self._headers())

        if response.status_code != 200:
            log.error(f"❌ Task oluşturma başarısız: HTTP {response.status_code}")
            log.error(f"   Yanıt: {response.text[:300]}")
            raise RuntimeError(f"Kie AI createTask başarısız: {response.status_code} — {response.text[:300]}")

        data = response.json()

        # Hata kodu kontrolü
        code = data.get("code", 200)
        if code != 200:
            error_msg = data.get("msg", "Bilinmeyen hata")
            log.error(f"❌ Kie AI hata kodu: {code} — {error_msg}")
            raise RuntimeError(f"Kie AI hata: {code} — {error_msg}")

        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError(f"Task ID alınamadı. Yanıt: {data}")

        return task_id

    async def _poll_for_result(self, cfg: dict, task_id: str) -> str:
        """Task durumunu sorgular ve video URL'sini döndürür."""
        url = f"{self._base_url}{cfg['poll_url']}"
        interval = settings.POLL_INTERVAL
        max_attempts = settings.POLL_MAX_ATTEMPTS
        consecutive_429 = 0  # Exponential backoff sayacı

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.get(
                        url,
                        params={"taskId": task_id},
                        headers=self._headers(),
                    )

                    if response.status_code == 429:
                        consecutive_429 += 1
                        wait_time = min(interval * (2 ** consecutive_429), 120)  # Max 120s
                        log.warning(f"⚠️ Rate limit! Exponential backoff: {wait_time}s (#{consecutive_429})...")
                        await asyncio.sleep(wait_time)
                        continue

                    # 429 olmayan başarılı yanıt → sayacı sıfırla
                    consecutive_429 = 0

                    resp_data = response.json()
                    data = resp_data.get("data", {})
                    state = data.get("state", "unknown")

                    if state in ("success", "completed"):
                        video_url = self._extract_video_url(data)
                        if not video_url:
                            raise RuntimeError(f"Video URL bulunamadı. data: {data}")

                        log.info(f"✅ Video hazır! ({attempt} deneme)")
                        log.info(f"   URL: {video_url[:80]}...")
                        return video_url

                    elif state in ("failed", "fail"):
                        fail_msg = data.get("failMsg", "Bilinmeyen hata")
                        log.error(f"❌ Video üretimi başarısız: {fail_msg}")
                        raise RuntimeError(f"Video üretimi başarısız: {fail_msg}")

                    else:
                        log.info(f"   [{attempt}/{max_attempts}] Durum: {state}... ({interval}s sonra tekrar)")
                        await asyncio.sleep(interval)

                except httpx.RequestError as e:
                    log.warning(f"⚠️ Polling ağ hatası (deneme {attempt}): {e}")
                    await asyncio.sleep(interval)

        raise RuntimeError(
            f"Video üretimi zaman aşımı! {max_attempts} deneme sonunda tamamlanmadı. "
            f"Task ID: {task_id}"
        )

    def _extract_video_url(self, data: dict) -> str | None:
        """Farklı response formatlarından video URL'sini çıkarır."""
        # Veo formatı: doğrudan video_url
        if data.get("video_url"):
            return data["video_url"]

        # Seedance formatı: resultJson içinde
        result_json_str = data.get("resultJson", "{}")
        try:
            result_obj = json.loads(result_json_str) if isinstance(result_json_str, str) else result_json_str
        except json.JSONDecodeError:
            result_obj = {}

        if isinstance(result_obj, dict):
            urls = result_obj.get("resultUrls", [])
            if urls:
                return urls[0]
            if result_obj.get("resultUrl"):
                return result_obj["resultUrl"]
            if result_obj.get("url"):
                return result_obj["url"]

        # Genel fallback
        if data.get("resultUrls"):
            return data["resultUrls"][0]

        return None

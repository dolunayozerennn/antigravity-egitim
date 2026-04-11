"""
Seedance 2.0 Client — Kie AI API üzerinden video üretimi.
Akıllı polling ile exponential backoff ve retry mekanizması.
"""
import time
import json
import requests
from config import settings
from logger import get_logger

log = get_logger("SeedanceClient")


def create_video(prompt: str) -> str:
    """
    Seedance 2.0 ile text-to-video üretir.
    
    Args:
        prompt: Video üretim prompt'u
        
    Returns:
        str: Üretilen videonun CDN URL'si
        
    Raises:
        RuntimeError: Video üretimi başarısız olduğunda
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock video URL döndürülüyor...")
        time.sleep(2)  # Gerçekçi gecikme
        return "https://cdn.example.com/dry-run-mock-video.mp4"

    # ── Task Oluştur ──
    task_id = _create_task(prompt)
    log.info(f"📋 Task oluşturuldu: {task_id}")

    # ── İlk Bekleme ──
    log.info(f"⏳ İlk bekleme: {settings.POLL_INITIAL_WAIT} saniye...")
    time.sleep(settings.POLL_INITIAL_WAIT)

    # ── Akıllı Polling ──
    video_url = _poll_for_result(task_id)
    return video_url


def _create_task(prompt: str) -> str:
    """Kie AI'da Seedance 2.0 task'ı oluşturur."""
    url = f"{settings.KIE_BASE_URL}/jobs/createTask"

    payload = {
        "model": settings.VIDEO_MODEL,
        "input": {
            "prompt": prompt,
            "aspect_ratio": settings.VIDEO_ASPECT_RATIO,
            "resolution": settings.VIDEO_RESOLUTION,
            "duration": settings.VIDEO_DURATION,
            "generate_audio": settings.GENERATE_AUDIO,
            "web_search": False
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.KIE_API_KEY}",
        "Content-Type": "application/json"
    }

    log.info(f"🎬 Seedance 2.0 task oluşturuluyor...")
    log.info(f"   Model: {settings.VIDEO_MODEL}")
    log.info(f"   Süre: {settings.VIDEO_DURATION}s | Çözünürlük: {settings.VIDEO_RESOLUTION}")
    log.info(f"   Aspect Ratio: {settings.VIDEO_ASPECT_RATIO} | Audio: {settings.GENERATE_AUDIO}")

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code != 200:
        log.error(f"❌ Task oluşturma başarısız: HTTP {response.status_code}")
        log.error(f"   Yanıt: {response.text}")
        raise RuntimeError(f"Kie AI createTask başarısız: {response.status_code} — {response.text}")

    data = response.json()

    if data.get("code") != 200:
        error_msg = data.get("msg", "Bilinmeyen hata")
        log.error(f"❌ Kie AI hata kodu: {data.get('code')} — {error_msg}")
        raise RuntimeError(f"Kie AI hata: {data.get('code')} — {error_msg}")

    task_id = data.get("data", {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"Task ID alınamadı. Yanıt: {data}")

    return task_id


def _poll_for_result(task_id: str) -> str:
    """
    Task durumunu sorgular ve video URL'sini döndürür.
    Exponential backoff ile rate limit'e uyar.
    """
    url = f"{settings.KIE_BASE_URL}/jobs/recordInfo"
    headers = {
        "Authorization": f"Bearer {settings.KIE_API_KEY}",
        "Content-Type": "application/json"
    }

    interval = settings.POLL_INTERVAL
    max_attempts = settings.POLL_MAX_ATTEMPTS

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                url,
                params={"taskId": task_id},
                headers=headers,
                timeout=30
            )

            if response.status_code == 429:
                # Rate limit — geri çekil
                wait_time = min(interval * 2, 60)
                log.warning(f"⚠️ Rate limit! {wait_time}s bekleniyor...")
                time.sleep(wait_time)
                continue

            data = response.json().get("data", {})
            state = data.get("state", "unknown")

            if state in ("success", "completed"):
                # Video hazır!
                result_json_str = data.get("resultJson", "{}")
                try:
                    result_obj = json.loads(result_json_str) if isinstance(result_json_str, str) else result_json_str
                except json.JSONDecodeError:
                    result_obj = {}

                # URL'yi bul
                video_url = None
                if isinstance(result_obj, dict):
                    urls = result_obj.get("resultUrls", [])
                    if urls:
                        video_url = urls[0]
                    elif result_obj.get("resultUrl"):
                        video_url = result_obj["resultUrl"]
                    elif result_obj.get("url"):
                        video_url = result_obj["url"]

                if not video_url:
                    raise RuntimeError(f"Video URL bulunamadı. resultJson: {result_json_str}")

                log.info(f"✅ Video hazır! ({attempt} deneme)")
                log.info(f"   URL: {video_url[:80]}...")
                return video_url

            elif state in ("failed", "fail"):
                fail_msg = data.get("failMsg", "Bilinmeyen hata")
                log.error(f"❌ Video üretimi başarısız: {fail_msg}")
                raise RuntimeError(f"Seedance video üretimi başarısız: {fail_msg}")

            else:
                # Hâlâ işleniyor
                log.info(f"   [{attempt}/{max_attempts}] Durum: {state}... ({interval}s sonra tekrar)")
                time.sleep(interval)

        except requests.RequestException as e:
            log.warning(f"⚠️ Polling ağ hatası (deneme {attempt}): {e}")
            time.sleep(interval)

    # Timeout
    raise RuntimeError(
        f"Video üretimi zaman aşımı! {max_attempts} deneme sonunda tamamlanmadı. "
        f"Task ID: {task_id}"
    )

#!/usr/bin/env python3
"""
Reklam Video Pipeline — Topuklu Ayakkabı
==========================================
1. Görseli ImgBB'ye yükle → public URL
2. Seedance 2.0 (Kie AI) → Image-to-Video
3. ElevenLabs → Türkçe seslendirme
4. FFmpeg → Video + Ses birleştir
"""

import base64
import json
import os
import subprocess
import sys
import time

import requests

# ── Credentials ──
KIE_API_KEY = "0bf01128b0840e22108b95e484b09f76"
KIE_BASE_URL = "https://api.kie.ai/api/v1"
ELEVENLABS_API_KEY = "sk_e01cf2f30e32582b063fe849e55ad7da262de33014cf9f4b"
IMGBB_API_KEY = "b7f0689f94db6510ed2ab3785a670ba1"

# ── Çıktı Dizini ──
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Reklam Metni (Türkçe) ──
REKLAM_METNI = (
    "Zarafet, her adımda hissedilir. "
    "Kırmızının gücüyle kendine güvenle yürü. "
    "Cesur, şık ve unutulmaz… "
    "Çünkü tarz, detaylarda gizlidir."
)

# ── Video Prompt (İngilizce — Seedance 2.0) ──
VIDEO_PROMPT = (
    "Cinematic product showcase of elegant glossy red patent leather stiletto high-heels. "
    "Camera slowly orbits around the shoes placed on a sleek reflective dark marble surface. "
    "Dramatic studio lighting with warm golden highlights and soft bokeh in the background. "
    "Premium luxury fashion commercial aesthetic. Shallow depth of field, ultra smooth camera movement. "
    "Photorealistic, raw camera footage quality, 4K commercial production."
)


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ─────────────────────────────────────────
# STEP 1: Görseli ImgBB'ye Yükle
# ─────────────────────────────────────────
def upload_image_to_imgbb() -> str:
    """Kırmızı topuklu ayakkabı görselini ImgBB'ye yükler."""
    log("📸 Görsel indiriliyor ve ImgBB'ye yükleniyor...")

    # Önce görseli workspace'e indir
    img_local = os.path.join(OUTPUT_DIR, "red_stiletto_input.png")

    # Workspace'deki dosyayı kontrol et
    if os.path.exists(img_local) and os.path.getsize(img_local) > 1000:
        log("   Görsel zaten mevcut, tekrar indirilmeyecek.")
    else:
        # Stok görseli indir — yüksek kaliteli kırmızı topuklu
        stock_url = "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=1024&q=90"
        resp = requests.get(stock_url, timeout=30)
        resp.raise_for_status()
        with open(img_local, "wb") as f:
            f.write(resp.content)
        log(f"   Görsel indirildi: {len(resp.content)} bytes")

    # ImgBB'ye yükle
    with open(img_local, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": b64},
        timeout=60,
    )
    resp.raise_for_status()
    url = resp.json()["data"]["url"]
    log(f"✅ ImgBB yükleme tamam: {url}")
    return url


# ─────────────────────────────────────────
# STEP 2: Seedance 2.0 Video Üretimi
# ─────────────────────────────────────────
def create_seedance_video(image_url: str) -> str:
    """Seedance 2.0 ile Image-to-Video görevi oluşturur, task_id döner."""
    log("🎬 Seedance 2.0 video görevi oluşturuluyor...")

    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "bytedance/seedance-2",
        "input": {
            "prompt": VIDEO_PROMPT,
            "first_frame_url": image_url,
            "duration": 10,
            "aspect_ratio": "9:16",
            "generate_audio": False,  # Kendi sesimizi ekleyeceğiz
            "web_search": False,
        },
    }

    resp = requests.post(
        f"{KIE_BASE_URL}/jobs/createTask",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 200:
        raise RuntimeError(f"Kie AI hata: {data}")

    task_id = data["data"]["taskId"]
    log(f"✅ Seedance task oluşturuldu: {task_id}")
    return task_id


def poll_kie_task(task_id: str, max_attempts: int = 90) -> list[str]:
    """Kie AI görevini polling ile takip eder, sonuç URL'lerini döner."""
    log(f"⏳ Video üretimi bekleniyor (task: {task_id})...")

    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_attempts + 1):
        resp = requests.get(
            f"{KIE_BASE_URL}/jobs/recordInfo",
            params={"taskId": task_id},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        state = data.get("data", {}).get("state", "unknown")

        if state == "success":
            result_json = data["data"].get("resultJson", "{}")
            parsed = json.loads(result_json) if isinstance(result_json, str) else result_json
            urls = parsed.get("resultUrls", [])
            log(f"✅ Video hazır! {len(urls)} dosya, {attempt} deneme")
            return urls

        if state in ("failed", "fail"):
            fail_msg = data["data"].get("failMsg", "Bilinmeyen hata")
            raise RuntimeError(f"Video üretimi başarısız: {fail_msg}")

        log(f"   Polling [{attempt}/{max_attempts}] state={state}")
        time.sleep(10)

    raise RuntimeError("Video üretimi zaman aşımına uğradı")


# ─────────────────────────────────────────
# STEP 3: ElevenLabs Türkçe Seslendirme
# ─────────────────────────────────────────
def generate_voiceover(text: str) -> bytes:
    """ElevenLabs ile Türkçe ses üretir, MP3 bytes döner."""
    log("🔊 ElevenLabs Türkçe seslendirme üretiliyor...")

    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Sarah — olgun kadın sesi

    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_v3",
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.45,
                "use_speaker_boost": True,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    audio = resp.content

    if len(audio) < 100:
        raise RuntimeError("ElevenLabs boş ses döndürdü")

    log(f"✅ Ses üretildi: {len(audio)} bytes")
    return audio


# ─────────────────────────────────────────
# STEP 4: Video + Ses Birleştirme (FFmpeg)
# ─────────────────────────────────────────
def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> str:
    """FFmpeg ile video ve sesi birleştirir."""
    log("🔧 FFmpeg ile video + ses birleştiriliyor...")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg hatası: {result.stderr[-500:]}")

    log(f"✅ Final video oluşturuldu: {output_path}")
    return output_path


# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────
def main():
    log("🚀 Reklam Video Pipeline başlatılıyor...")
    log(f"   Reklam metni: {REKLAM_METNI[:60]}...")

    # Step 1: ImgBB Upload
    image_url = upload_image_to_imgbb()

    # Step 2: Seedance 2.0 Video (async — paralel başlat)
    video_task_id = create_seedance_video(image_url)

    # Step 3: ElevenLabs TTS (video beklerken paralel çalışsın)
    audio_bytes = generate_voiceover(REKLAM_METNI)
    audio_path = os.path.join(OUTPUT_DIR, "reklam_voiceover.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    log(f"💾 Ses kaydedildi: {audio_path}")

    # Step 2 devam: Video polling
    video_urls = poll_kie_task(video_task_id)
    if not video_urls:
        raise RuntimeError("Video URL'si döndürülmedi")

    video_url = video_urls[0]
    log(f"📥 Video indiriliyor: {video_url[:80]}...")

    # Video indir
    video_resp = requests.get(video_url, timeout=120)
    video_resp.raise_for_status()
    raw_video_path = os.path.join(OUTPUT_DIR, "reklam_raw_video.mp4")
    with open(raw_video_path, "wb") as f:
        f.write(video_resp.content)
    log(f"💾 Ham video kaydedildi: {raw_video_path} ({len(video_resp.content)} bytes)")

    # Step 4: FFmpeg Merge
    final_path = os.path.join(OUTPUT_DIR, "topuklu_ayakkabi_reklam_final.mp4")
    merge_video_audio(raw_video_path, audio_path, final_path)

    log("=" * 50)
    log("🎉 REKLAM VİDEOSU TAMAMLANDI!")
    log(f"   📁 Final: {final_path}")
    log(f"   📁 Ham video: {raw_video_path}")
    log(f"   📁 Ses: {audio_path}")
    log("=" * 50)


if __name__ == "__main__":
    main()

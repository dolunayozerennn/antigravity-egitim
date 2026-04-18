#!/usr/bin/env python3
from __future__ import annotations

"""
YouTube Otomasyonu V3 — "Pets Got Talent" Tam Otonom Pipeline
=============================================================
Her gün otomatik çalışır: yaratıcı senaryo üretir → video üretir →
YouTube Shorts olarak yükler.

Telegram YOK — CronJob ile tetiklenir, insan müdahalesi gerektirmez.

Çalıştırma:
  python main.py                → Tam pipeline (CronJob bu komutu çalıştırır)
  python main.py --dry-run      → Gerçek üretim yapmadan test
  python main.py --check        → Sistem sağlık kontrolü

Railway CronJob: `python main.py` — günde 1x tetiklenir.
"""
import os
import sys
import time
import asyncio
import logging
import argparse

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from logger import get_logger
from core.prompt_generator import generate_prompts
from infrastructure.kie_client import KieClient, ContentFilterError
from infrastructure.replicate_merger import merge_videos
from infrastructure.video_downloader import download_video, cleanup_video
from infrastructure.youtube_uploader import upload_to_youtube
from infrastructure.notion_logger import NotionTracker

log = get_logger("PetsGotTalent")


# ────────────────────────────────────────
# 📋 TEKRAR ÖNLEME (Notion-backed)
# ────────────────────────────────────────

def load_used_combos() -> list[str]:
    """
    Notion'dan son 60 günün kullanılan combo_key'lerini yükler.
    Hata durumunda boş liste döner (pipeline durmaz).
    """
    try:
        tracker = NotionTracker()
        combos = tracker.get_used_combos(days=60)
        log.info(f"📋 Son 60 günde {len(combos)} benzersiz senaryo kullanılmış")
        return combos
    except Exception as e:
        log.warning(f"⚠️ Kullanılan senaryolar yüklenemedi (devam ediliyor): {e}")
        return []


# ────────────────────────────────────────
# ⚙️ ANA PİPELINE
# ────────────────────────────────────────

async def run_pipeline(dry_run: bool = False):
    """
    Tam otonom video üretim pipeline'ı.

    Akış:
      1. Tekrar önleme → kullanılan senaryoları yükle
      2. Creative Engine + GPT → senaryo + prompt üret
      3. Seedance 2.0 → video üret (dinamik klip sayısı ve süre)
      4. Replicate → birleştir (gerekirse)
      5. YouTube → Shorts olarak yükle
      6. Notion → log kaydet

    Content filter retry: 3 farklı senaryo dener.
    """
    if dry_run:
        # GÜVENLİ: main.py her zaman ayrı CronJob process'i olarak çalışır
        settings.IS_DRY_RUN = True
        settings.ENV = "development"

    mode = "DRY-RUN" if settings.IS_DRY_RUN else "PRODUCTION"
    log.info(f"🚀 Pets Got Talent V3 başlatılıyor... (Mod: {mode})")
    log.info(f"   Model: {settings.DEFAULT_MODEL}")
    log.info(f"   YouTube Upload: {'Aktif' if settings.YOUTUBE_ENABLED else 'Devre Dışı'}")
    log.info(f"   Notion Log: {'Aktif' if settings.NOTION_ENABLED else 'Devre Dışı'}")

    # ── Tekrar önleme ──
    used_combos = load_used_combos()

    # ── Content filter retry — 3 farklı senaryo dene ──
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await _execute_pipeline(used_combos)
            return result
        except ContentFilterError as cfe:
            last_error = cfe
            if attempt < max_retries - 1:
                log.warning(
                    f"🛡️ İçerik filtresi reddetti (deneme {attempt + 1}/{max_retries}). "
                    f"Farklı senaryo ile tekrar denenecek..."
                )
                # Reddedilen combo'yu listeye ekle ki tekrar seçilmesin
                # (pipeline_config'den combo_key elimizde yok ama
                # generate_prompts zaten rastgele seçiyor)
            else:
                log.error(f"❌ {max_retries} farklı senaryo denendi, hepsi reddedildi.")
                return {"success": False, "error": str(last_error)}

    return {"success": False, "error": "Tüm denemeler başarısız"}


async def _execute_pipeline(used_combos: list[str]) -> dict:
    """
    Pipeline'ın asıl implementasyonu.
    ContentFilterError yukarı fırlatılır → retry mekanizması yakalar.
    """
    tracker = NotionTracker()
    kie = KieClient()
    video_paths = []
    start_time = time.time()

    pipeline_config = {
        "used_combos": used_combos,
    }

    try:
        # ── ADIM 1: Prompt üret (Creative Engine + GPT) ──
        log.info("🧠 Yaratıcı motor çalışıyor...")
        prompt_data = await generate_prompts(pipeline_config)

        scenes = prompt_data.get("scenes", [])
        combo_key = prompt_data.get("combo_key", "")
        clip_count = len(scenes)
        total_duration = prompt_data.get("total_duration", 0)

        log.info(f"🎬 Senaryo: {prompt_data.get('scenario_summary', '')}")
        log.info(f"   {clip_count} klip, toplam {total_duration}s")
        log.info(f"   Hayvan: {prompt_data.get('animal', '?')} | Yetenek: {prompt_data.get('talent', '?')}")

        # ── ADIM 2: Notion entry ──
        notion_config = {
            "topic": prompt_data.get("scenario_summary", "Pets Got Talent video"),
            "model": settings.DEFAULT_MODEL,
            "clip_count": clip_count,
            "orientation": settings.DEFAULT_ORIENTATION,
            "audio": settings.DEFAULT_AUDIO,
            "combo_key": combo_key,
        }
        await asyncio.to_thread(tracker.create_entry, notion_config, trigger="auto")
        await asyncio.to_thread(tracker.update_with_prompts, prompt_data)

        # ── ADIM 3: Video üret (Seedance 2.0) ──
        log.info(f"🎬 Video üretimi başlıyor ({settings.DEFAULT_MODEL})...")
        await asyncio.to_thread(tracker.update_status, "Video Üretiliyor")

        if clip_count == 1:
            video_url = await kie.create_video(
                model=settings.DEFAULT_MODEL,
                prompt=scenes[0]["prompt"],
                orientation=settings.DEFAULT_ORIENTATION,
                duration=scenes[0].get("duration", settings.DEFAULT_DURATION),
                audio=settings.DEFAULT_AUDIO,
                resolution=settings.DEFAULT_RESOLUTION,
            )
            video_urls = [video_url]
        else:
            video_urls = await kie.create_videos_batch(
                model=settings.DEFAULT_MODEL,
                scenes=scenes,
                orientation=settings.DEFAULT_ORIENTATION,
                audio=settings.DEFAULT_AUDIO,
                resolution=settings.DEFAULT_RESOLUTION,
            )

        await asyncio.to_thread(tracker.update_with_video, video_urls[0])
        log.info(f"✅ {len(video_urls)} video hazır")

        # ── Güvenlik Telemetrisi ──
        try:
            preflight_meta = getattr(kie, '_last_preflight_meta', {})
            if preflight_meta and preflight_meta.get('risk_score', 0) > 0:
                safety_data = {
                    "preflight_risk_score": preflight_meta.get('risk_score', 0),
                    "preflight_rewritten": preflight_meta.get('rewritten', False),
                    "rejection_reasons": preflight_meta.get('risk_reasons', []),
                }
                await asyncio.to_thread(tracker.update_with_safety_info, safety_data)
        except Exception as e:
            log.debug(f"Güvenlik telemetrisi hatası (önemsiz): {e}")

        # ── ADIM 4: Birleştir (gerekirse) ──
        final_video_url = video_urls[0]
        if len(video_urls) > 1:
            log.info(f"🎞️ {len(video_urls)} video birleştiriliyor...")
            await asyncio.to_thread(tracker.update_status, "Birleştiriliyor")
            final_video_url = await merge_videos(video_urls, keep_audio=True)

        # ── ADIM 5: Video indir ──
        log.info("📥 Video indiriliyor...")
        video_path = await asyncio.to_thread(download_video, final_video_url)
        video_paths.append(video_path)

        # ── ADIM 6: YouTube upload (Shorts) ──
        youtube_url = ""
        if settings.YOUTUBE_ENABLED:
            log.info("📺 YouTube Shorts olarak yükleniyor...")
            await asyncio.to_thread(tracker.update_status, "Yükleniyor")
            youtube_url = await upload_to_youtube(
                video_path, prompt_data, is_shorts=True
            )
            if youtube_url:
                await asyncio.to_thread(tracker.update_with_youtube, youtube_url)
                log.info(f"✅ YouTube'a yüklendi: {youtube_url}")

        # ── ADIM 7: Tamamlandı ──
        elapsed = time.time() - start_time

        if not youtube_url:
            if settings.YOUTUBE_ENABLED:
                await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı (Upload Başarısız)")
            else:
                await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı (YouTube Kapalı)")
        else:
            await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı")

        log.info(f"🎉 Pipeline tamamlandı! ({elapsed:.0f}s)")
        log.info(f"   📺 {youtube_url or 'Upload kapalı'}")
        log.info(f"   🎬 {prompt_data.get('youtube_title', 'N/A')}")

        return {
            "success": True,
            "youtube_url": youtube_url,
            "title": prompt_data.get("youtube_title", ""),
            "scenario": prompt_data.get("scenario_summary", ""),
            "combo_key": combo_key,
            "clip_count": clip_count,
            "total_duration": total_duration,
            "elapsed": elapsed,
        }

    except ContentFilterError:
        # Yukarı fırlat → retry mekanizması yakalasın
        raise

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        log.error(f"❌ Pipeline HATASI ({elapsed:.1f}s): {error_msg}", exc_info=True)
        await asyncio.to_thread(tracker.update_with_error, error_msg)
        return {"success": False, "error": error_msg}

    finally:
        for vp in video_paths:
            cleanup_video(vp)


# ────────────────────────────────────────
# 🏥 SİSTEM SAĞLIK KONTROLÜ
# ────────────────────────────────────────

def health_check():
    """Sistem sağlık kontrolü — tüm servisleri test eder."""
    checks = []

    # Config
    checks.append(("Config Boot", True, f"ENV={settings.ENV}"))

    # OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        checks.append(("OpenAI API Key", not settings.OPENAI_API_KEY.startswith("sk-test"), ""))
    except Exception as e:
        checks.append(("OpenAI", False, str(e)))

    # Kie AI
    checks.append(("Kie AI API Key", not settings.KIE_API_KEY.startswith("test-"), ""))

    # YouTube
    yt_ok = bool(settings.YOUTUBE_CLIENT_ID and settings.YOUTUBE_CLIENT_SECRET and settings.YOUTUBE_REFRESH_TOKEN)
    checks.append(("YouTube OAuth2", yt_ok, f"Upload: {'Aktif' if settings.YOUTUBE_ENABLED else 'Kapalı'}"))

    # Notion
    checks.append(("Notion", settings.NOTION_ENABLED, f"DB: {settings.NOTION_DB_ID[:8]}..." if settings.NOTION_DB_ID else "DB yok"))

    # Replicate
    checks.append(("Replicate", not settings.REPLICATE_API_TOKEN.startswith("test-"), ""))

    # FFmpeg
    checks.append(("FFmpeg", settings.FFMPEG_AVAILABLE, "Opsiyonel — Replicate fallback mevcut"))

    print("\n🏥 Sistem Sağlık Raporu — Pets Got Talent V3\n" + "=" * 50)
    all_ok = True
    for name, ok, detail in checks:
        icon = "✅" if ok else "❌"
        detail_str = f" — {detail}" if detail else ""
        print(f"  {icon} {name}{detail_str}")
        if not ok and name not in ("FFmpeg",):
            all_ok = False

    print("=" * 50)
    if all_ok:
        print("✅ Tüm kritik sistemler hazır!")
    else:
        print("❌ Bazı sistemler hazır değil — yukarıdaki hataları kontrol edin.")
    print()

    return all_ok


# ────────────────────────────────────────
# 🚀 ENTRY POINT
# ────────────────────────────────────────

def main():
    """CLI entry point — CronJob bu fonksiyonu çalıştırır."""
    parser = argparse.ArgumentParser(
        description="Pets Got Talent V3 — Günlük Otonom Video Pipeline"
    )
    parser.add_argument("--dry-run", action="store_true", help="Gerçek üretim yapmadan test")
    parser.add_argument("--check", action="store_true", help="Sistem sağlık kontrolü")
    args = parser.parse_args()

    if args.check:
        health_check()
        return

    result = asyncio.run(run_pipeline(dry_run=args.dry_run))

    if result and result.get("success"):
        log.info("🎉 Günlük video başarıyla üretildi ve yüklendi!")
        sys.exit(0)
    else:
        error = result.get("error", "Bilinmeyen hata") if result else "Pipeline sonuç döndürmedi"
        log.error(f"💥 Pipeline başarısız: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

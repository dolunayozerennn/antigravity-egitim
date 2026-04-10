"""
Dolunay Otonom Kapak Üreticisi (V2)
-----------------------------------
Reels (9:16) ve YouTube (16:9) formatlarındaki kapakları tek noktadan yönetir.
"""

import os
import sys
import time
import random
import argparse
from core.logger import get_logger
from core.notion_service import get_ready_videos, add_revision_panel
from core.drive_service import upload_cover_to_drive, count_existing_covers, check_covers_exist
from core.ops_logger import get_ops_logger


def get_available_cutouts(project_dir: str):
    """
    Returns a list of local cutout filenames.
    Cutouts are in assets/cutouts/ within the unified project.
    """
    cutout_dir = os.path.join(project_dir, "assets", "cutouts")
    if not os.path.exists(cutout_dir):
        return None, []
    
    cutouts = [f for f in os.listdir(cutout_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    return cutout_dir, cutouts


def process_reels(logger):
    """Reels pipeline: 3 Themes x 2 Variants = 6 Covers"""
    ops = get_ops_logger("Reels_Kapak", "Pipeline")
    ops.info("Reels Cover Pipeline Başlatıldı")
    
    from agents.reels_agent import run_autonomous_generation, generate_three_themes
    
    videos = get_ready_videos(cover_type="reels")
    if not videos:
        logger.info("İşlem bekleyen Reels videosu bulunamadı ('Çekildi - Edit YOK').")
        return

    os.makedirs("outputs", exist_ok=True)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    cutout_dir, available_cutouts = get_available_cutouts(project_dir)
    if not available_cutouts:
        logger.error(f"Cutout dosyası bulunamadı: {cutout_dir}")
        return

    for video in videos:
        logger.info(f"🎬 İşleniyor (Reels): {video['name']}")
        drive_url = video.get('drive_url')
        if not drive_url:
            logger.warning(f"Atlanıyor '{video['name']}': Drive linki Notion'da mevcut değil.")
            continue
            
        REQUIRED_COVERS = 6
        existing_count = count_existing_covers(drive_url)
        if existing_count >= REQUIRED_COVERS:
            logger.info(f"✅ Atlanıyor '{video['name']}': Minimum {REQUIRED_COVERS} kapak zaten Drive'da mevcut.")
            continue
            
        script_content = video.get('script_text', '')
        topic = video['name']
        
        # Select single random cutout for all themes for identity lock
        cutout_name = random.choice(available_cutouts)
        cutout_path = os.path.join(cutout_dir, cutout_name)
        
        other_cutouts = [f for f in available_cutouts if f != cutout_name]
        extra_cutout_paths = [os.path.join(cutout_dir, c) for c in random.sample(other_cutouts, min(2, len(other_cutouts)))] if other_cutouts else []
        
        logger.info(f"🧑 Cutout referansı: {cutout_name}")
        
        try:
            themes = generate_three_themes(topic, script_content)
        except Exception as e:
            logger.error(f"Tema üretimi başarısız: {e}")
            continue
            
        themes_with_links = []
        for t_idx, theme in enumerate(themes, 1):
            theme_name = theme.get("theme_name", f"theme{t_idx}")
            cover_text = theme.get("cover_text", topic.upper())
            scene_description = theme.get("scene_description", "")
            
            logger.info(f"Tema {t_idx}/{len(themes)}: {theme_name.upper()} -> '{cover_text}'")
            theme_drive_links = []
            
            for v_idx in range(1, 3):
                safe_video_name = "".join([c for c in video['name'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                final_cover_path = os.path.join("outputs", f"{safe_video_name}_T{t_idx}_V{v_idx}.png")
                
                success = run_autonomous_generation(
                    local_person_image_path=cutout_path,
                    video_topic=topic,
                    main_text=cover_text,
                    output_path=final_cover_path,
                    max_retries=2,
                    variant_index=v_idx,
                    script_text=script_content,
                    scene_description=scene_description,
                    extra_cutout_paths=extra_cutout_paths
                )
                
                if success:
                    drive_file_name = f"Kapak T{t_idx} ({theme_name}) V{v_idx}.png"
                    upload_cover_to_drive(final_cover_path, drive_url, file_name=drive_file_name)
                    theme_drive_links.append({"variant": v_idx, "url": drive_url})
                else:
                    logger.warning(f"Tema {t_idx} Varyasyon {v_idx} başarısız oldu.")
            
            themes_with_links.append({
                "theme_index": t_idx,
                "theme_name": theme_name,
                "cover_text": cover_text,
                "drive_links": theme_drive_links,
            })
            
        if themes_with_links:
            add_revision_panel(cover_type="reels", page_id=video["id"], themes_with_links=themes_with_links)
            
    ops.success("Reels Cover Pipeline Tamamlandı")


def process_youtube(logger):
    """YouTube pipeline: 5 Themes x 2 Variants = 10 Covers"""
    ops = get_ops_logger("YouTube_Kapak", "Pipeline")
    ops.info("YouTube Thumbnail Pipeline Başlatıldı")
    
    from agents.youtube_agent import run_autonomous_generation, generate_concepts, select_cutouts_for_theme
    
    videos = get_ready_videos(cover_type="youtube")
    if not videos:
        logger.info("İşlem bekleyen YouTube videosu bulunamadı ('Çekildi').")
        return

    os.makedirs("outputs", exist_ok=True)
    
    for video in videos:
        logger.info(f"🎬 İşleniyor (YouTube): {video['name']}")
        drive_url = video.get('drive_url')
        if not drive_url:
            logger.warning(f"Atlanıyor '{video['name']}': Drive linki Notion'da mevcut değil.")
            continue
            
        if check_covers_exist(drive_url):
            logger.info(f"✅ Atlanıyor '{video['name']}': Thumbnailler zaten Drive'da mevcut.")
            continue
            
        script_content = video.get('script_text', '')
        topic = video['name']
        
        try:
            themes = generate_concepts(topic, script_content, count=5)
        except Exception as e:
            logger.error(f"Konsept üretimi başarısız: {e}")
            continue
            
        themes_with_links = []
        for t_idx, theme in enumerate(themes, 1):
            theme_name = theme.get("theme_name", f"theme{t_idx}")
            cover_text = theme.get("cover_text", "BUNU İZLE")
            scene_description = theme.get("scene_description", "")
            screenshot_url = theme.get("screenshot_url")
            
            logger.info(f"Tema {t_idx}/{len(themes)}: {theme_name.upper()} -> '{cover_text}'")
            theme_drive_links = []
            
            # Use specific agent functions to retrieve best cutouts matching mood
            cutout_paths = select_cutouts_for_theme(theme_name=theme_name, target_mood=theme.get('mood', 'confident'), count=3)
            base_cutout = cutout_paths[0] if cutout_paths else None
            extra_cutouts = cutout_paths[1:] if len(cutout_paths) > 1 else None
            
            if not base_cutout:
                logger.error("Cutout bulunamadı. Varyasyon atlanıyor.")
                continue

            for v_idx in range(1, 3):
                safe_video_name = "".join([c for c in video['name'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                final_cover_path = os.path.join("outputs", f"{safe_video_name}_THUMBNAIL_T{t_idx}_V{v_idx}.png")
                
                success = run_autonomous_generation(
                    local_person_image_path=base_cutout,
                    video_topic=topic,
                    main_text=cover_text,
                    output_path=final_cover_path,
                    max_retries=5,
                    variant_index=v_idx,
                    script_text=script_content,
                    scene_description=scene_description,
                    extra_cutout_paths=extra_cutouts,
                    screenshot_url=screenshot_url
                )
                
                if success:
                    drive_file_name = f"Thumbnail T{t_idx} ({theme_name}) V{v_idx}.png"
                    upload_cover_to_drive(final_cover_path, drive_url, file_name=drive_file_name)
                    theme_drive_links.append({"variant": v_idx, "url": drive_url})
                else:
                    logger.warning(f"Tema {t_idx} Varyasyon {v_idx} başarısız oldu.")
            
            themes_with_links.append({
                "theme_index": t_idx,
                "theme_name": theme_name,
                "cover_text": cover_text,
                "drive_links": theme_drive_links,
            })
            
        if themes_with_links:
            add_revision_panel(cover_type="youtube", page_id=video["id"], themes_with_links=themes_with_links)

    ops.success("YouTube Thumbnail Pipeline Tamamlandı")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Otonom Kapak Üreticisi (V2)")
    parser.add_argument("--type", type=str, choices=["reels", "youtube"], required=False, help="Hangi platform için kapak üretilecek?")
    args = parser.parse_args()

    cover_type = args.type or os.environ.get("COVER_TYPE")
    if not cover_type or cover_type not in ["reels", "youtube"]:
        print("❌ HATA: Lütfen --type argümanı veya COVER_TYPE environment variable ile 'reels' veya 'youtube' seçin.")
        sys.exit(1)

    # Fail-Fast konfigürasyon garantisi için V2 yapısı Logger dahil edilir
    logger = get_logger("Otonom_Kapak", level="INFO")
    logger.info(f"[{cover_type.upper()}] Pipeline Başlatılıyor...")

    # CronJob Mode (default) — tek sefer çalıştır, çık
    # Worker Mode (opt-in) — LOOP=1 ile sonsuz döngü
    use_worker_loop = os.environ.get("LOOP") == "1"

    if use_worker_loop:
        logger.info(f"🔄 [Worker Mode] Döngüsü Başlatıldı. {cover_type} pipeline sonsuz döngüde çalışacak...")
        while True:
            try:
                if cover_type == "reels":
                    process_reels(logger)
                else:
                    process_youtube(logger)
            except Exception as e:
                logger.error(f"Beklenmeyen hata oluştu: {e}")
                get_ops_logger(f"{cover_type.capitalize()}_Kapak", "Pipeline").error(f"Fatally Failed: {e}", exception=e)
            
            logger.info("⏳ 10 dakika bekleniyor...")
            time.sleep(600)
    else:
        # CronJob Mode — çalıştır ve çık
        logger.info(f"⏱️ [CronJob Mode] Tek seferlik çalışma başlatıldı.")
        try:
            if cover_type == "reels":
                process_reels(logger)
            else:
                process_youtube(logger)
            logger.info(f"✅ [{cover_type.upper()}] Pipeline tamamlandı. Çıkılıyor.")
        except Exception as e:
            logger.error(f"Pipeline hatası: {e}", exc_info=True)
            get_ops_logger(f"{cover_type.capitalize()}_Kapak", "Pipeline").error(f"Fatally Failed: {e}", exception=e)
            sys.exit(1)


if __name__ == "__main__":
    main()

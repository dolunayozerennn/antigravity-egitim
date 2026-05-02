from config import settings
from logger import get_logger
from core.apify_client import fetch_all_social_media
from core.llm_helper import generate_report_summary
from infrastructure.email_sender import send_performance_report, send_technical_error_report, GmailAuthError
from infrastructure.state_manager import NotifiedVideosManager, NotionStateError
from ops_logger import wait_all_loggers

logger = get_logger(__name__)


def _safe_send_tech_error(errors):
    """Hata raporunu gönderirken hata oluşursa sadece logla (fatal handler içinde de güvenli)."""
    try:
        send_technical_error_report(errors)
    except Exception as e:
        logger.error(f"Teknik hata raporu gönderimi sırasında hata: {e}", exc_info=True)


def main():
    logger.info(f"Ceren Notifier başladı (ENV={settings.ENV}, DRY_RUN={settings.IS_DRY_RUN})")
    try:
        state = NotifiedVideosManager()
        videos, errors = fetch_all_social_media()

        # ── Partial failure routing ────────────────────────────────────
        failed_platforms = [e["platform"] for e in errors if isinstance(e, dict) and "platform" in e]
        critical_failure = len(failed_platforms) >= 2

        if errors:
            logger.warning(f"{len(errors)} platform hatası: {failed_platforms}")
            _safe_send_tech_error(errors)

        if critical_failure:
            logger.error(
                f"2+ platform başarısız ({failed_platforms}); Ceren'e mail GÖNDERİLMİYOR"
            )
            return

        # ── Yeni videoları filtrele ────────────────────────────────────
        new_videos = [
            v for v in videos
            if v.get("url") and not state.is_notified(v["url"])
        ]

        if not new_videos:
            logger.info("Barajı aşan yeni video yok, mail atlanıyor")
            return

        logger.info(f"{len(new_videos)} yeni video bulundu, mail hazırlanıyor")

        try:
            summary = generate_report_summary(new_videos)
        except Exception as e:
            logger.warning(f"LLM özet üretilemedi (mail yine gönderilecek): {e}")
            summary = ""

        try:
            send_performance_report(
                new_videos,
                report_summary=summary,
                missing_platforms=failed_platforms or None,
            )
        except GmailAuthError as e:
            logger.error(f"Gmail auth hatası, rapor gönderilemedi: {e}")
            _safe_send_tech_error([{"platform": "Gmail", "stage": "auth", "actor_id": "-", "error": str(e)}])
            return
        except Exception as e:
            logger.error(f"Rapor gönderim hatası: {e}", exc_info=True)
            _safe_send_tech_error([{"platform": "Gmail", "stage": "send", "actor_id": "-", "error": str(e)}])
            return

        # ── Per-video state mark ───────────────────────────────────────
        state_errors = []
        for v in new_videos:
            try:
                state.mark_as_notified(v["url"], v.get("platform", "Unknown"), v.get("views", 0))
            except NotionStateError as e:
                logger.error(f"State mark başarısız ({v['url']}): {e}")
                state_errors.append({
                    "platform": v.get("platform", "?"),
                    "stage": "state_save",
                    "actor_id": "Notion",
                    "error": str(e),
                })

        marked = len(new_videos) - len(state_errors)
        logger.info(f"State mark: {marked}/{len(new_videos)} başarılı")

        if state_errors:
            _safe_send_tech_error(state_errors)

        logger.info("Pipeline başarıyla tamamlandı")

    except Exception as e:
        logger.error(f"Fatal: {e}", exc_info=True)
        _safe_send_tech_error([{
            "platform": "Pipeline",
            "stage": "fatal",
            "actor_id": "-",
            "error": f"{type(e).__name__}: {e}",
        }])
    finally:
        wait_all_loggers()


if __name__ == "__main__":
    main()

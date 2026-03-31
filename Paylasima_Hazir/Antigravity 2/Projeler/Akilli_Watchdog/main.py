"""
Akıllı Watchdog — Ana Orkestrasyon Modülü
3 katmanlı sağlık kontrolünü orkestre eder:
  Katman 1: Yapısal kontrol (Sheet tab/header, Notion DB property)
  Katman 2: LLM analiz (şema kayması, veri kalitesi, pipeline tutarlılığı)

Çalıştırma:
  python main.py           # Tek seferlik kontrol (günlük cron için ideal)
  python main.py --force   # Sorun olmasa bile rapor e-postası gönder
  python main.py --loop    # Sürekli döngü (CHECK_INTERVAL_HOURS aralığında)
"""
import sys
import time
import signal
import logging
import argparse
from datetime import datetime

from datetime import timezone as tz_module, timedelta as td_module

from config import Config
from sheets_checker import SheetsChecker
from notion_checker import NotionChecker
from llm_analyzer import LLMAnalyzer
from alerter import send_alert_email

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("AkilliWatchdog")

# ── Graceful Shutdown ────────────────────────────────────────
_running = True


def _signal_handler(sig, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı...")
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


def _now_tr() -> str:
    """Türkiye saatini string olarak döner."""
    tr_tz = tz_module(td_module(hours=3))
    return datetime.now(tr_tz).strftime("%Y-%m-%d %H:%M:%S UTC+3")


def run_health_check(force_email: bool = False) -> dict:
    """
    Tam sağlık kontrolü çalıştırır.

    Returns:
        {
            "timestamp": str,
            "all_healthy": bool,
            "total_issues": int,
            "issues": list[str],
            "sheets_results": list[dict],
            "notion_results": list[dict],
            "llm_results": list[dict],
        }
    """
    logger.info("=" * 65)
    logger.info("🐕 Akıllı Watchdog — Sağlık Kontrolü Başlıyor")
    logger.info(f"   Zaman: {_now_tr()}")
    logger.info(f"   İzlenen proje sayısı: {len(Config.MONITORED_PROJECTS)}")
    logger.info("=" * 65)

    all_issues: list[str] = []
    sheets_results: list[dict] = []
    notion_results: list[dict] = []
    llm_results: list[dict] = []

    # ── KATMAN 1: Yapısal Kontrol ────────────────────────────
    logger.info("── Katman 1: Yapısal Kontrol ──")

    # 1a. Google Sheets kontrolü
    sheets_checker = SheetsChecker()
    try:
        sheets_checker.authenticate()
    except Exception as e:
        logger.error(f"❌ Google Sheets authentication başarısız: {e}")
        all_issues.append(f"🚨 Google Sheets'e bağlanılamadı: {e}")
        return _build_result(all_issues, sheets_results, notion_results, llm_results)

    for project in Config.MONITORED_PROJECTS:
        logger.info(f"📋 [{project['name']}] Sheets kontrolü...")
        result = sheets_checker.full_check(project)
        sheets_results.append(result)
        all_issues.extend(result.get("issues", []))

        if result["healthy"]:
            logger.info(f"  ✅ {project['name']} → Sağlıklı")
        else:
            logger.warning(f"  ⚠️ {project['name']} → {len(result['issues'])} sorun")

    # 1b. Notion kontrolü (sadece sheets_to_notion pipeline'ları)
    if Config.NOTION_API_TOKEN:
        notion_checker = NotionChecker()
        for project in Config.MONITORED_PROJECTS:
            if project.get("pipeline") == "sheets_to_notion":
                logger.info(f"📋 [{project['name']}] Notion kontrolü...")
                result = notion_checker.full_check(project)
                notion_results.append(result)
                all_issues.extend(result.get("issues", []))

                if result["healthy"]:
                    logger.info(f"  ✅ {project['name']} → Notion sağlıklı")
                else:
                    logger.warning(f"  ⚠️ {project['name']} → Notion sorunlu")
    else:
        logger.warning("⚠️ NOTION_API_TOKEN tanımlı değil, Notion kontrolü atlandı")

    # ── KATMAN 2: LLM Analiz ─────────────────────────────────
    logger.info("── Katman 2: LLM Akıllı Analiz ──")

    if Config.GROQ_API_KEY:
        llm = LLMAnalyzer()
        for i, project in enumerate(Config.MONITORED_PROJECTS):
            sheets_result = sheets_results[i] if i < len(sheets_results) else {}
            notion_result = next(
                (n for n in notion_results if n["project_name"] == project["name"]),
                None,
            )

            logger.info(f"🧠 [{project['name']}] LLM analizi...")
            result = llm.full_analysis(project, sheets_result, notion_result)
            llm_results.append(result)

            if result["critical_issues"]:
                all_issues.extend(result["critical_issues"])

            logger.info(f"  {result['overall_status']} {project['name']}")
    else:
        logger.warning("⚠️ GROQ_API_KEY tanımlı değil, LLM analizi atlandı")

    # ── SONUÇ & RAPOR ────────────────────────────────────────
    report = _build_result(all_issues, sheets_results, notion_results, llm_results)

    logger.info("=" * 65)
    if report["all_healthy"]:
        logger.info("✅ Tüm kontroller geçti — sistemler sağlıklı!")
    else:
        logger.warning(
            f"⚠️ {report['total_issues']} sorun tespit edildi — "
            f"detaylar e-posta raporunda"
        )
    logger.info("=" * 65)

    # E-posta gönder
    send_alert_email(
        sheets_results, notion_results, llm_results,
        all_issues, force=force_email,
    )

    return report


def _build_result(
    all_issues: list[str],
    sheets_results: list[dict],
    notion_results: list[dict],
    llm_results: list[dict],
) -> dict:
    """Sonuçları standart yapıda toplar."""
    return {
        "timestamp": _now_tr(),
        "all_healthy": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "sheets_results": sheets_results,
        "notion_results": notion_results,
        "llm_results": llm_results,
    }


def main():
    """Ana giriş noktası."""
    parser = argparse.ArgumentParser(description="Akıllı Watchdog — Pipeline Sağlık Kontrolü")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sorun olmasa bile rapor e-postası gönder",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help=f"Sürekli döngü ({Config.CHECK_INTERVAL_HOURS}h aralık)",
    )
    args = parser.parse_args()

    if not Config.validate():
        logger.critical("❌ Konfigürasyon hatalı, çıkılıyor...")
        sys.exit(1)

    if args.loop:
        logger.info(
            f"♻️ Sürekli döngü modu — {Config.CHECK_INTERVAL_HOURS} saatte bir kontrol"
        )
        while _running:
            try:
                run_health_check(force_email=args.force)
            except Exception as e:
                logger.error(f"❌ Beklenmeyen hata: {e}", exc_info=True)

            # Bekleme
            wait_seconds = Config.CHECK_INTERVAL_HOURS * 3600
            logger.info(
                f"⏳ Sonraki kontrol: {Config.CHECK_INTERVAL_HOURS} saat sonra"
            )
            for _ in range(wait_seconds):
                if not _running:
                    break
                time.sleep(1)

        logger.info("👋 Akıllı Watchdog durduruldu.")
    else:
        # Tek seferlik kontrol
        result = run_health_check(force_email=args.force)
        sys.exit(0 if result["all_healthy"] else 1)


if __name__ == "__main__":
    main()

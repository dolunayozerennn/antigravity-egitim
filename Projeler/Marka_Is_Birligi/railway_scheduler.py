#!/usr/bin/env python3
"""
Marka İş Birliği — Railway Scheduler
=====================================
Bu dosya Railway üzerinde sürekli çalışır ve haftalık görevleri tetikler.

Görevler:
1. Haftalık Pipeline (Pazartesi 07:00 TR / 04:00 UTC)
   → Reels scrape, marka analizi, iletişim bulma, outreach gönderim
2. Follow-Up Kontrolü (Perşembe 07:00 TR / 04:00 UTC)
   → 7+ günlük cevapsız markalara kişiselleştirilmiş reply
3. Haftalık Rapor (Cuma 07:00 TR / 04:00 UTC)
   → Telegram'a haftalık performans özeti

Timezone:
    Railway sunucuları UTC kullanır.
    Cron: 0 4 * * 1,4,5 → TR 07:00 = UTC 04:00

Health Check:
    PORT env variable üzerinden HTTP sunucusu açılır.
    GET / → JSON durum bilgisi
"""

import os
import sys
import time
import json
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Proje path'ini ayarla ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from ops_logger import get_ops_logger
ops = get_ops_logger("Marka_Is_Birligi", "Scheduler")

# ── Timezone ─────────────────────────────────────────────────────────────
TR_OFFSET = timedelta(hours=3)

def tr_now():
    """Şu anki Türkiye saatini döndür (UTC+3)."""
    return datetime.now(timezone.utc) + TR_OFFSET


# ═══════════════════════════════════════════════════════════════════════
# 🏥 Health Check Sunucusu
# ═══════════════════════════════════════════════════════════════════════

_service_status = {
    "service": "marka-is-birligi-outreach",
    "scheduler_started_at": None,
    "last_heartbeat": None,
    "last_job_run": None,
    "last_job_result": None,
    "next_run": None,
    "total_runs": 0,
    "total_errors": 0,
    "pipeline_stats": {},
    "followup_stats": {},
    "report_stats": {},
}


def _check_dependencies():
    """Notion / Gmail / Apify hızlıca ping et — /health/deps için."""
    import requests as _r

    deps = {}

    # Notion
    try:
        token = os.environ.get("NOTION_SOCIAL_TOKEN", "")
        if not token:
            deps["notion"] = "missing_token"
        else:
            r = _r.get(
                "https://api.notion.com/v1/users/me",
                headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
                timeout=5,
            )
            deps["notion"] = "ok" if r.status_code == 200 else f"http_{r.status_code}"
    except Exception as e:
        deps["notion"] = f"err:{type(e).__name__}"

    # Gmail token (sadece varlık + format kontrolü; canlı API çağırmıyoruz)
    gmail_b64 = os.environ.get("GOOGLE_DOLUNAY_AI_TOKEN_JSON", "")
    deps["gmail_token"] = "ok" if gmail_b64 else "missing"

    # Apify token sayısı
    apify_keys = sum(1 for i in range(1, 10) if os.environ.get(f"APIFY_API_KEY_{i}"))
    if os.environ.get("APIFY_API_KEY"):
        apify_keys += 1
    deps["apify_tokens"] = apify_keys

    # OpenAI / Hunter sadece varlık
    deps["openai"] = "ok" if os.environ.get("OPENAI_API_KEY") else "missing"
    deps["hunter"] = "ok" if os.environ.get("HUNTER_API_KEY") else "missing"

    return deps


class HealthHandler(BaseHTTPRequestHandler):
    """Basit health check HTTP handler."""

    def do_GET(self):
        _service_status["last_heartbeat"] = datetime.now().isoformat()
        _service_status["next_run"] = None  # CronJob modunda schedule kullanılmıyor
        _service_status["uptime_seconds"] = int(
            (datetime.now() - datetime.fromisoformat(_service_status["scheduler_started_at"])).total_seconds()
        ) if _service_status["scheduler_started_at"] else 0

        if self.path.rstrip("/") == "/health/deps":
            payload = dict(_service_status)
            payload["dependencies"] = _check_dependencies()
        else:
            payload = _service_status

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=2).encode())

    def log_message(self, format, *args):
        pass


def start_health_server():
    """Health check sunucusunu ayrı bir thread'de başlat."""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"🏥 Health check sunucusu aktif: http://0.0.0.0:{port}/")
    server.serve_forever()


# ═══════════════════════════════════════════════════════════════════════
# 🚀 İş Fonksiyonları
# ═══════════════════════════════════════════════════════════════════════

def run_weekly_pipeline(force=False, dry_run=False):
    """Haftalik marka kesif + outreach pipeline'ini calistir."""
    now = tr_now()
    weekday = now.weekday()

    if not force and weekday >= 5:
        print(f"📅 {now.strftime('%Y-%m-%d %H:%M')} — Hafta sonu, atlanıyor.")
        return

    # Önce yanit/bounce kontrolü yap (dry-run'da skip)
    if not dry_run:
        print(f"\n{'='*60}")
        print(f"🔍 RESPONSE CHECK (pipeline öncesi): {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
        print(f"{'='*60}\n")
        try:
            from src.response_checker import check_responses
            check_responses(dry_run=False)
        except Exception as e:
            print(f"⚠️ Response check hatası: {e}")

    print(f"\n{'='*60}")
    print(f"🚀 HAFTALIK PİPELİNE başladı: {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
    print(f"{'='*60}\n")

    _service_status["total_runs"] += 1

    try:
        from src.outreach import run_full_pipeline
        metrics = run_full_pipeline(dry_run=dry_run) or {}
        _service_status["pipeline_stats"] = metrics
        print(f"\n✅ Pipeline tamamlandı: {tr_now().strftime('%H:%M:%S')} (TR)")
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = "pipeline_success"
        ops_pipe = get_ops_logger("Marka_Is_Birligi", "Outreach")
        ops_pipe.success("Haftalık Pipeline tamamlandı", json.dumps(metrics, ensure_ascii=False))

        # Fallback oranı yüksekse uyarı (>%10) — GPT/prompt regression sinyali
        if metrics.get("fallback_rate_pct", 0) > 10:
            ops_pipe.warning(
                "Yüksek GPT fallback oranı",
                f"%{metrics['fallback_rate_pct']} ({metrics.get('fallbacks',0)} fallback). "
                "Personalizer prompt veya OpenAI API durumu kontrol edilmeli.",
            )
    except Exception as e:
        print(f"❌ Pipeline hatası: {e}")
        import traceback
        traceback.print_exc()
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"pipeline_error: {str(e)[:200]}"
        _service_status["total_errors"] += 1
        ops_pipe = get_ops_logger("Marka_Is_Birligi", "Outreach")
        ops_pipe.error("Haftalık Pipeline çöktü", exception=e)


def run_followup_check(force=False, dry_run=False):
    """Follow-up kontrolü — cevapsız markalara reply at."""
    now = tr_now()
    weekday = now.weekday()

    if not force and weekday >= 5:
        print(f"📅 {now.strftime('%Y-%m-%d %H:%M')} — Hafta sonu, atlanıyor.")
        return

    if not dry_run:
        print(f"\n{'='*60}")
        print(f"🔍 RESPONSE CHECK (follow-up öncesi): {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
        print(f"{'='*60}\n")
        try:
            from src.response_checker import check_responses
            check_responses(dry_run=False)
        except Exception as e:
            print(f"⚠️ Response check hatası: {e}")

    print(f"\n{'='*60}")
    print(f"📬 FOLLOW-UP KONTROLÜ başladı: {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
    print(f"{'='*60}\n")

    _service_status["total_runs"] += 1

    try:
        from src.followup import send_followup_emails
        stats = send_followup_emails(dry_run=dry_run)
        _service_status["followup_stats"] = stats
        print(f"\n✅ Follow-up tamamlandı: {tr_now().strftime('%H:%M:%S')} (TR)")
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"followup_success: {stats}"
        ops_fu = get_ops_logger("Marka_Is_Birligi", "Follow-Up")
        ops_fu.success("Follow-up tamamlandı", str(stats))
    except Exception as e:
        print(f"❌ Follow-up hatası: {e}")
        import traceback
        traceback.print_exc()
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"followup_error: {str(e)[:200]}"
        _service_status["total_errors"] += 1
        ops_fu = get_ops_logger("Marka_Is_Birligi", "Follow-Up")
        ops_fu.error("Follow-up çöktü", exception=e)


def run_weekly_report_job():
    """Haftalık raporu oluştur ve gönder."""
    now = tr_now()
    weekday = now.weekday()
    
    # Sadece Cuma günleri çalışmalı ama manuel tetikleme de olabilir
    
    print(f"\n{'='*60}")
    print(f"📊 HAFTALIK RAPOR başladı: {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
    print(f"{'='*60}\n")
    
    _service_status["total_runs"] += 1
    
    try:
        from src.reporter import run_weekly_report
        run_weekly_report()
        print(f"\n✅ Rapor tamamlandı: {tr_now().strftime('%H:%M:%S')} (TR)")
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = "report_success"
        get_ops_logger("Marka_Is_Birligi", "Pipeline").success("Haftalık rapor gönderildi")
    except Exception as e:
        print(f"❌ Rapor hatası: {e}")
        import traceback
        traceback.print_exc()
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"report_error: {str(e)[:200]}"
        _service_status["total_errors"] += 1
        get_ops_logger("Marka_Is_Birligi", "Pipeline").error("Haftalık rapor hatası", exception=e)


# ═══════════════════════════════════════════════════════════════════════
# 🚀 Ana Giriş Noktası (Cron Modu)
# ═══════════════════════════════════════════════════════════════════════

def main():
    now_tr = tr_now()
    weekday = now_tr.weekday()
    
    force_pipeline = "--pipeline" in sys.argv
    force_followup = "--followup" in sys.argv
    force_report = "--report" in sys.argv
    force_all = "--all" in sys.argv
    dry_run = "--dry-run" in sys.argv

    is_manual = force_pipeline or force_followup or force_report or force_all
    mode = "Manuel Mod" if is_manual else "Cron Modu"
    if dry_run:
        mode += " · DRY-RUN"

    print("=" * 60)
    print(f"🤝 Marka İş Birliği — Otomatik Outreach Sistemi ({mode})")
    print(f"   🕐 Sunucu UTC: {datetime.now(timezone.utc).strftime('%H:%M')} → TR: {now_tr.strftime('%H:%M')}")
    print(f"   📅 Gün (0=Pzt, 6=Paz): {weekday}")
    print("=" * 60)

    if is_manual:
        if force_all or force_pipeline:
            print("➡️ Manuel tetikleme: run_weekly_pipeline çalışıyor...")
            run_weekly_pipeline(force=True, dry_run=dry_run)
        if force_all or force_followup:
            print("➡️ Manuel tetikleme: run_followup_check çalışıyor...")
            run_followup_check(force=True, dry_run=dry_run)
        if force_all or force_report:
            print("➡️ Manuel tetikleme: run_weekly_report_job çalışıyor...")
            run_weekly_report_job()
    else:
        # Cron mantığı
        if weekday == 0:
            print("➡️ Pazartesi: run_weekly_pipeline tetikleniyor...")
            run_weekly_pipeline(force=False, dry_run=dry_run)
        elif weekday == 3:
            print("➡️ Perşembe: run_followup_check tetikleniyor...")
            run_followup_check(force=False, dry_run=dry_run)
        elif weekday == 4:
            print("➡️ Cuma: run_weekly_report_job tetikleniyor...")
            run_weekly_report_job()
        else:
            print("➡️ Bugün planlanmış bir görev bulunmuyor.")

    print("\n👋 İşlem tamamlandı, çıkılıyor.")
    ops.wait_for_logs()
    sys.exit(0)

if __name__ == "__main__":
    main()

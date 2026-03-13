#!/usr/bin/env python3
"""
Marka İş Birliği — Railway Scheduler
=====================================
Bu dosya Railway üzerinde sürekli çalışır ve haftalık görevleri tetikler.

Görevler:
1. Haftalık Pipeline (Pazartesi 10:00 TR / 07:00 UTC)
   → Reels scrape, marka analizi, iletişim bulma, outreach gönderim
2. Follow-Up Kontrolü (Perşembe 10:00 TR / 07:00 UTC)
   → 7+ günlük cevapsız markalara kişiselleştirilmiş reply

Timezone:
    Railway sunucuları UTC kullanır.
    TR 10:00 = UTC 07:00

Health Check:
    PORT env variable üzerinden HTTP sunucusu açılır.
    GET / → JSON durum bilgisi
"""

import os
import sys
import time
import json
import schedule
import threading
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Proje path'ini ayarla ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

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
}


class HealthHandler(BaseHTTPRequestHandler):
    """Basit health check HTTP handler."""

    def do_GET(self):
        _service_status["last_heartbeat"] = datetime.now().isoformat()
        _service_status["next_run"] = str(schedule.next_run()) if schedule.jobs else None
        _service_status["uptime_seconds"] = int(
            (datetime.now() - datetime.fromisoformat(_service_status["scheduler_started_at"])).total_seconds()
        ) if _service_status["scheduler_started_at"] else 0

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(_service_status, indent=2).encode())

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

def run_weekly_pipeline():
    """Haftalık marka keşif + outreach pipeline'ını çalıştır."""
    now = tr_now()
    weekday = now.weekday()

    if weekday >= 5:
        print(f"📅 {now.strftime('%Y-%m-%d %H:%M')} — Hafta sonu, atlanıyor.")
        return

    print(f"\n{'='*60}")
    print(f"🚀 HAFTALIK PİPELİNE başladı: {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
    print(f"{'='*60}\n")

    _service_status["total_runs"] += 1

    try:
        from src.outreach import run_full_pipeline
        run_full_pipeline(dry_run=False)
        print(f"\n✅ Pipeline tamamlandı: {tr_now().strftime('%H:%M:%S')} (TR)")
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = "pipeline_success"
    except Exception as e:
        print(f"❌ Pipeline hatası: {e}")
        import traceback
        traceback.print_exc()
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"pipeline_error: {str(e)[:200]}"
        _service_status["total_errors"] += 1


def run_followup_check():
    """Follow-up kontrolü — cevapsız markalara reply at."""
    now = tr_now()
    weekday = now.weekday()

    if weekday >= 5:
        print(f"📅 {now.strftime('%Y-%m-%d %H:%M')} — Hafta sonu, atlanıyor.")
        return

    print(f"\n{'='*60}")
    print(f"📬 FOLLOW-UP KONTROLÜ başladı: {now.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
    print(f"{'='*60}\n")

    _service_status["total_runs"] += 1

    try:
        from src.followup import send_followup_emails
        stats = send_followup_emails(dry_run=False)
        _service_status["followup_stats"] = stats
        print(f"\n✅ Follow-up tamamlandı: {tr_now().strftime('%H:%M:%S')} (TR)")
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"followup_success: {stats}"
    except Exception as e:
        print(f"❌ Follow-up hatası: {e}")
        import traceback
        traceback.print_exc()
        _service_status["last_job_run"] = tr_now().isoformat()
        _service_status["last_job_result"] = f"followup_error: {str(e)[:200]}"
        _service_status["total_errors"] += 1


# ═══════════════════════════════════════════════════════════════════════
# 🚀 Ana Giriş Noktası
# ═══════════════════════════════════════════════════════════════════════

def main():
    _service_status["scheduler_started_at"] = datetime.now().isoformat()

    now_tr = tr_now()
    print("=" * 60)
    print("🤝 Marka İş Birliği — Otomatik Outreach Sistemi")
    print("   📊 Haftalık Pipeline: Pazartesi 10:00 (TR)")
    print("   📬 Follow-Up Check:  Perşembe 10:00 (TR)")
    print("   🏥 Health Check: Aktif (idle-sleep koruması)")
    print(f"   🕐 Sunucu UTC: {datetime.now(timezone.utc).strftime('%H:%M')} → TR: {now_tr.strftime('%H:%M')}")
    print("=" * 60)

    # Health check sunucusu
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # ═══════════════════════════════════════════════════════
    # Schedule: Haftalık Pipeline — Pazartesi 10:00 TR = 07:00 UTC
    # ═══════════════════════════════════════════════════════
    schedule.every().monday.at("07:00").do(run_weekly_pipeline)

    # ═══════════════════════════════════════════════════════
    # Schedule: Follow-Up — Perşembe 10:00 TR = 07:00 UTC
    # ═══════════════════════════════════════════════════════
    schedule.every().thursday.at("07:00").do(run_followup_check)

    print(f"\n⏰ Scheduler aktif. Bir sonraki çalışma: {schedule.next_run()}")
    print("🔁 Bekleniyor...\n")

    # Ana döngü — crash korumalı
    consecutive_errors = 0
    while True:
        try:
            schedule.run_pending()
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            print(f"⚠️ Scheduler döngü hatası #{consecutive_errors}: {e}")
            if consecutive_errors >= 10:
                print("🔴 10 ardışık hata! 5 dakika bekleniyor...")
                time.sleep(300)
                consecutive_errors = 0

        time.sleep(30)


if __name__ == "__main__":
    main()

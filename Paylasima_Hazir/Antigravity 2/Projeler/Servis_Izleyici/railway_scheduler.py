"""
🏥 Antigravity Servis İzleyici — Railway Scheduler
====================================================
Railway üzerinde sürekli çalışır ve her saat başı
health_check.py'yi tetikler.

Schedule:
    Her 60 dakikada bir → health_check (deep scan + auto-heal)
    Sorun varsa → e-posta bildirim

Health Check Endpoint:
    GET / → JSON durum bilgisi (Railway idle-sleep koruması)

Timezone:
    Railway UTC kullanır. Loglar UTC olarak yazılır.
"""

import os
import sys
import time
import json
import logging
import schedule
import threading
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# Logging yapılandır
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# ═══════════════════════════════════════════════════════════════
# 🕐 Timezone
# ═══════════════════════════════════════════════════════════════
TR_OFFSET = timedelta(hours=3)

def tr_now():
    """Şu anki Türkiye saatini döndür (UTC+3)."""
    return datetime.now(timezone.utc) + TR_OFFSET


# ═══════════════════════════════════════════════════════════════
# 🏥 Health Check Sunucusu
# ═══════════════════════════════════════════════════════════════

_service_status = {
    "service": "servis-izleyici",
    "version": "v4-railway",
    "scheduler_started_at": None,
    "last_heartbeat": None,
    "last_check_run": None,
    "last_check_result": None,
    "next_run": None,
    "total_checks": 0,
    "total_problems_found": 0,
    "total_auto_healed": 0,
    "total_errors": 0,
}


class HealthHandler(BaseHTTPRequestHandler):
    """Health check HTTP handler."""

    def do_GET(self):
        """GET / → servis durumu JSON."""
        _service_status["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        _service_status["next_run"] = str(schedule.next_run()) if schedule.jobs else None
        _service_status["uptime_seconds"] = int(
            (datetime.now() - datetime.fromisoformat(_service_status["scheduler_started_at"])).total_seconds()
        ) if _service_status["scheduler_started_at"] else 0

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(_service_status, indent=2, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        """Health check loglarını bastır."""
        pass


def start_health_server():
    """Health check sunucusunu ayrı thread'de başlat."""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logging.info(f"🏥 Health check sunucusu aktif: http://0.0.0.0:{port}/")
    server.serve_forever()


# ═══════════════════════════════════════════════════════════════
# 🔍 Health Check İşlevi
# ═══════════════════════════════════════════════════════════════

def run_check():
    """Health check'i çalıştır ve sonuçları güncelle."""
    now_tr = tr_now()
    logging.info(f"\n{'='*60}")
    logging.info(f"🏥 Zamanlanmış health check başlıyor: {now_tr.strftime('%Y-%m-%d %H:%M:%S')} (TR)")
    logging.info(f"{'='*60}\n")

    _service_status["total_checks"] += 1

    try:
        from health_check import run_health_check
        result = run_health_check()

        _service_status["last_check_run"] = datetime.now(timezone.utc).isoformat()
        _service_status["last_check_result"] = {
            "total": result.get("total", 0),
            "healthy": result.get("healthy", 0),
            "problems": result.get("problems", 0),
            "healed": result.get("healed", 0),
        }
        _service_status["total_problems_found"] += result.get("problems", 0)
        _service_status["total_auto_healed"] += result.get("healed", 0)

        logging.info(f"\n✅ Health check tamamlandı: {tr_now().strftime('%H:%M:%S')} (TR)")
        logging.info(f"   📊 {result.get('total', 0)} servis kontrol edildi, "
                     f"{result.get('healthy', 0)} sağlıklı, "
                     f"{result.get('problems', 0)} sorunlu, "
                     f"{result.get('healed', 0)} otomatik düzeltildi")

    except Exception as e:
        logging.error(f"❌ Health check hatası: {e}")
        import traceback
        traceback.print_exc()
        _service_status["last_check_run"] = datetime.now(timezone.utc).isoformat()
        _service_status["last_check_result"] = {"error": str(e)[:200]}
        _service_status["total_errors"] += 1


# ═══════════════════════════════════════════════════════════════
# 🚀 Ana Giriş Noktası
# ═══════════════════════════════════════════════════════════════

def main():
    _service_status["scheduler_started_at"] = datetime.now().isoformat()

    now_tr = tr_now()
    print("=" * 60)
    print("🏥 Antigravity Servis İzleyici — Railway Edition v4")
    print("   🔍 Health check: Her saat başı")
    print("   🩺 Self-healing: Aktif (otomatik düzeltme)")
    print("   📧 E-posta alarm: Sorun tespit edilince")
    print("   🏥 HTTP endpoint: Aktif (idle-sleep koruması)")
    print(f"   🕐 UTC: {datetime.now(timezone.utc).strftime('%H:%M')} → TR: {now_tr.strftime('%H:%M')}")
    print("=" * 60)

    # Health check sunucusunu arka planda başlat
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # İlk çalışmayı hemen yap (deploy sonrası anında kontrol)
    logging.info("\n🚀 İlk health check hemen başlıyor...")
    run_check()

    # ═══════════════════════════════════════════════════════
    # Schedule — Her saat başı kontrol
    # ═══════════════════════════════════════════════════════
    # Her saat 00'da çalışır (UTC)
    schedule.every().hour.at(":00").do(run_check)

    logging.info(f"\n⏰ Scheduler aktif. Bir sonraki çalışma: {schedule.next_run()}")
    logging.info("🔁 Bekleniyor...\n")

    # Ana döngü — crash korumalı
    consecutive_errors = 0
    while True:
        try:
            schedule.run_pending()
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            logging.error(f"⚠️ Scheduler döngü hatası #{consecutive_errors}: {e}")
            if consecutive_errors >= 10:
                logging.error("🔴 10 ardışık hata! 5 dakika bekleniyor...")
                time.sleep(300)
                consecutive_errors = 0

        time.sleep(30)


if __name__ == '__main__':
    main()

"""
🔄 Unified Worker — Kapak Üretimi + Revizyon Kontrolü (Tek Cron Servis)
========================================================================
Günde 3 kez Railway Cron ile çalışır (0 7,13,19 * * *).
1. Önce yeni videoların kapaklarını üretir (main.py → process_ready_videos)
2. Sonra revizyon bekleyen feedback'leri işler (check_revisions_job.py → run_cron_job)
İş yoksa anında çıkar.
"""

import sys
import time
import datetime
from dotenv import load_dotenv

load_dotenv()


def main():
    start = datetime.datetime.utcnow()
    print(f"\n{'='*60}")
    print(f"🚀 Unified Worker başlatıldı — {start.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*60}\n")

    errors = 0

    # ── Adım 1: Yeni kapak üretimi ──
    print("📸 [1/2] Kapak üretimi başlıyor...")
    try:
        from main import process_ready_videos
        process_ready_videos()
    except Exception as e:
        print(f"❌ Kapak üretimi hatası: {e}", file=sys.stderr)
        errors += 1

    # ── Adım 2: Revizyon kontrolü ──
    print("\n🔄 [2/2] Revizyon kontrolü başlıyor...")
    try:
        from check_revisions_job import run_cron_job
        run_cron_job()
    except Exception as e:
        print(f"❌ Revizyon kontrolü hatası: {e}", file=sys.stderr)
        errors += 1

    # ── Özet ──
    elapsed = (datetime.datetime.utcnow() - start).total_seconds()
    print(f"\n{'='*60}")
    if errors == 0:
        print(f"✅ Unified Worker tamamlandı — {elapsed:.1f} saniye")
    elif errors == 1:
        print(f"⚠️ Unified Worker tamamlandı (1 adımda hata) — {elapsed:.1f} saniye")
    else:
        print(f"❌ Unified Worker tamamlandı (tüm adımlar hatalı) — {elapsed:.1f} saniye")
    print(f"{'='*60}")

    return errors


if __name__ == "__main__":
    errors = main()
    sys.exit(1 if errors >= 2 else 0)

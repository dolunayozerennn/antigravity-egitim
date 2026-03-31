import os
import time
import schedule
from main import process_ready_videos

def job():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled run...")
    try:
        process_ready_videos()
    except Exception as e:
        print(f"Error during scheduled run: {e}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scheduled run finished.\n")

# Run once and exit (for Railway Cron)
if __name__ == "__main__":
    print("\nExecuting run...")
    job()
    print("Worker finished successfully.")
    import sys
    sys.exit(0)

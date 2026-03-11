#!/usr/bin/env python3
"""
Rakipler.csv'deki Instagram profillerinden Apify Instagram Reel Scraper ile
reels verilerini çeken script.
"""

import csv
import json
import time
import sys
import requests

# ── Config ──────────────────────────────────────────────────────────────────
APIFY_TOKEN = "apify_api_lwsaQjTTemCehNTswvPxyCE5L9R8Ey12MI25"
ACTOR_ID = "shu8hvrXbJbY3Eb9W"
CSV_PATH = "Rakipler.csv"
OUTPUT_PATH = "data/raw_reels.json"
RESULTS_PER_PROFILE = 30  # Her profil için max reels sayısı
POLL_INTERVAL = 10  # saniye

# ── Helpers ─────────────────────────────────────────────────────────────────

def read_profiles(csv_path: str) -> list[str]:
    """Rakipler.csv'den profil URL'lerini okur ve duplicate'leri temizler."""
    urls = []
    seen = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row["Link"].strip().rstrip("/")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    print(f"[INFO] {len(urls)} benzersiz profil bulundu.")
    return urls


def start_actor_run(urls: list[str]) -> dict:
    """Apify aktörünü başlatır."""
    endpoint = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "directUrls": urls,
        "resultsType": "posts",
        "resultsLimit": RESULTS_PER_PROFILE,
    }

    print("[INFO] Apify aktörü başlatılıyor...")
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    run_data = resp.json()["data"]
    run_id = run_data["id"]
    print(f"[INFO] Çalışma başlatıldı → run_id: {run_id}")
    return run_data


def poll_run(run_id: str) -> str:
    """Çalışma tamamlanana kadar polling yapar. Dataset ID döner."""
    endpoint = f"https://api.apify.com/v2/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}

    while True:
        resp = requests.get(endpoint, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data["status"]
        print(f"  ⏳ Durum: {status}")

        if status == "SUCCEEDED":
            dataset_id = data["defaultDatasetId"]
            print(f"[INFO] ✅ Çalışma tamamlandı! Dataset: {dataset_id}")
            return dataset_id
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"[ERROR] ❌ Çalışma başarısız: {status}")
            sys.exit(1)

        time.sleep(POLL_INTERVAL)


def fetch_results(dataset_id: str) -> list[dict]:
    """Dataset'ten sonuçları çeker."""
    endpoint = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    params = {"format": "json", "clean": "true"}

    print("[INFO] Sonuçlar indiriliyor...")
    resp = requests.get(endpoint, headers=headers, params=params, timeout=120)
    resp.raise_for_status()
    items = resp.json()
    print(f"[INFO] {len(items)} reel verisi indirildi.")
    return items


def save_results(items: list[dict], output_path: str):
    """Sonuçları JSON olarak kaydeder."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Sonuçlar kaydedildi → {output_path}")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    # Dry-run mode
    if "--dry-run" in sys.argv:
        urls = read_profiles(CSV_PATH)
        print("[DRY-RUN] Aşağıdaki profiller scrape edilecek:")
        for u in urls:
            print(f"  • {u}")
        print(f"[DRY-RUN] Toplam tahmini sonuç: {len(urls) * RESULTS_PER_PROFILE}")
        return

    urls = read_profiles(CSV_PATH)
    run_data = start_actor_run(urls)
    dataset_id = poll_run(run_data["id"])
    items = fetch_results(dataset_id)
    save_results(items, OUTPUT_PATH)

    # Kısa özet
    profiles_found = set()
    for item in items:
        owner = item.get("ownerUsername") or item.get("inputUrl", "")
        profiles_found.add(owner)

    print(f"\n{'='*60}")
    print(f"📊 ÖZET")
    print(f"{'='*60}")
    print(f"  Profil sayısı: {len(profiles_found)}")
    print(f"  Toplam reel  : {len(items)}")
    print(f"  Çıktı dosyası: {OUTPUT_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

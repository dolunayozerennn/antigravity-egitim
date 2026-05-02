#!/usr/bin/env python3
"""
Scraper modülü — Rakip influencer'ların son reels'lerini Apify ile çeker.

Her hafta çalışarak yeni marka mention'larını tespit etmek için veri sağlar.
"""

import csv
import json
import os
import time
import requests
import random
from datetime import datetime, timezone, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAKIPLER_CSV = os.path.join(BASE_DIR, "config", "rakipler.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "raw_reels.json")
ACTOR_ID = "shu8hvrXbJbY3Eb9W"  # Apify Instagram Reel Scraper
RESULTS_PER_PROFILE = 4  # Son 4 reel/profil (haftalık 1 reels varsayımı)
POLL_INTERVAL = 15  # saniye


def get_all_apify_tokens():
    """Apify token'larını env var'lardan topla ve liste olarak döndür (Rotasyon için)."""
    keys = []
    
    # Yeni yapı: APIFY_API_KEY_1, APIFY_API_KEY_2 vs.
    for i in range(1, 10):
        val = os.environ.get(f"APIFY_API_KEY_{i}")
        if val and val not in keys:
            keys.append(val)
            
    # Geriye dönük uyumluluk
    val = os.environ.get("APIFY_API_KEY")
    if val and val not in keys:
        keys.append(val)
    val = os.environ.get("APIFY_BACKUP_TOKEN")
    if val and val not in keys:
        keys.append(val)
            
    if not keys:
        # Lokal fallback: master.env üzerinden APIFY_API_KEY_*
        try:
            from env_loader import get_env as _ge
        except ImportError:
            _ge = None
        if _ge:
            for i in range(1, 10):
                v = _ge(f"APIFY_API_KEY_{i}")
                if v and v not in keys:
                    keys.append(v)
            v = _ge("APIFY_API_KEY")
            if v and v not in keys:
                keys.append(v)

    if keys:
        # Rastgeleliyi koruyarak load balancing yapalım
        random.shuffle(keys)
    return keys


def _apify_token_health(token, timeout=4):
    """Apify /users/me ile token'ın aylık quota kullanım oranını döndürür.

    Returns:
        float | None: 0.0–1.0 arası kullanım oranı, hata/erişim yoksa None.
    """
    try:
        r = requests.get(
            "https://api.apify.com/v2/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
        if r.status_code != 200:
            return None
        data = r.json().get("data", {}).get("plan", {}) or {}
        # Hesap planına göre alan adı değişebilir; en yaygınlarını dener.
        usage = data.get("monthlyUsageUsd") or data.get("monthlyUsage") or 0
        limit = data.get("monthlyLimitUsd") or data.get("monthlyLimit") or 0
        if not limit:
            return None
        return float(usage) / float(limit)
    except requests.exceptions.RequestException:
        return None


def prefer_healthy_tokens(keys, threshold=0.95):
    """Quota'sı dolmaya yakın token'ları listenin sonuna iter.

    Çağrı başına token başına ~1 ek HTTP isteği maliyetlidir; sadece
    pipeline başlangıcında bir kez çağrılması beklenir. Quota öğrenilemezse
    sıralama korunur.
    """
    healthy, exhausted = [], []
    for k in keys:
        ratio = _apify_token_health(k)
        (exhausted if ratio is not None and ratio >= threshold else healthy).append(k)
    return healthy + exhausted


def read_profiles(csv_path=None):
    """Rakipler CSV'den profil URL'lerini okur. Sadece Instagram URL'lerini döner."""
    csv_path = csv_path or RAKIPLER_CSV
    urls = []
    skipped = []
    seen = set()
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row["Link"].strip().rstrip("/")
            if not url or url in seen:
                continue
            seen.add(url)
            # Apify Instagram Scraper sadece instagram.com URL kabul eder
            if "instagram.com" in url:
                urls.append(url)
            else:
                skipped.append(url)
    if skipped:
        print(f"[SCRAPER] ⚠️ {len(skipped)} Instagram dışı URL atlandı: {skipped}")
    print(f"[SCRAPER] {len(urls)} benzersiz Instagram profili bulundu.")
    return urls


def start_actor_run(urls, token):
    """Apify aktörünü başlatır."""
    endpoint = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "directUrls": urls,
        "resultsType": "posts",
        "resultsLimit": RESULTS_PER_PROFILE,
    }

    print("[SCRAPER] Apify aktörü başlatılıyor...")
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    run_data = resp.json()["data"]
    run_id = run_data["id"]
    print(f"[SCRAPER] Çalışma başlatıldı → run_id: {run_id}")
    return run_data


def poll_run(run_id, token):
    """Çalışma tamamlanana kadar polling yapar."""
    endpoint = f"https://api.apify.com/v2/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {token}"}

    while True:
        resp = requests.get(endpoint, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data["status"]
        print(f"  ⏳ Durum: {status}")

        if status == "SUCCEEDED":
            dataset_id = data["defaultDatasetId"]
            print(f"[SCRAPER] ✅ Çalışma tamamlandı! Dataset: {dataset_id}")
            return dataset_id
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise Exception(f"Apify çalışma başarısız: {status}")

        time.sleep(POLL_INTERVAL)


def fetch_results(dataset_id, token):
    """Dataset'ten sonuçları çeker."""
    endpoint = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"format": "json", "clean": "true"}

    print("[SCRAPER] Sonuçlar indiriliyor...")
    resp = requests.get(endpoint, headers=headers, params=params, timeout=120)
    resp.raise_for_status()
    items = resp.json()
    print(f"[SCRAPER] {len(items)} reel verisi indirildi.")
    return items


def scrape_reels(dry_run=False):
    """
    Ana scrape fonksiyonu. Rakiplerin son reels'lerini çeker.
    
    Returns:
        list[dict]: Reel verileri listesi
    """
    urls = read_profiles()

    if dry_run:
        print("[DRY-RUN] Aşağıdaki profiller scrape edilecek (Simülasyon):")
        for u in urls:
            print(f"  • {u}")
        print(f"[DRY-RUN] Toplam tahmini sonuç: {len(urls) * RESULTS_PER_PROFILE}")
        if os.path.exists(OUTPUT_PATH):
            print(f"[DRY-RUN] {OUTPUT_PATH} dosyası bulundu, simülasyon için kullanılıyor...")
            with open(OUTPUT_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        print("[DRY-RUN] Local data bulunamadı, simülasyon devam edemiyor.")
        return []

    keys = get_all_apify_tokens()
    if not keys:
        raise ValueError("Apify token bulunamadı! APIFY_API_KEY env var ayarla.")

    last_err = None
    for token in keys:
        try:
            print(f"[SCRAPER] Apify deneniyor. (Token Prefix: {token[:6]}...)")
            run_data = start_actor_run(urls, token)
            dataset_id = poll_run(run_data["id"], token)
            items = fetch_results(dataset_id, token)

            # Sonuçları kaydet
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            with open(OUTPUT_PATH, "w", encoding="utf-8-sig") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[SCRAPER] Sonuçlar kaydedildi → {OUTPUT_PATH}")

            return items
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code in (402, 429):
                    print(f"  ⚠️ Limit aşıldı! (HTTP {e.response.status_code}). Diğer anahtara geçiliyor...")
                    last_err = e
                    continue
            print(f"  ⚠️ Apify çalışma hatası: {e}. Diğer anahtara geçiliyor...")
            last_err = e
            continue
        except Exception as e:
            print(f"  ⚠️ Beklenmeyen Apify hatası: {e}. Diğer anahtara geçiliyor...")
            last_err = e
            continue

    raise Exception(f"Tüm Apify API anahtarları denendi ancak işlem başarısız oldu. Son hata: {last_err}")


def scrape_profile_posts(handle, limit=5, max_wait_seconds=120):
    """Tek bir Instagram profilinin son N paylaşımını çeker.

    Token rotasyonunu (get_all_apify_tokens) reuse eder; quota/rate limit
    durumunda diğer anahtara geçer. Follow-up brand research için kullanılır.

    Returns:
        list[dict]: [{caption, likes_count, url, timestamp}, ...]
    """
    if not handle:
        return []

    handle = handle.lstrip("@").strip()
    keys = get_all_apify_tokens()
    if not keys:
        print(f"[SCRAPER] ⚠️ @{handle} için Apify token yok, atlanıyor.")
        return []

    payload = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": limit,
    }
    poll_iters = max(1, max_wait_seconds // POLL_INTERVAL)

    for token in keys:
        try:
            resp = requests.post(
                f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            if resp.status_code in (402, 429):
                print(f"  ⚠️ @{handle} Apify limit (HTTP {resp.status_code}), token değişiyor...")
                continue
            if resp.status_code != 201:
                print(f"  ⚠️ @{handle} Apify başlatılamadı (HTTP {resp.status_code})")
                continue

            run_id = resp.json()["data"]["id"]
            for _ in range(poll_iters):
                time.sleep(POLL_INTERVAL)
                status_resp = requests.get(
                    f"https://api.apify.com/v2/actor-runs/{run_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
                status = status_resp.json()["data"]["status"]
                if status == "SUCCEEDED":
                    dataset_id = status_resp.json()["data"]["defaultDatasetId"]
                    items = requests.get(
                        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=60,
                    ).json()
                    return [
                        {
                            "caption": (item.get("caption") or "")[:280],
                            "likes_count": item.get("likesCount", 0),
                            "url": item.get("url", ""),
                            "timestamp": item.get("timestamp", ""),
                        }
                        for item in (items or [])[:limit]
                    ]
                if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    print(f"  ⚠️ @{handle} Apify run {status}")
                    break
        except requests.exceptions.RequestException as e:
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (402, 429):
                continue
            print(f"  ⚠️ @{handle} scrape hatası: {e}")
            continue

    return []


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    scrape_reels(dry_run=dry)

#!/usr/bin/env python3
"""
1_influencer_bul.py — Adım 1
Instagram ve TikTok'tan influencer profilleri toplar.

Kullanım:
  python3 1_influencer_bul.py                  # Hem Instagram hem TikTok
  python3 1_influencer_bul.py --platform insta  # Sadece Instagram
  python3 1_influencer_bul.py --platform tiktok # Sadece TikTok
"""

import json
import sys
import time
import requests
from config import (
    APIFY_TOKEN,
    INSTAGRAM_KEYWORDS,
    INSTAGRAM_HASHTAGS,
    TIKTOK_KEYWORDS,
    HEDEF_PROFIL,
    INPUT_RAW,
)

BASE_URL = "https://api.apify.com/v2"


# ─────────────────────────────────────────────
# Apify Actor Çalıştırıcı
# ─────────────────────────────────────────────

def run_actor(actor_id: str, run_input: dict) -> str:
    """Apify actor'ı başlatır ve run_id döndürür."""
    url = f"{BASE_URL}/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    resp = requests.post(url, json={"input": run_input}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def wait_for_run(run_id: str, timeout: int = 300) -> bool:
    """Actor run tamamlanana kadar bekler."""
    url = f"{BASE_URL}/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(url, headers=headers, timeout=10)
        status = resp.json()["data"]["status"]
        print(f"  ⏳ Durum: {status} ({elapsed}s)")
        if status == "SUCCEEDED":
            return True
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  ❌ Hata: {status}")
            return False
        time.sleep(10)
        elapsed += 10
    return False


def get_results(run_id: str) -> list:
    """Tamamlanan run'dan sonuçları çeker."""
    url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=30)
    return resp.json()


# ─────────────────────────────────────────────
# Instagram Scraping
# ─────────────────────────────────────────────

def scrape_instagram_by_hashtag(hashtag: str) -> list:
    """Belirtilen hashtag'den profil toplar."""
    print(f"\n📸 Instagram Hashtag taranıyor: #{hashtag}")
    run_input = {
        "hashtags": [hashtag.lstrip("#")],
        "resultsLimit": 100,
        "scrapePostsUntilDate": "",
    }
    run_id = run_actor("apify/instagram-hashtag-scraper", run_input)
    if wait_for_run(run_id):
        return get_results(run_id)
    return []


def scrape_instagram_by_keyword(keyword: str) -> list:
    """Arama kelimesiyle profil toplar."""
    print(f"\n📸 Instagram Keyword taranıyor: {keyword}")
    run_input = {
        "search": keyword,
        "searchType": "user",
        "searchLimit": 50,
    }
    run_id = run_actor("apify/instagram-search-scraper", run_input)
    if wait_for_run(run_id):
        return get_results(run_id)
    return []


def scrape_instagram_profiles(usernames: list) -> list:
    """Belirtilen kullanıcı adlarının profil detaylarını çeker."""
    print(f"\n📸 {len(usernames)} Instagram profili detaylandırılıyor...")
    run_input = {
        "usernames": usernames,
        "resultsLimit": 1,
    }
    run_id = run_actor("apify/instagram-profile-scraper", run_input)
    if wait_for_run(run_id):
        return get_results(run_id)
    return []


# ─────────────────────────────────────────────
# TikTok Scraping
# ─────────────────────────────────────────────

def scrape_tiktok_by_keyword(keyword: str) -> list:
    """TikTok'ta keyword ile kullanıcı arar."""
    print(f"\n🎵 TikTok Keyword taranıyor: {keyword}")
    run_input = {
        "keywords": [keyword],
        "maxResults": 50,
    }
    run_id = run_actor("clockworks/tiktok-user-search-scraper", run_input)
    if wait_for_run(run_id):
        return get_results(run_id)
    return []


def scrape_tiktok_profiles(usernames: list) -> list:
    """TikTok profil detaylarını çeker."""
    print(f"\n🎵 {len(usernames)} TikTok profili detaylandırılıyor...")
    run_input = {
        "profiles": usernames,
        "resultsPerPage": 1,
    }
    run_id = run_actor("clockworks/tiktok-profile-scraper", run_input)
    if wait_for_run(run_id):
        return get_results(run_id)
    return []


# ─────────────────────────────────────────────
# Filtreleme & Normalleştirme
# ─────────────────────────────────────────────

MIN_TAK = HEDEF_PROFIL.get("minimum_takipci", 0)
MAX_TAK = HEDEF_PROFIL.get("maksimum_takipci", 99999999)


def normalize_instagram(raw: dict) -> dict | None:
    """Ham Instagram verisini standart formata çevirir."""
    username = raw.get("username") or raw.get("ownerUsername") or ""
    followers = raw.get("followersCount") or raw.get("followsCount") or 0
    bio = raw.get("biography") or raw.get("bio") or ""

    if not username:
        return None
    if not (MIN_TAK <= followers <= MAX_TAK):
        return None

    return {
        "platform": "Instagram",
        "kullanici_adi": username,
        "profil_url": f"https://www.instagram.com/{username}/",
        "takipci": followers,
        "bio": bio,
        "tam_ad": raw.get("fullName") or raw.get("name") or "",
        "website": raw.get("externalUrl") or raw.get("website") or "",
        "email_bio": "",       # Adım 2'de doldurulacak
        "email_buton": "",     # Adım 2'de doldurulacak (mobil Instagram butonu)
        "email_hunter": "",    # Adım 2'de doldurulacak
        "email_apollo": "",    # Adım 2'de doldurulacak
        "email_final": "",     # Adım 2'de doldurulacak (en iyi email)
    }


def normalize_tiktok(raw: dict) -> dict | None:
    """Ham TikTok verisini standart formata çevirir."""
    username = raw.get("uniqueId") or raw.get("username") or ""
    followers = raw.get("followerCount") or raw.get("fans") or 0
    bio = raw.get("signature") or raw.get("bio") or ""

    if not username:
        return None
    if not (MIN_TAK <= followers <= MAX_TAK):
        return None

    return {
        "platform": "TikTok",
        "kullanici_adi": username,
        "profil_url": f"https://www.tiktok.com/@{username}",
        "takipci": followers,
        "bio": bio,
        "tam_ad": raw.get("nickname") or raw.get("name") or "",
        "website": raw.get("bioLink") or "",
        "email_bio": "",
        "email_buton": "",
        "email_hunter": "",
        "email_apollo": "",
        "email_final": "",
    }


# ─────────────────────────────────────────────
# Ana Fonksiyon
# ─────────────────────────────────────────────

def main():
    if not APIFY_TOKEN:
        print("❌ HATA: config.py dosyasında APIFY_TOKEN boş! Lütfen doldur.")
        return

    platform_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--platform" and i + 1 < len(sys.argv):
            platform_filter = sys.argv[i + 1].lower()

    all_influencers = []
    seen_usernames = set()

    # ── Instagram ──────────────────────────────
    if platform_filter in (None, "insta", "instagram"):
        if not INSTAGRAM_KEYWORDS and not INSTAGRAM_HASHTAGS:
            print("⚠️  config.py'de INSTAGRAM_KEYWORDS veya INSTAGRAM_HASHTAGS boş. Atlıyorum.")
        else:
            raw_insta_items = []

            for keyword in INSTAGRAM_KEYWORDS:
                raw_insta_items.extend(scrape_instagram_by_keyword(keyword))

            for hashtag in INSTAGRAM_HASHTAGS:
                raw_insta_items.extend(scrape_instagram_by_hashtag(hashtag))

            print(f"\n📊 Instagram'dan {len(raw_insta_items)} ham kayıt alındı.")

            for item in raw_insta_items:
                normalized = normalize_instagram(item)
                if normalized and normalized["kullanici_adi"] not in seen_usernames:
                    seen_usernames.add(normalized["kullanici_adi"])
                    all_influencers.append(normalized)

    # ── TikTok ────────────────────────────────
    if platform_filter in (None, "tiktok"):
        if not TIKTOK_KEYWORDS:
            print("⚠️  config.py'de TIKTOK_KEYWORDS boş. Atlıyorum.")
        else:
            raw_tiktok_items = []

            for keyword in TIKTOK_KEYWORDS:
                raw_tiktok_items.extend(scrape_tiktok_by_keyword(keyword))

            print(f"\n📊 TikTok'tan {len(raw_tiktok_items)} ham kayıt alındı.")

            for item in raw_tiktok_items:
                normalized = normalize_tiktok(item)
                if normalized and normalized["kullanici_adi"] not in seen_usernames:
                    seen_usernames.add(normalized["kullanici_adi"])
                    all_influencers.append(normalized)

    # Takipçi sayısına göre sırala
    all_influencers.sort(key=lambda x: -x["takipci"])

    # Kaydet
    import os
    os.makedirs("data", exist_ok=True)
    with open(INPUT_RAW, "w", encoding="utf-8") as f:
        json.dump(all_influencers, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ TAMAMLANDI: {len(all_influencers)} influencer bulundu.")
    print(f"📁 Kaydedildi: {INPUT_RAW}")
    print(f"{'='*60}")
    for i, inf in enumerate(all_influencers[:10], 1):
        print(f"  {i:2d}. [{inf['platform']:9s}] @{inf['kullanici_adi']:25s} | {inf['takipci']:>8,} takipçi")
    if len(all_influencers) > 10:
        print(f"  ... ve {len(all_influencers) - 10} tane daha")
    print(f"\n➡️  Sonraki adım: python3 2_email_topla.py")


if __name__ == "__main__":
    main()

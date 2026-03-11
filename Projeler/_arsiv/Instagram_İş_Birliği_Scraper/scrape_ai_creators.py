#!/usr/bin/env python3
"""
Instagram'da İngilizce yapay zeka (AI) içeriği paylaşan 10 içerik üreticiyi bulan,
profil analizini yapan ve son 30 günde yayınlanan post/reels sayısını hesaplayan script.

Kullanılan Apify Aktörleri:
  1. crawler-bros/instagram-keyword-search-scraper  → anahtar keline ile post/profil tarama
  2. apify/instagram-scraper                        → profil detaylarını çekme
"""

import json
import os
from datetime import datetime, timezone, timedelta
from apify_client import ApifyClient

# ── Config ───────────────────────────────────────────────────────────────────
APIFY_TOKEN  = "apify_api_lwsaQjTTemCehNTswvPxyCE5L9R8Ey12MI25"
MAX_CREATORS = 10
CUTOFF_DAYS  = 30

# Yapay zeka alanında İngilizce içerik bulduran anahtar kelimeler
AI_KEYWORDS = [
    "artificial intelligence",
    "AI tools",
    "ChatGPT tips",
    "machine learning",
    "generative AI",
]

client = ApifyClient(APIFY_TOKEN)

# ── Helpers ──────────────────────────────────────────────────────────────────

def count_posts_last_n_days(posts: list, days: int = 30) -> int:
    """Verilen post listesinden son `days` gün içindeki kaç post olduğunu döner."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    count = 0
    for post in posts:
        ts = post.get("timestamp") or post.get("takenAt") or post.get("time")
        if not ts:
            continue
        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if dt >= cutoff:
                count += 1
        except Exception as e:
            print(f"  [WARN] Tarih ayrıştırma hatası: {ts} → {e}")
    return count


def is_likely_english(profile: dict) -> bool:
    """Bio'nun ağırlıklı olarak Latin alfabesiyle yazılıp yazılmadığını kontrol eder."""
    bio = (profile.get("biography") or "").strip()
    if len(bio) < 10:
        return True  # Bio yoksa dahil et
    latin = sum(1 for c in bio if c.isalpha() and ord(c) < 256)
    return (latin / len(bio)) > 0.65


# ── Ana akış ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("🤖 Instagram AI İçerik Üreticisi Scraper")
    print(f"   Hedef: {MAX_CREATORS} üretici | Analiz: son {CUTOFF_DAYS} gün")
    print("=" * 65)

    # ── Adım 1: Anahtar kelimelerle kullanıcı adlarını topla ─────────────
    print(f"\n📌 Adım 1: AI keyword'leriyle profil aranıyor...")

    seen_users: set = set()
    usernames_ordered: list = []

    for keyword in AI_KEYWORDS:
        if len(usernames_ordered) >= MAX_CREATORS * 5:
            break
        print(f"  🔍 Keyword: \"{keyword}\"")
        try:
            run = client.actor("crawler-bros/instagram-keyword-search-scraper").call(
                run_input={
                    "keyword": keyword,
                    "resultsLimit": 50,
                }
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            print(f"     → {len(items)} sonuç")
            for item in items:
                u = item.get("ownerUsername") or item.get("username")
                if u and u not in seen_users:
                    seen_users.add(u)
                    usernames_ordered.append(u)
        except Exception as e:
            print(f"  [WARN] Keyword hatası ({keyword}): {e}")
            continue

    print(f"\n[INFO] Toplam {len(usernames_ordered)} benzersiz kullanıcı adı bulundu.")

    if not usernames_ordered:
        print("[ERROR] Hiç kullanıcı bulunamadı. Çıkılıyor.")
        return

    # Profil URL listesi oluştur
    selected = usernames_ordered[: MAX_CREATORS * 4]
    profile_urls = [f"https://www.instagram.com/{u}/" for u in selected]

    # ── Adım 2: Profil detaylarını çek ───────────────────────────────────
    print(f"\n📌 Adım 2: {len(profile_urls)} profil detayı çekiliyor...")
    try:
        profile_run = client.actor("apify/instagram-scraper").call(
            run_input={
                "directUrls": profile_urls,
                "resultsType": "details",
                "resultsLimit": 30,
            }
        )
        profiles = list(client.dataset(profile_run["defaultDatasetId"]).iterate_items())
    except Exception as e:
        print(f"[ERROR] Profil çekme hatası: {e}")
        return

    print(f"[INFO] {len(profiles)} profil detayı indirildi.")

    # ── Adım 3: Analiz ────────────────────────────────────────────────────
    print(f"\n📌 Adım 3: Profiller analiz ediliyor (son {CUTOFF_DAYS} gün)...")

    results: list = []
    for profile in profiles:
        username = profile.get("username")
        if not username:
            continue

        if not is_likely_english(profile):
            print(f"  [SKIP] @{username} – Latin dışı bio, atlanıyor.")
            continue

        latest_posts = profile.get("latestPosts") or []
        posts_30d = count_posts_last_n_days(latest_posts, CUTOFF_DAYS)

        results.append({
            "sira": len(results) + 1,
            "username": username,
            "full_name": profile.get("fullName") or "",
            "followers": profile.get("followersCount") or 0,
            "following": profile.get("followingCount") or 0,
            "total_posts": profile.get("postsCount") or 0,
            "biography": (profile.get("biography") or "")[:200],
            "profile_url": f"https://www.instagram.com/{username}/",
            "posts_last_30_days": posts_30d,
            "verified": profile.get("verified") or False,
            "is_business": profile.get("isBusinessAccount") or False,
        })

        if len(results) >= MAX_CREATORS:
            break

    # ── Çıktı ─────────────────────────────────────────────────────────────
    print(f"\n{'=' * 65}")
    print(f"📊 SONUÇLAR — İngilizce Yapay Zeka İçerik Üreticileri")
    print(f"   Analiz penceresi: Son {CUTOFF_DAYS} gün")
    print(f"{'=' * 65}")

    for r in results:
        verified_badge = " ✅" if r["verified"] else ""
        biz_badge = "🏢" if r["is_business"] else "👤"
        print(f"\n{r['sira']:2d}. {biz_badge} @{r['username']}{verified_badge}")
        print(f"     İsim          : {r['full_name']}")
        print(f"     Takipçi       : {r['followers']:,}")
        print(f"     Toplam Post   : {r['total_posts']:,}")
        print(f"     📅 Son 30 Günde Post/Reels: {r['posts_last_30_days']}")
        bio_preview = r["biography"][:120] + "..." if len(r["biography"]) > 120 else r["biography"]
        print(f"     Bio           : {bio_preview}")
        print(f"     URL           : {r['profile_url']}")

    # JSON kaydet
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ai_creators_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_posts_30d = sum(r["posts_last_30_days"] for r in results)
    print(f"\n{'=' * 65}")
    print(f"✅ Toplamda {len(results)} üretici analiz edildi.")
    print(f"📅 Bu hesaplar son 30 günde TOPLAM {total_posts_30d} post/reels paylaştı.")
    print(f"💾 Sonuçlar kaydedildi → {out_path}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
kampanya_baslat.py — Lead Bulma + Email Toplama (Birleşik Parametrik Script)

Bu script, Buğra projesindeki 1_influencer_bul.py ve 2_email_topla.py scriptlerini
tek bir parametrik script olarak birleştirir. YAML config dosyasından parametreleri
okuyarak herhangi bir kampanya için çalışabilir.

Kullanım:
  python3 kampanya_baslat.py --config config/bugra-influencer.yaml
  python3 kampanya_baslat.py --config config/sweatcoin-outreach.yaml --sadece-lead
  python3 kampanya_baslat.py --config config/creative-sourcing.yaml --sadece-email

Kaynak: Projeler/Bugra_Influencer_Kampanya/1_influencer_bul.py + 2_email_topla.py birleştirildi
Referans: _agents/musteri-kazanim/AGENT.md
"""

import argparse
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests
import yaml

# ═══════════════════════════════════════════════════
# 🔑 API ANAHTAR YÖNETİMİ
# ═══════════════════════════════════════════════════

def api_anahtari_oku(anahtar_adi: str) -> str:
    """
    API anahtarını şu sırayla arar:
    1. Environment variable
    2. _knowledge/api-anahtarlari.md dosyasından parse
    """
    # 1. Environment variable
    env_val = os.environ.get(anahtar_adi, "")
    if env_val:
        return env_val

    # 2. _knowledge/api-anahtarlari.md
    bilgi_dosyasi = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "_knowledge", "api-anahtarlari.md"
    )
    bilgi_dosyasi = os.path.normpath(bilgi_dosyasi)

    if os.path.exists(bilgi_dosyasi):
        with open(bilgi_dosyasi, "r", encoding="utf-8") as f:
            icerik = f.read()
        # Basit arama: "ANAHTAR_ADI: deger" veya "ANAHTAR_ADI=deger" formatı
        for satir in icerik.split("\n"):
            if anahtar_adi in satir:
                # "key: value" veya "key=value" veya "`key`" formatlarını dene
                for ayirici in [":", "=", "`"]:
                    if ayirici in satir:
                        parca = satir.split(ayirici)
                        if len(parca) >= 2:
                            deger = parca[-1].strip().strip("`").strip("\"").strip("'")
                            if deger and len(deger) > 5:
                                return deger

    return ""


# ═══════════════════════════════════════════════════
# ⚙️ CONFIG YÜKLEME
# ═══════════════════════════════════════════════════

def config_yukle(config_yolu: str) -> dict:
    """YAML config dosyasını yükler."""
    with open(config_yolu, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════
# 🌐 APIFY YARDIMCILARI
# ═══════════════════════════════════════════════════

BASE_URL = "https://api.apify.com/v2"


def run_actor(actor_id: str, run_input: dict, token: str) -> str:
    """Apify actor'ı başlatır ve run_id döndürür."""
    url = f"{BASE_URL}/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, json={"input": run_input}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def wait_for_run(run_id: str, token: str, timeout: int = 300) -> bool:
    """Actor run tamamlanana kadar bekler."""
    url = f"{BASE_URL}/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {token}"}
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


def get_results(run_id: str, token: str) -> list:
    """Tamamlanan run'dan sonuçları çeker."""
    url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    return resp.json()


# ═══════════════════════════════════════════════════
# 📸 PLATFORM SCRAPING FONKSİYONLARI
# ═══════════════════════════════════════════════════

def scrape_instagram_by_keyword(keyword: str, token: str) -> list:
    """Instagram'da keyword ile kullanıcı arar."""
    print(f"\n📸 Instagram Keyword taranıyor: {keyword}")
    run_input = {"search": keyword, "searchType": "user", "searchLimit": 50}
    run_id = run_actor("apify/instagram-search-scraper", run_input, token)
    if wait_for_run(run_id, token):
        return get_results(run_id, token)
    return []


def scrape_instagram_by_hashtag(hashtag: str, token: str) -> list:
    """Instagram'da hashtag ile profil toplar."""
    print(f"\n📸 Instagram Hashtag taranıyor: #{hashtag}")
    run_input = {"hashtags": [hashtag.lstrip("#")], "resultsLimit": 100}
    run_id = run_actor("apify/instagram-hashtag-scraper", run_input, token)
    if wait_for_run(run_id, token):
        return get_results(run_id, token)
    return []


def scrape_tiktok_by_keyword(keyword: str, token: str) -> list:
    """TikTok'ta keyword ile kullanıcı arar."""
    print(f"\n🎵 TikTok Keyword taranıyor: {keyword}")
    run_input = {"keywords": [keyword], "maxResults": 50}
    run_id = run_actor("clockworks/tiktok-user-search-scraper", run_input, token)
    if wait_for_run(run_id, token):
        return get_results(run_id, token)
    return []


def scrape_google_maps(keyword: str, token: str) -> list:
    """Google Maps'te işletme arar."""
    print(f"\n🗺️ Google Maps taranıyor: {keyword}")
    run_input = {"searchStrings": [keyword], "maxCrawledPlaces": 50}
    run_id = run_actor("compass/crawler-google-places", run_input, token)
    if wait_for_run(run_id, token):
        return get_results(run_id, token)
    return []


# ═══════════════════════════════════════════════════
# 🔄 NORMALLEŞTİRME
# ═══════════════════════════════════════════════════

def normalize_instagram(raw: dict, min_tak: int, max_tak: int) -> dict | None:
    """Ham Instagram verisini standart formata çevirir."""
    username = raw.get("username") or raw.get("ownerUsername") or ""
    followers = raw.get("followersCount") or raw.get("followsCount") or 0
    bio = raw.get("biography") or raw.get("bio") or ""

    if not username:
        return None
    if not (min_tak <= followers <= max_tak):
        return None

    return {
        "platform": "Instagram",
        "kullanici_adi": username,
        "profil_url": f"https://www.instagram.com/{username}/",
        "takipci": followers,
        "bio": bio,
        "tam_ad": raw.get("fullName") or raw.get("name") or "",
        "website": raw.get("externalUrl") or raw.get("website") or "",
        "email_bio": "",
        "email_buton": raw.get("publicEmail") or raw.get("businessEmail") or "",
        "email_hunter": "",
        "email_apollo": "",
        "email_final": "",
        "email_kaynagi": "",
    }


def normalize_tiktok(raw: dict, min_tak: int, max_tak: int) -> dict | None:
    """Ham TikTok verisini standart formata çevirir."""
    username = raw.get("uniqueId") or raw.get("username") or ""
    followers = raw.get("followerCount") or raw.get("fans") or 0
    bio = raw.get("signature") or raw.get("bio") or ""

    if not username:
        return None
    if not (min_tak <= followers <= max_tak):
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
        "email_kaynagi": "",
    }


def normalize_google_maps(raw: dict) -> dict | None:
    """Google Maps verisini standart formata çevirir."""
    name = raw.get("title") or raw.get("name") or ""
    if not name:
        return None

    return {
        "platform": "Google Maps",
        "kullanici_adi": name,
        "profil_url": raw.get("url") or "",
        "takipci": 0,
        "bio": raw.get("categoryName") or "",
        "tam_ad": name,
        "website": raw.get("website") or "",
        "email_bio": "",
        "email_buton": "",
        "email_hunter": "",
        "email_apollo": "",
        "email_final": "",
        "email_kaynagi": "",
        "telefon": raw.get("phone") or "",
        "adres": raw.get("address") or "",
    }


# ═══════════════════════════════════════════════════
# 📧 EMAIL TOPLAMA FONKSİYONLARI
# ═══════════════════════════════════════════════════

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)


def extract_emails_from_text(text: str) -> list[str]:
    """Metinden e-posta adreslerini çeker."""
    if not text:
        return []
    return list(set(EMAIL_REGEX.findall(text)))


def get_domain_from_url(url: str) -> str:
    """URL'den domain çıkarır."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc
    return domain.lstrip("www.")


def search_hunter(domain: str, api_key: str) -> str:
    """Hunter.io ile domain'den kişisel e-posta arar."""
    if not api_key or not domain:
        return ""
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": api_key, "limit": 5},
            timeout=10,
        )
        if resp.status_code == 200:
            emails = resp.json().get("data", {}).get("emails", [])
            for e in emails:
                if e.get("type") == "personal":
                    return e["value"]
            if emails:
                return emails[0]["value"]
        elif resp.status_code == 429:
            print("    ⚠️  Hunter.io rate limit.")
    except Exception as ex:
        print(f"    ⚠️  Hunter hatası: {ex}")
    return ""


def search_apollo(domain: str, api_key: str) -> str:
    """Apollo.io ile domain'den kişi ve e-posta arar."""
    if not api_key or not domain:
        return ""
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/people/search",
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
            json={
                "q_organization_domains": domain,
                "page": 1,
                "per_page": 5,
                "person_titles": [
                    "marketing", "partnerships", "influencer",
                    "brand", "pr", "growth", "founder",
                ],
            },
            timeout=10,
        )
        if resp.status_code == 200:
            people = resp.json().get("people", [])
            for p in people:
                email = p.get("email")
                if email:
                    return email
        elif resp.status_code == 429:
            print("    ⚠️  Apollo.io rate limit.")
    except Exception as ex:
        print(f"    ⚠️  Apollo hatası: {ex}")
    return ""


def email_topla(influencer: dict, apify_token: str, hunter_key: str, apollo_key: str) -> dict:
    """
    Tek bir influencer için 3 katmanlı waterfall email bulma.
    Bio/Buton → Hunter → Apollo
    """
    # 1. Bio'dan email
    bio_email = ""
    bio_emails = extract_emails_from_text(influencer.get("bio", ""))
    if bio_emails:
        bio_email = bio_emails[0]
        influencer["email_bio"] = bio_email
        influencer["email_final"] = bio_email
        influencer["email_kaynagi"] = "bio"
        return influencer

    # 2. Instagram business buton email (zaten scraping sırasında alınmış olabilir)
    buton_email = influencer.get("email_buton", "")
    if buton_email:
        influencer["email_final"] = buton_email
        influencer["email_kaynagi"] = "buton"
        return influencer

    # 3. Hunter.io (website varsa)
    website = influencer.get("website", "")
    if website:
        domain = get_domain_from_url(website)
        if domain:
            print(f"  🔍 Hunter.io: {domain}")
            hunter_email = search_hunter(domain, hunter_key)
            if hunter_email:
                print(f"  ✅ Hunter'dan: {hunter_email}")
                influencer["email_hunter"] = hunter_email
                influencer["email_final"] = hunter_email
                influencer["email_kaynagi"] = "hunter"
                return influencer

            # 4. Apollo.io fallback
            print(f"  🔍 Apollo.io: {domain}")
            apollo_email = search_apollo(domain, apollo_key)
            if apollo_email:
                print(f"  ✅ Apollo'dan: {apollo_email}")
                influencer["email_apollo"] = apollo_email
                influencer["email_final"] = apollo_email
                influencer["email_kaynagi"] = "apollo"
                return influencer

    influencer["email_final"] = ""
    influencer["email_kaynagi"] = "not_found"
    return influencer


# ═══════════════════════════════════════════════════
# 🚀 ANA ADIMLAR
# ═══════════════════════════════════════════════════

def adim1_lead_bul(config: dict, apify_token: str) -> list:
    """Adım 1: Platform bazlı lead bulma."""
    icp = config.get("icp", {})
    arama = config.get("arama", {})
    platformlar = icp.get("platform", ["instagram"])
    min_tak = icp.get("minimum_takipci", 0)
    max_tak = icp.get("maksimum_takipci", 99999999)
    max_lead = arama.get("max_lead_sayisi", 100)

    keywords = arama.get("anahtar_kelimeler", [])
    hashtags = arama.get("hashtag_listesi", [])
    tiktok_keywords = arama.get("tiktok_anahtar_kelimeler", keywords)

    all_leads = []
    seen = set()

    for platform in platformlar:
        if platform.lower() in ("instagram", "insta"):
            if not keywords and not hashtags:
                print("⚠️  Instagram için keyword veya hashtag belirtilmemiş.")
            else:
                for kw in keywords:
                    for item in scrape_instagram_by_keyword(kw, apify_token):
                        n = normalize_instagram(item, min_tak, max_tak)
                        if n and n["kullanici_adi"] not in seen:
                            seen.add(n["kullanici_adi"])
                            all_leads.append(n)

                for ht in hashtags:
                    for item in scrape_instagram_by_hashtag(ht, apify_token):
                        n = normalize_instagram(item, min_tak, max_tak)
                        if n and n["kullanici_adi"] not in seen:
                            seen.add(n["kullanici_adi"])
                            all_leads.append(n)

        elif platform.lower() == "tiktok":
            if not tiktok_keywords:
                print("⚠️  TikTok için keyword belirtilmemiş.")
            else:
                for kw in tiktok_keywords:
                    for item in scrape_tiktok_by_keyword(kw, apify_token):
                        n = normalize_tiktok(item, min_tak, max_tak)
                        if n and n["kullanici_adi"] not in seen:
                            seen.add(n["kullanici_adi"])
                            all_leads.append(n)

        elif platform.lower() == "google_maps":
            for kw in keywords:
                for item in scrape_google_maps(kw, apify_token):
                    n = normalize_google_maps(item)
                    if n and n["kullanici_adi"] not in seen:
                        seen.add(n["kullanici_adi"])
                        all_leads.append(n)

    # Takipçi sıralama + limit
    all_leads.sort(key=lambda x: -x.get("takipci", 0))
    all_leads = all_leads[:max_lead]

    return all_leads


def adim2_email_topla(leads: list, apify_token: str, hunter_key: str, apollo_key: str) -> list:
    """Adım 2: Her lead için email toplama (waterfall)."""
    print(f"\n📋 {len(leads)} lead için e-posta aranıyor...\n")

    for i, lead in enumerate(leads, 1):
        username = lead["kullanici_adi"]
        platform = lead["platform"]
        print(f"[{i}/{len(leads)}] @{username} ({platform})")

        lead = email_topla(lead, apify_token, hunter_key, apollo_key)

        if not lead.get("email_final"):
            print(f"  ⚠️  E-posta bulunamadı.")

        time.sleep(1)  # Rate limiting

    return leads


# ═══════════════════════════════════════════════════
# 🏁 MAIN
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Kampanya Başlatıcı — Lead Bulma + Email Toplama"
    )
    parser.add_argument(
        "--config", required=True,
        help="Kampanya config YAML dosyası (ör: config/bugra-influencer.yaml)"
    )
    parser.add_argument(
        "--sadece-lead", action="store_true",
        help="Sadece lead bulma yap, email toplama atlansın"
    )
    parser.add_argument(
        "--sadece-email", action="store_true",
        help="Sadece email toplama yap (mevcut _raw.json dosyasını kullan)"
    )
    args = parser.parse_args()

    # Config yükle
    config = config_yukle(args.config)
    kampanya_adi = config.get("kampanya_adi", "bilinmeyen-kampanya")
    dosyalar = config.get("dosyalar", {})

    print(f"\n{'='*60}")
    print(f"🚀 KAMPANYA BAŞLATILIYOR: {kampanya_adi}")
    print(f"{'='*60}")

    # API anahtarlarını al
    apify_token = api_anahtari_oku("APIFY_TOKEN")
    hunter_key = api_anahtari_oku("HUNTER_API_KEY")
    apollo_key = api_anahtari_oku("APOLLO_API_KEY")

    if not apify_token:
        print("❌ HATA: APIFY_TOKEN bulunamadı!")
        print("   → _knowledge/api-anahtarlari.md dosyasını kontrol et")
        print("   → Veya: export APIFY_TOKEN=...")
        return

    # Data dizini oluştur
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Dosya yollarını belirle
    raw_path = os.path.join(data_dir, f"{kampanya_adi}_raw.json")
    enriched_path = os.path.join(data_dir, f"{kampanya_adi}_enriched.json")

    # ── ADIM 1: Lead Bulma ──────────────────────────
    if not args.sadece_email:
        leads = adim1_lead_bul(config, apify_token)

        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"✅ ADIM 1 TAMAMLANDI: {len(leads)} lead bulundu.")
        print(f"📁 Kaydedildi: {raw_path}")
        print(f"{'='*60}")

        for i, lead in enumerate(leads[:10], 1):
            print(f"  {i:2d}. [{lead['platform']:9s}] @{lead['kullanici_adi']:25s} | {lead.get('takipci', 0):>8,} takipçi")
        if len(leads) > 10:
            print(f"  ... ve {len(leads) - 10} tane daha")
    else:
        # Mevcut raw dosyasını yükle
        if not os.path.exists(raw_path):
            print(f"❌ {raw_path} bulunamadı. Önce --sadece-lead olmadan çalıştır.")
            return
        with open(raw_path, "r", encoding="utf-8") as f:
            leads = json.load(f)
        print(f"📂 Mevcut lead'ler yüklendi: {len(leads)} adet")

    # ── ADIM 2: Email Toplama ──────────────────────
    if not args.sadece_lead:
        leads = adim2_email_topla(leads, apify_token, hunter_key, apollo_key)

        with open(enriched_path, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)

        # Özet
        with_email = [l for l in leads if l.get("email_final")]
        print(f"\n{'='*60}")
        print(f"✅ ADIM 2 TAMAMLANDI")
        print(f"   Toplam lead       : {len(leads)}")
        print(f"   E-posta bulunan   : {len(with_email)}")
        print(f"   E-posta bulunamayan: {len(leads) - len(with_email)}")
        print(f"📁 Kaydedildi: {enriched_path}")
        print(f"{'='*60}")

    print(f"\n➡️  Sonraki adım: python3 scripts/outreach_gonder.py --config {args.config} --dry-run")


if __name__ == "__main__":
    main()

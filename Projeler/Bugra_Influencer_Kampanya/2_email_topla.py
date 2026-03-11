#!/usr/bin/env python3
"""
2_email_topla.py — Adım 2
Bulunan influencerların e-posta adreslerini çeşitli kaynaklardan toplar:

  Kaynak 1: Instagram biyografisi (bio'dan regex ile e-posta extraction)
  Kaynak 2: Instagram "E-posta" butonu (mobil Instagram'daki iletişim butonu)
  Kaynak 3: TikTok biyografisi (bio'dan regex ile e-posta extraction)
  Kaynak 4: Hunter.io (websiteden domain bazlı e-posta arama)
  Kaynak 5: Apollo.io (Hunter yetmezse fallback)

Öncelik sırası: Bio/Buton > Hunter > Apollo
"""

import json
import re
import time
import requests
from urllib.parse import urlparse
from config import (
    APIFY_TOKEN,
    HUNTER_API_KEY,
    APOLLO_API_KEY,
    INPUT_RAW,
    INPUT_EMAILS,
)

BASE_URL = "https://api.apify.com/v2"


# ─────────────────────────────────────────────
# Yardımcı: E-posta Regex
# ─────────────────────────────────────────────

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE
)

def extract_emails_from_text(text: str) -> list[str]:
    """Metinden e-posta adreslerini çeker."""
    if not text:
        return []
    return list(set(EMAIL_REGEX.findall(text)))


# ─────────────────────────────────────────────
# Kaynak 1 & 3: Biyografiden E-posta
# ─────────────────────────────────────────────

def get_email_from_bio(influencer: dict) -> str:
    """Influencer'ın biyografisinden ilk e-postayı döndürür."""
    bio = influencer.get("bio") or ""
    emails = extract_emails_from_text(bio)
    return emails[0] if emails else ""


# ─────────────────────────────────────────────
# Kaynak 2: Instagram İletişim Butonu (Apify)
# ─────────────────────────────────────────────
# Instagram'ın mobil versiyonunda bazı işletme hesaplarında
# "E-posta Gönder" butonu bulunur. Bu buton profil verisinde
# `publicEmail` veya `contactEmail` alanı olarak gelir.

def run_actor(actor_id: str, run_input: dict) -> str:
    url = f"{BASE_URL}/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    resp = requests.post(url, json={"input": run_input}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["id"]

def wait_for_run(run_id: str, timeout: int = 180) -> bool:
    url = f"{BASE_URL}/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(url, headers=headers, timeout=10)
        status = resp.json()["data"]["status"]
        if status == "SUCCEEDED":
            return True
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            return False
        time.sleep(10)
        elapsed += 10
    return False

def get_results(run_id: str) -> list:
    url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=30)
    return resp.json()


def get_instagram_contact_email(username: str) -> str:
    """
    Instagram profil scraper'ından 'publicEmail' (İletişim Butonu) alır.
    Bu alan, işletme hesaplarının Instagram mobil sayfasında gösterdiği
    e-posta butonuna karşılık gelir.
    """
    if not APIFY_TOKEN:
        return ""
    try:
        run_input = {"usernames": [username], "resultsLimit": 1}
        run_id = run_actor("apify/instagram-profile-scraper", run_input)
        if wait_for_run(run_id, timeout=120):
            results = get_results(run_id)
            if results:
                profile = results[0]
                # Apify instagram-profile-scraper bu alanları döndürür:
                return (
                    profile.get("publicEmail") or
                    profile.get("businessEmail") or
                    profile.get("contactEmail") or
                    ""
                )
    except Exception as e:
        print(f"    ⚠️  Instagram buton scrape hatası ({username}): {e}")
    return ""


# ─────────────────────────────────────────────
# Kaynak 4: Hunter.io
# ─────────────────────────────────────────────

def get_domain_from_url(url: str) -> str:
    """URL'den temiz domain çıkarır."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc
    return domain.lstrip("www.")


def search_hunter(domain: str) -> str:
    """Hunter.io ile domain'den kişisel e-posta arar."""
    if not HUNTER_API_KEY or not domain:
        return ""
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 5},
            timeout=10
        )
        if resp.status_code == 200:
            emails = resp.json().get("data", {}).get("emails", [])
            # Kişisel e-postayı tercih et
            for e in emails:
                if e.get("type") == "personal":
                    return e["value"]
            # Yoksa ilk generic'i al
            if emails:
                return emails[0]["value"]
        elif resp.status_code == 429:
            print("    ⚠️  Hunter.io rate limit.")
    except Exception as ex:
        print(f"    ⚠️  Hunter hatası: {ex}")
    return ""


# ─────────────────────────────────────────────
# Kaynak 5: Apollo.io
# ─────────────────────────────────────────────

def search_apollo(domain: str) -> str:
    """Apollo.io ile domain'den kişi ve e-posta arar."""
    if not APOLLO_API_KEY or not domain:
        return ""
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/people/search",
            headers={"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"},
            json={
                "q_organization_domains": domain,
                "page": 1,
                "per_page": 5,
                "person_titles": ["marketing", "partnerships", "influencer", "brand", "pr", "growth", "founder"],
            },
            timeout=10
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


# ─────────────────────────────────────────────
# Ana Fonksiyon
# ─────────────────────────────────────────────

def main():
    try:
        with open(INPUT_RAW, "r", encoding="utf-8") as f:
            influencers = json.load(f)
    except FileNotFoundError:
        print(f"❌ {INPUT_RAW} bulunamadı. Önce: python3 1_influencer_bul.py")
        return

    print(f"📋 {len(influencers)} influencer için e-posta aranıyor...\n")

    for i, inf in enumerate(influencers, 1):
        username = inf["kullanici_adi"]
        platform = inf["platform"]
        website = inf.get("website") or ""

        print(f"[{i}/{len(influencers)}] @{username} ({platform})")

        # Kaynak 1/3: Biyografi
        bio_email = get_email_from_bio(inf)
        if bio_email:
            print(f"  ✅ Bio'dan: {bio_email}")
            inf["email_bio"] = bio_email

        # Kaynak 2: Instagram İletişim Butonu (sadece Instagram için)
        buton_email = ""
        if platform == "Instagram" and APIFY_TOKEN and not bio_email:
            print(f"  🔍 Instagram iletişim butonu kontrol ediliyor...")
            buton_email = get_instagram_contact_email(username)
            if buton_email:
                print(f"  ✅ Instagram buton'dan: {buton_email}")
            inf["email_buton"] = buton_email

        # Kaynak 4: Hunter.io (website varsa)
        hunter_email = ""
        if website and not bio_email and not buton_email:
            domain = get_domain_from_url(website)
            if domain:
                print(f"  🔍 Hunter.io: {domain}")
                hunter_email = search_hunter(domain)
                if hunter_email:
                    print(f"  ✅ Hunter'dan: {hunter_email}")
                inf["email_hunter"] = hunter_email

        # Kaynak 5: Apollo.io (Hunter bulamazsa)
        apollo_email = ""
        if website and not bio_email and not buton_email and not hunter_email:
            domain = get_domain_from_url(website)
            if domain:
                print(f"  🔍 Apollo.io: {domain}")
                apollo_email = search_apollo(domain)
                if apollo_email:
                    print(f"  ✅ Apollo'dan: {apollo_email}")
                inf["email_apollo"] = apollo_email

        # Final e-posta (öncelik: bio/buton > hunter > apollo)
        final = bio_email or buton_email or hunter_email or apollo_email
        inf["email_final"] = final

        if not final:
            print(f"  ⚠️  E-posta bulunamadı.")

        # Rate limiting
        time.sleep(1)

    # Kaydet
    import os
    os.makedirs("data", exist_ok=True)
    with open(INPUT_EMAILS, "w", encoding="utf-8") as f:
        json.dump(influencers, f, ensure_ascii=False, indent=2)

    # Özet
    with_email = [i for i in influencers if i.get("email_final")]
    print(f"\n{'='*60}")
    print(f"✅ TAMAMLANDI")
    print(f"   Toplam influencer  : {len(influencers)}")
    print(f"   E-posta bulunan    : {len(with_email)}")
    print(f"   E-posta bulunamayan: {len(influencers) - len(with_email)}")
    print(f"📁 Kaydedildi: {INPUT_EMAILS}")
    print(f"{'='*60}")
    print(f"\n➡️  Sonraki adım: python3 3_outreach_gonder.py --dry-run")


if __name__ == "__main__":
    main()

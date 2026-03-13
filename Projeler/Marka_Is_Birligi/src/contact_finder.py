#!/usr/bin/env python3
"""
Contact Finder modülü — Yeni bulunan markalar için iletişim bilgisi toplar.

Sırasıyla:
1. Apify contact-info-scraper ile web sitesini tara
2. Hunter.io ile domain email arama
3. Apollo.io ile B2B kişi arama (fallback)
"""

import json
import os
import time
import requests
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_env(key, fallback_lines=None):
    """Env var veya bilgi dosyasından değer al."""
    val = os.environ.get(key)
    if val:
        return val
    # Lokal fallback: _knowledge/api-anahtarlari.md
    knowledge_path = os.path.join(BASE_DIR, "..", "..", "_knowledge", "api-anahtarlari.md")
    if os.path.exists(knowledge_path) and fallback_lines:
        with open(knowledge_path, "r") as f:
            content = f.read()
        for search_term in fallback_lines:
            for line in content.split("\n"):
                if search_term in line:
                    # Backtick içindeki değeri çıkar
                    import re
                    match = re.search(r"`([^`]+)`", line)
                    if match:
                        return match.group(1)
    return None


def get_domain_from_url(url):
    """URL'den domaini çıkarır."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def guess_website_from_handle(handle):
    """Instagram handle'dan olası web sitesini tahmin et."""
    clean = handle.lower().replace("_", "").replace(".", "")
    # Yaygın pattern'ler
    candidates = [
        f"https://{handle.replace('_', '')}.ai",
        f"https://{handle.replace('_', '')}.com",
        f"https://www.{handle.replace('_', '')}.ai",
    ]
    
    # .ai handle'ı varsa direkt dene
    if "ai" in handle.lower() or ".ai" in handle.lower():
        base = handle.lower().replace("_ai", "").replace(".ai", "").replace("_", "")
        candidates.insert(0, f"https://{base}.ai")
    
    for url in candidates:
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                return url
        except:
            continue
    
    return ""


def search_hunter_emails(domain, api_key):
    """Hunter.io API ile domainden email arar."""
    if not api_key:
        return [], None
    
    print(f"  🔍 Hunter.io: {domain}...")
    endpoint = "https://api.hunter.io/v2/domain-search"
    params = {
        "domain": domain,
        "api_key": api_key,
        "limit": 10,
    }

    try:
        resp = requests.get(endpoint, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            
            # Genel email (pattern bazlı)
            general_email = None
            pattern = data.get("pattern")
            if data.get("webmail", False) is False:
                org_name = data.get("organization")
                # info@, hello@, contact@ gibi genel adresler
                for prefix in ["info", "hello", "contact", "partnerships", "business"]:
                    general_email = f"{prefix}@{domain}"
                    break
            
            personal_emails = []
            for e in emails:
                if e.get("type") == "personal":
                    name = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
                    pos = e.get("position", "")
                    personal_emails.append({
                        "email": e["value"],
                        "name": name,
                        "position": pos,
                    })

            return personal_emails, general_email
        elif resp.status_code == 429:
            print("  ⚠️ Hunter.io limit aşıldı.")
    except Exception as e:
        print(f"  ❌ Hunter.io hatası: {e}")

    return [], None


def search_apollo_emails(domain, api_key):
    """Apollo.io API ile domainden email arar."""
    if not api_key:
        return []
    
    print(f"  🔍 Apollo.io: {domain}...")
    endpoint = "https://api.apollo.io/v1/people/search"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }
    payload = {
        "q_organization_domains": domain,
        "page": 1,
        "per_page": 5,
        "person_titles": ["marketing", "growth", "influencer", "founder", "ceo", "partnerships", "brand"],
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            people = resp.json().get("people", [])
            results = []
            for p in people:
                email = p.get("email")
                if email:
                    results.append({
                        "email": email,
                        "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                        "position": p.get("title", ""),
                    })
            return results
    except Exception as e:
        print(f"  ❌ Apollo.io hatası: {e}")

    return []


def find_contacts_for_brand(brand_info):
    """
    Tek bir marka için iletişim bilgisi toplar.
    
    Args:
        brand_info: dict with keys: instagram_handle, marka_adi, website (optional)
    
    Returns:
        dict: {website, general_email, personal_emails, best_email}
    """
    handle = brand_info.get("instagram_handle", "")
    brand_name = brand_info.get("marka_adi", handle)
    website = brand_info.get("website", "")

    print(f"\n📧 İletişim aranıyor: {brand_name} (@{handle})")

    # Web sitesini bul/doğrula
    if not website:
        website = guess_website_from_handle(handle)
        if website:
            print(f"  🌐 Web sitesi tahmin edildi: {website}")
        else:
            print(f"  ⚠️ Web sitesi bulunamadı")

    domain = get_domain_from_url(website)
    if not domain:
        return {
            "website": "",
            "general_email": "",
            "personal_emails": [],
            "best_email": "",
        }

    # API anahtarları
    hunter_key = _get_env("HUNTER_API_KEY", ["Hunter.io", "API Anahtarı"])
    apollo_key = _get_env("APOLLO_API_KEY", ["Apollo.io", "API Anahtarı"])

    # 1. Hunter.io
    personal_emails, general_email = search_hunter_emails(domain, hunter_key)

    # 2. Apollo.io (fallback)
    if not personal_emails:
        personal_emails = search_apollo_emails(domain, apollo_key)

    # Genel email yoksa tahmin et
    if not general_email:
        general_email = f"info@{domain}"

    # En iyi email
    best_email = personal_emails[0]["email"] if personal_emails else general_email

    result = {
        "website": website,
        "general_email": general_email,
        "personal_emails": personal_emails,
        "best_email": best_email,
    }

    print(f"  ✅ Email: {best_email}")
    return result


def enrich_new_brands(new_brands):
    """
    Yeni bulunan markalara iletişim bilgisi ekler.
    
    Args:
        new_brands: list of brand dicts from analyzer
    
    Returns:
        list of enriched brand dicts
    """
    print(f"\n{'='*60}")
    print(f"📧 {len(new_brands)} marka için iletişim bilgisi aranıyor...")
    print(f"{'='*60}")

    enriched = []
    for brand in new_brands:
        contacts = find_contacts_for_brand(brand)
        brand.update(contacts)
        enriched.append(brand)
        time.sleep(1)  # Rate limiting

    found = sum(1 for b in enriched if b.get("best_email"))
    print(f"\n{'='*60}")
    print(f"✅ {found}/{len(enriched)} markaya email bulundu.")
    print(f"{'='*60}")

    return enriched


if __name__ == "__main__":
    # Test: tek marka
    test = find_contacts_for_brand({
        "instagram_handle": "test_ai",
        "marka_adi": "Test AI",
    })
    print(json.dumps(test, indent=2, ensure_ascii=False))

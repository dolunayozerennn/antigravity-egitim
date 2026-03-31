#!/usr/bin/env python3
"""
Contact Finder modülü — Yeni bulunan markalar için iletişim bilgisi toplar.

Pipeline (iyileştirilmiş):
1. Apollo.io Person Search → "influencer", "partnerships", "marketing", "brand", "growth"
   title'lı kişileri bul (doğru karar vericiyi hedefle)
2. Hunter.io Email Finder → Apollo'dan bulunan kişinin emailini al (first_name + last_name + domain)
3. Hunter.io Domain Search → Kişi bulunamazsa domain genelinde email ara
4. Hunter.io Email Verification → Bulunan emaili doğrula (sadece deliverable/accept_all kabul)
5. Doğrulanamayan/bulunamayan → email boş bırakılır, email_status: "not_found"
"""

import json
import os
import re
import time
import requests
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── Doğru kişiyi bulmak için aranan pozisyon anahtar kelimeleri ───
TARGET_TITLES = [
    "influencer",
    "partnerships",
    "marketing manager",
    "brand manager",
    "brand",
    "growth",
    "marketing",
    "influencer marketing",
    "creator partnerships",
    "head of marketing",
    "head of growth",
    "business development",
]


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
        except Exception:
            continue

    return ""


# ═══════════════════════════════════════════════════════════
# ADIM 1: Apollo.io — Doğru kişiyi bul
# ═══════════════════════════════════════════════════════════

def search_apollo_people(domain, api_key):
    """
    Apollo.io People Search — domaindeki influencer/partnerships/marketing
    pozisyonundaki kişileri ara. Email DEĞİL, kişi adı döndürür.

    Returns:
        list of dict: [{first_name, last_name, title, email (varsa)}, ...]
    """
    if not api_key:
        print("  ⚠️ Apollo.io API key yok, atlanıyor.")
        return []

    print(f"  🔍 Apollo.io Person Search: {domain}...")
    endpoint = "https://api.apollo.io/v1/people/search"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }
    payload = {
        "q_organization_domains": domain,
        "page": 1,
        "per_page": 10,
        "person_titles": TARGET_TITLES,
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            people = resp.json().get("people", [])
            results = []
            for p in people:
                first = p.get("first_name", "").strip()
                last = p.get("last_name", "").strip()
                title = p.get("title", "").strip()
                email = p.get("email", "")  # Apollo bazen veriyor

                if first or last:
                    results.append({
                        "first_name": first,
                        "last_name": last,
                        "title": title,
                        "email": email or "",
                    })

            if results:
                print(f"  ✅ Apollo: {len(results)} kişi bulundu")
                for r in results[:3]:
                    print(f"     → {r['first_name']} {r['last_name']} ({r['title']})")
            else:
                print(f"  ℹ️ Apollo: Hedef pozisyonda kişi bulunamadı")

            return results
        elif resp.status_code == 429:
            print("  ⚠️ Apollo.io rate limit aşıldı")
        else:
            print(f"  ⚠️ Apollo.io HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Apollo.io hatası: {e}")

    return []


# ═══════════════════════════════════════════════════════════
# ADIM 2: Hunter.io Email Finder — Kişi adıyla email bul
# ═══════════════════════════════════════════════════════════

def find_email_by_name(domain, first_name, last_name, api_key):
    """
    Hunter.io Email Finder — Bilinen bir kişinin emailini bul.

    Returns:
        str or None: Bulunan email adresi
    """
    if not api_key or (not first_name and not last_name):
        return None

    print(f"  🔍 Hunter.io Email Finder: {first_name} {last_name} @ {domain}...")
    endpoint = "https://api.hunter.io/v2/email-finder"
    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": api_key,
    }

    try:
        resp = requests.get(endpoint, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            email = data.get("email")
            score = data.get("score", 0)

            if email and score >= 50:
                print(f"  ✅ Hunter Email Finder: {email} (score: {score})")
                return email
            elif email:
                print(f"  ⚠️ Hunter Email Finder: {email} (düşük score: {score})")
                return email  # Yine de dene, verify adımı filtreleyecek
            else:
                print(f"  ℹ️ Hunter Email Finder: Email bulunamadı")
        elif resp.status_code == 429:
            print("  ⚠️ Hunter.io rate limit aşıldı")
    except Exception as e:
        print(f"  ❌ Hunter.io Email Finder hatası: {e}")

    return None


# ═══════════════════════════════════════════════════════════
# ADIM 3: Hunter.io Domain Search — Genel email arama
# ═══════════════════════════════════════════════════════════

def search_hunter_domain(domain, api_key):
    """
    Hunter.io Domain Search — Domaindeki emailleri ara.

    Returns:
        tuple: (personal_emails: list, general_emails: list)
            personal_emails: [{email, name, position}, ...]
            general_emails: [email, ...]
    """
    if not api_key:
        return [], []

    print(f"  🔍 Hunter.io Domain Search: {domain}...")
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

            personal_emails = []
            general_emails = []

            for e in emails:
                email_val = e.get("value", "")
                email_type = e.get("type", "")

                if email_type == "personal":
                    name = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
                    pos = e.get("position", "")
                    personal_emails.append({
                        "email": email_val,
                        "name": name,
                        "position": pos,
                    })
                elif email_type == "generic":
                    general_emails.append(email_val)

            if personal_emails:
                print(f"  ✅ Hunter Domain: {len(personal_emails)} kişisel email")
            if general_emails:
                print(f"  ℹ️ Hunter Domain: {len(general_emails)} genel email")
            if not personal_emails and not general_emails:
                print(f"  ℹ️ Hunter Domain: Email bulunamadı")

            return personal_emails, general_emails
        elif resp.status_code == 429:
            print("  ⚠️ Hunter.io rate limit aşıldı")
    except Exception as e:
        print(f"  ❌ Hunter.io Domain Search hatası: {e}")

    return [], []


# ═══════════════════════════════════════════════════════════
# ADIM 4: Hunter.io Email Verification
# ═══════════════════════════════════════════════════════════

def verify_email(email, api_key):
    """
    Hunter.io Email Verification — Emailin gerçek olup olmadığını doğrula.

    Returns:
        dict: {
            is_valid: bool (deliverable veya accept_all),
            status: str (deliverable/accept_all/undeliverable/risky/unknown),
            score: int
        }
    """
    if not api_key or not email:
        return {"is_valid": False, "status": "no_api_key", "score": 0}

    print(f"  🔍 Hunter.io Verify: {email}...")
    endpoint = "https://api.hunter.io/v2/email-verifier"
    params = {
        "email": email,
        "api_key": api_key,
    }

    try:
        resp = requests.get(endpoint, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            status = data.get("status", "unknown")
            result = data.get("result", "unknown")
            score = data.get("score", 0)

            # "deliverable" veya "accept_all" → geçerli kabul et
            is_valid = result in ("deliverable", "accept_all")

            if is_valid:
                print(f"  ✅ Verify: {email} → {result} (score: {score})")
            else:
                print(f"  ❌ Verify: {email} → {result} (score: {score}) — REDDEDİLDİ")

            return {"is_valid": is_valid, "status": result, "score": score}
        elif resp.status_code == 429:
            print("  ⚠️ Hunter.io verify rate limit — emaili güvenli kabul ediyoruz")
            # Rate limit durumunda emaili kabul etmiyoruz — güvenli tarafta kal
            return {"is_valid": False, "status": "rate_limited", "score": 0}
    except Exception as e:
        print(f"  ❌ Hunter.io Verify hatası: {e}")

    return {"is_valid": False, "status": "error", "score": 0}


# ═══════════════════════════════════════════════════════════
# ANA FONKSİYON: Marka için iletişim bilgisi topla
# ═══════════════════════════════════════════════════════════

def find_contacts_for_brand(brand_info):
    """
    Tek bir marka için iletişim bilgisi toplar.

    Yeni akış:
    1. Apollo.io → Doğru kişiyi bul (isim + pozisyon)
    2. Hunter.io Email Finder → O kişinin emailini bul
    3. Hunter.io Domain Search → Fallback: domain genelinde ara
    4. Hunter.io Email Verify → Bulunan emaili doğrula
    5. Doğrulanamayan → best_email boş bırakılır

    Args:
        brand_info: dict with keys: instagram_handle, marka_adi, website (optional)

    Returns:
        dict: {website, best_email, email_contact_name, email_contact_title,
               email_status, email_source, personal_emails}
    """
    handle = brand_info.get("instagram_handle", "")
    brand_name = brand_info.get("marka_adi", handle)
    website = brand_info.get("website", "")

    print(f"\n📧 İletişim aranıyor: {brand_name} (@{handle})")

    # ─── Web sitesini bul/doğrula ───
    if not website:
        website = guess_website_from_handle(handle)
        if website:
            print(f"  🌐 Web sitesi tahmin edildi: {website}")
        else:
            print(f"  ⚠️ Web sitesi bulunamadı")

    domain = get_domain_from_url(website)
    if not domain:
        print(f"  ❌ Domain çıkarılamadı — iletişim araması atlanıyor")
        return _empty_result(website="")

    # ─── API anahtarları ───
    hunter_key = _get_env("HUNTER_API_KEY", ["Hunter.io", "API Anahtarı"])
    apollo_key = _get_env("APOLLO_API_KEY", ["Apollo.io", "API Anahtarı"])

    best_email = None
    contact_name = ""
    contact_title = ""
    email_source = ""
    personal_emails = []

    # ═══ ADIM 1: Apollo.io → Doğru kişiyi bul ═══
    apollo_people = search_apollo_people(domain, apollo_key)

    # ═══ ADIM 2: Hunter.io Email Finder (Apollo kişisi varsa) ═══
    if apollo_people:
        for person in apollo_people:
            # Apollo zaten email verdi mi?
            if person.get("email"):
                best_email = person["email"]
                contact_name = f"{person['first_name']} {person['last_name']}".strip()
                contact_title = person.get("title", "")
                email_source = "apollo_direct"
                print(f"  ✅ Apollo direkt email: {best_email}")
                break

            # Hunter Email Finder ile kişinin emailini bul
            found_email = find_email_by_name(
                domain,
                person["first_name"],
                person["last_name"],
                hunter_key,
            )
            if found_email:
                best_email = found_email
                contact_name = f"{person['first_name']} {person['last_name']}".strip()
                contact_title = person.get("title", "")
                email_source = "hunter_finder"
                break

            time.sleep(0.5)  # Rate limiting

    # ═══ ADIM 3: Hunter.io Domain Search (Fallback) ═══
    if not best_email:
        hunter_personal, hunter_general = search_hunter_domain(domain, hunter_key)
        personal_emails = hunter_personal

        if hunter_personal:
            # Kişisel emaillerden en uygununu seç (marketing/partnership tercihi)
            selected = _select_best_personal(hunter_personal)
            best_email = selected["email"]
            contact_name = selected.get("name", "")
            contact_title = selected.get("position", "")
            email_source = "hunter_domain_personal"
        elif hunter_general:
            # Genel emailleri marketing ile ilişkili olanlara öncelik ver
            best_email = _select_best_general(hunter_general)
            email_source = "hunter_domain_general"

    # ═══ ADIM 4: Email Verification ═══
    if best_email:
        verification = verify_email(best_email, hunter_key)

        if verification["is_valid"]:
            email_status = "verified"
            print(f"  ✅ Doğrulanmış email: {best_email}")
        else:
            print(f"  ⛔ Email doğrulanamadı: {best_email} → {verification['status']}")
            print(f"     → Bu markaya email GÖNDERİLMEYECEK")
            email_status = f"failed_verification:{verification['status']}"
            best_email = ""  # Email gönderme!
            contact_name = ""
            contact_title = ""
    else:
        email_status = "not_found"
        print(f"  ⛔ Email bulunamadı — bu markaya email GÖNDERİLMEYECEK")

    # ─── Sonuç ───
    result = {
        "website": website,
        "best_email": best_email,
        "email_contact_name": contact_name,
        "email_contact_title": contact_title,
        "email_status": email_status,
        "email_source": email_source,
        "personal_emails": personal_emails,
    }

    if best_email:
        print(f"  ✅ Sonuç: {best_email} ({contact_name}, {contact_title})")
    else:
        print(f"  ⚠️ Sonuç: Email yok — marka CSV'ye 'not_found' olarak kaydedilecek")

    return result


def _empty_result(website=""):
    """Boş sonuç döndürür."""
    return {
        "website": website,
        "best_email": "",
        "email_contact_name": "",
        "email_contact_title": "",
        "email_status": "not_found",
        "email_source": "",
        "personal_emails": [],
    }


def _select_best_personal(personal_emails):
    """
    Kişisel emailler arasından en uygununu seç.
    Marketing/partnerships/brand/influencer pozisyonlarını tercih et.
    """
    priority_keywords = [
        "influencer", "partnership", "marketing", "brand",
        "growth", "creator", "content", "collab",
    ]

    for person in personal_emails:
        pos = (person.get("position") or "").lower()
        for kw in priority_keywords:
            if kw in pos:
                return person

    # Hiçbiri eşleşmezse ilkini döndür
    return personal_emails[0]


def _select_best_general(general_emails):
    """
    Genel emailler arasından en uygununu seç.
    partnerships@ > business@ > hello@ > contact@ > info@ sıralaması.
    """
    # Tercih sırası — partnerships/business en iyi
    priority_prefixes = [
        "partnerships@", "partner@", "business@", "marketing@",
        "collab@", "influencer@", "creators@",
        "hello@", "contact@", "info@",
    ]

    for prefix in priority_prefixes:
        for email in general_emails:
            if email.lower().startswith(prefix):
                return email

    # Hiçbiri eşleşmezse ilkini döndür
    return general_emails[0]


# ═══════════════════════════════════════════════════════════
# BATCH İŞLEM
# ═══════════════════════════════════════════════════════════

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

    # İstatistikler
    verified = sum(1 for b in enriched if b.get("email_status") == "verified")
    not_found = sum(1 for b in enriched if b.get("email_status") == "not_found")
    failed = sum(1 for b in enriched if (b.get("email_status") or "").startswith("failed"))

    print(f"\n{'='*60}")
    print(f"📊 İLETİŞİM SONUÇ RAPORU")
    print(f"   ✅ Doğrulanmış: {verified}/{len(enriched)}")
    print(f"   ⛔ Bulunamayan: {not_found}/{len(enriched)}")
    print(f"   ❌ Doğrulama başarısız: {failed}/{len(enriched)}")
    print(f"{'='*60}")

    return enriched


if __name__ == "__main__":
    # Test: tek marka
    test = find_contacts_for_brand({
        "instagram_handle": "test_ai",
        "marka_adi": "Test AI",
    })
    print(json.dumps(test, indent=2, ensure_ascii=False))

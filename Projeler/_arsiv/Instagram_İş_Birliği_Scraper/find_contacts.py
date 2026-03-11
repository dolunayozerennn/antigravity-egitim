#!/usr/bin/env python3
"""
Tespit edilen AI markalarının iletişim bilgilerini toplar ve
Outreach_Listesi.csv oluşturur.

Ayrıca her marka için kişiselleştirilmiş outreach metinleri üretir.
"""

import csv
import json
import sys
import requests
from urllib.parse import urlparse

# ── API KEYS (Hunter.io & Apollo.io) ────────────────────────────────────────
HUNTER_API_KEY = "e547690085351aeca4ba177d8fadc81797b0018f"
APOLLO_API_KEY = "_IKHzcP1wFhwhFTzF34v1A"

INPUT_PATH = "data/ai_brands.json"
OUTPUT_CSV = "Outreach_Listesi.csv"
OUTPUT_MESSAGES = "data/outreach_messages.json"

# ── FALSE POSITIVE FİLTRESİ ─────────────────────────────────────────────────
# Bunlar AI markası değil — kişiler, medya hesapları vs.
FALSE_POSITIVES = {
    "ibrahimselim", "birceakalay", "duygubaloglut",
    "sedaincekilagoz", "gaminggentr", "nvidiageforcetr",
    "hepsiburada", "iamozdesign", "raw.dijital",  # Ajans, marka değil
    "igquinteroch/alan-turings-computing-machinery-and-intelligence-foundations-of-ai-and-its-modern-relevance-797756081e79",  # URL hata
    "aysevain", "burakcakir.ai",  # Kişisel profiller
    "archivinciai",  # Kişisel profil
}

# ── Büyük şirketler — outreach için uygun değil (Google, Meta vs.) ────────
SKIP_BIG_COMPANIES = {
    "googleturkiye", "googlegemini", "meta.ai", "samsungturkiye",
}


# ── Marka bilgi veritabanı (web araştırması sonuçları) ─────────────────────
# Bu veritabanı, markaların web araştırması sonuçlarını içerir.
BRAND_INFO = {
    "yandex__turkiye": {
        "brand_name": "Yandex",
        "website": "https://yandex.com.tr",
        "general_email": "info@yandex.com.tr",
        "description": "Arama motoru ve yapay zeka teknolojileri",
        "is_target": False,  # Çok büyük şirket
        "skip_reason": "Büyük şirket — doğrudan iş birliği zor",
    },
    "syntx_global": {
        "brand_name": "Syntx",
        "website": "https://syntx.ai",
        "general_email": "info@syntx.ai",
        "description": "AI destekli dijital pazarlama ve içerik platformu",
        "is_target": True,
    },
    "syntx_ai": {
        "brand_name": "Syntx",
        "website": "https://syntx.ai",
        "general_email": "info@syntx.ai",
        "description": "AI destekli dijital pazarlama ve içerik platformu",
        "is_target": True,
        "duplicate_of": "syntx_global",
    },
    "itspollo.ai": {
        "brand_name": "Pollo AI",
        "website": "https://pollo.ai",
        "general_email": "creator@pollo.ai",
        "description": "AI motion graphics ve animasyon aracı",
        "is_target": True,
    },
    "hailuoai_official": {
        "brand_name": "Hailuo AI (MiniMax)",
        "website": "https://hailuoai.video",
        "general_email": "info@hailuoaiminimax.com",
        "description": "AI video üretim aracı",
        "is_target": True,
    },
    "genspark_ai": {
        "brand_name": "Genspark",
        "website": "https://www.genspark.ai",
        "general_email": "hello@genspark.ai",
        "description": "AI arama motoru ve araştırma asistanı",
        "is_target": True,
    },
    "learna.ai": {
        "brand_name": "Learna AI",
        "website": "https://learna.ai",
        "general_email": "info@learna.ai",
        "description": "AI eğitim ve öğrenme platformu",
        "is_target": True,
    },
    "lovart.ai": {
        "brand_name": "Lovart AI",
        "website": "https://lovart.ai",
        "general_email": "support@lovart.ai",
        "description": "AI grafik tasarım aracı",
        "is_target": True,
    },
    "aicatchapp": {
        "brand_name": "AICatch",
        "website": "https://aicatch.app",
        "general_email": "info@aicatch.app",
        "description": "AI içerik tespit ve analiz aracı",
        "is_target": True,
    },
    "aicatch_us": {
        "brand_name": "AICatch",
        "website": "https://aicatch.app",
        "general_email": "info@aicatch.app",
        "description": "AI içerik tespit ve analiz aracı",
        "is_target": True,
        "duplicate_of": "aicatchapp",
    },
    "aicatch_eu": {
        "brand_name": "AICatch",
        "website": "https://aicatch.app",
        "general_email": "info@aicatch.app",
        "description": "AI içerik tespit ve analiz aracı",
        "is_target": True,
        "duplicate_of": "aicatchapp",
    },
    "repl.it": {
        "brand_name": "Replit",
        "website": "https://replit.com",
        "general_email": "partnerships@replit.com",
        "description": "AI destekli kodlama platformu",
        "is_target": True,
    },
    "napkin_ai": {
        "brand_name": "Napkin AI",
        "website": "https://www.napkin.ai",
        "general_email": "hello@napkin.ai",
        "description": "Yazıyı görsele dönüştüren AI aracı",
        "is_target": True,
    },
    "kimiai.official": {
        "brand_name": "Kimi AI (Moonshot AI)",
        "website": "https://kimi.ai",
        "general_email": "contact@moonshot.cn",
        "description": "AI asistan ve sohbet platformu",
        "is_target": True,
    },
    "vmeg.ai": {
        "brand_name": "Vmeg AI",
        "website": "https://vmeg.ai",
        "general_email": "support@vmeg.ai",
        "description": "AI video düzenleme aracı",
        "is_target": True,
    },
    "higgsfield.ai": {
        "brand_name": "Higgsfield AI",
        "website": "https://higgsfield.ai",
        "general_email": "hello@higgsfield.ai",
        "description": "AI video üretim aracı",
        "is_target": True,
    },
    "meshy.ai": {
        "brand_name": "Meshy AI",
        "website": "https://www.meshy.ai",
        "general_email": "hello@meshy.ai",
        "description": "3D model üretim AI aracı",
        "is_target": True,
    },
    "verdent__ai": {
        "brand_name": "Verdent AI",
        "website": "https://verdent.ai",
        "general_email": "hello@verdent.ai",
        "description": "AI web sitesi oluşturma aracı",
        "is_target": True,
    },
    "abacus.ai": {
        "brand_name": "Abacus AI",
        "website": "https://abacus.ai",
        "general_email": "info@abacus.ai",
        "description": "AI uygulama geliştirme platformu",
        "is_target": True,
    },
    "mozartaiofficial": {
        "brand_name": "Mozart AI",
        "website": "https://mozart.ai",
        "general_email": "hello@mozart.ai",
        "description": "AI müzik üretim aracı",
        "is_target": True,
    },
    "pulseboostai": {
        "brand_name": "PulseBoost AI",
        "website": "https://pulseboost.ai",
        "general_email": "info@pulseboost.ai",
        "description": "AI pazarlama ve büyüme aracı",
        "is_target": True,
    },
    "creatiai.official": {
        "brand_name": "Creati AI",
        "website": "https://creati.ai",
        "general_email": "hello@creati.ai",
        "description": "AI içerik üretim aracı",
        "is_target": True,
    },
    "klingai_official": {
        "brand_name": "Kling AI (Kuaishou)",
        "website": "https://klingai.com",
        "general_email": "business@kuaishou.com",
        "description": "AI video üretim aracı",
        "is_target": True,
    },
    "promake.ai": {
        "brand_name": "Promake AI",
        "website": "https://promake.ai",
        "general_email": "hello@promake.ai",
        "description": "AI ile profesyonel içerik ve ürün fotoğrafı üretimi",
        "is_target": True,
    },
    "manusaiofficial": {
        "brand_name": "Manus AI",
        "website": "https://manus.im",
        "general_email": "hello@manus.im",
        "description": "Genel amaçlı AI asistanı",
        "is_target": True,
    },
    "weavy_ai": {
        "brand_name": "Weavy AI",
        "website": "https://weavy.ai",
        "general_email": "hello@weavy.ai",
        "description": "AI araç ve iş akışı platformu",
        "is_target": True,
    },
    "echtaworld": {
        "brand_name": "Echta World",
        "website": "https://echta.world",
        "general_email": "info@echta.world",
        "description": "AI metaverse / dijital dünya platformu",
        "is_target": True,
    },
    "medeo.ai": {
        "brand_name": "Medeo AI",
        "website": "https://medeo.ai",
        "general_email": "hello@medeo.ai",
        "description": "AI video üretim aracı",
        "is_target": True,
    },
}

# ── DM / Email şablonları ────────────────────────────────────────────────────

DM_TEMPLATE = """Sorry, I got 19M views, but it's not {brand_name} 😢

Hi {brand_name} team,

I'm Dolunay, a content creator focused on AI, tech, and digital tools. My content has reached 100M+ organic views in Turkey.

My profiles:
Instagram: https://www.instagram.com/dolunay_ozeren/
TikTok: https://www.tiktok.com/@dolunayozeren
YouTube: https://www.youtube.com/@dolunayozeren/

Recent collabs include Pixelcut, Nim AI, Aithor, TopView, Creatify, Lexi AI, ArtFlow, Temu, and Printify.

A few results:
Pixelcut: 19.7M views — https://www.instagram.com/reel/DAdt0tUN-j9/

Nim AI: 4M views — https://www.instagram.com/reel/DKtuJ3cK-Yr/

Aithor: 2M views — https://www.instagram.com/reel/DKHLswaK4Tj/

I have a viral campaign idea that could make {brand_name} stand out. If you're open to it, just reply and I'll send the concept.

Best,
Dolunay"""


GENERAL_EMAIL_SUBJECT = "Sorry — I got 100M views, but it's not {brand_name} 😢"

GENERAL_EMAIL_BODY = """Hi {brand_name} team,

I'm reaching out via your general contact email, and I'd really appreciate it if you could forward this to the right person (Influencer Marketing / Partnerships / Growth / PR) or share the best collaboration contact.

I'm Dolunay, a content creator focused on AI, tech, and digital tools. My videos have reached over 100 million organic views in Turkey.

My profiles:
- Instagram: https://www.instagram.com/dolunay_ozeren/
- TikTok: https://www.tiktok.com/@dolunayozeren
- YouTube: https://www.youtube.com/@dolunayozeren

I've collaborated with brands like Pixelcut, Nim AI, Aithor, TopView, Creatify, Lexi AI, ArtFlow, Temu, and Printify.

A few examples:
- 19.7M views with Pixelcut: https://www.instagram.com/reel/DAdt0tUN-j9/
- 4M views with Nim AI: https://www.instagram.com/reel/DKtuJ3cK-Yr/
- 2M views with Aithor: https://www.instagram.com/reel/DKHLswaK4Tj/

I have a viral campaign idea that could make {brand_name} stand out 🚀

If you're interested, just reply to this email and I'll share the details.

Best,
Dolunay"""


def load_existing_brands():
    """Halihazırda çalışılan markaları calisan_markalar.json'dan yükler."""
    import os
    path = "calisan_markalar.json"
    if not os.path.exists(path):
        return set(), set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Handle bazlı set
    handles = set(h.lower() for h in data.get("instagram_handles_to_exclude", []))
    # İsim bazlı set (fuzzy matching için küçük harfe çevir)
    names = set(n.lower().strip() for n in data.get("brands", []))
    return handles, names



# ── Email Finder Helper Functions ──────────────────────────────────────────

def get_domain_from_url(url: str) -> str:
    """URL'den domaini çıkarır (örn. https://www.napkin.ai -> napkin.ai)."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def search_hunter_emails(domain: str) -> list[str]:
    """Hunter.io API ile domainden email arar."""
    print(f"  🔍 Hunter.io taranıyor: {domain}...")
    endpoint = "https://api.hunter.io/v2/domain-search"
    params = {
        "domain": domain,
        "api_key": HUNTER_API_KEY,
        # "department": "marketing, executive",  <-- Kaldırdım, herkesi arasın
        "limit": 10,
    }
    
    try:
        resp = requests.get(endpoint, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            print(f"    ↳ Hunter: {len(emails)} email bulundu.")  # Debug print eklendi
            
            # Kişisel emailleri filtrele (generic olmayanlar)
            personal_emails = []
            for e in emails:
                if e.get("type") == "personal":
                    personal_emails.append(f"{e['value']} ({e['first_name']} {e['last_name']} - {e['position']})")
            
            if personal_emails:
                return personal_emails
            
            # Eğer hiç personal yoksa, generic'leri de döndürebiliriz (opsiyonel)
            # Amaç kişisel bulmak olduğu için şimdilik boş dönelim, Apollo'ya şans verelim.
            return []

        elif resp.status_code == 429:
             print("  ⚠️ Hunter.io limit aşıldı.")
        elif resp.status_code == 401:
             print("  ⚠️ Hunter.io API Key geçersiz.")
    except Exception as e:
        print(f"  ❌ Hunter.io hatası: {e}")
    
    return []


def search_apollo_emails(domain: str) -> list[str]:
    """Apollo.io API ile domainden email arar (Fallback)."""
    print(f"  🔍 Apollo.io taranıyor: {domain}...")
    endpoint = "https://api.apollo.io/v1/people/search"  # Endpoint değiştirildi
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    payload = {
        "q_organization_domains": domain, # String olarak gönderilebilir, docs öyle diyor
        "page": 1,
        "per_page": 5,
        "person_titles": ["marketing", "growth", "influencer", "founder", "ceo", "partnerships", "brand"],
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            people = data.get("people", [])
            personal_emails = []
            for p in people:
                email = p.get("email")
                if email:
                    fname = p.get("first_name", "")
                    lname = p.get("last_name", "")
                    title = p.get("title", "")
                    personal_emails.append(f"{email} ({fname} {lname} - {title})")
            print(f"    ↳ Apollo: {len(personal_emails)} email bulundu.")
            return personal_emails
        elif resp.status_code == 429:
             print("  ⚠️ Apollo.io limit aşıldı.")
        else:
             print(f"  ⚠️ Apollo hatası: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"  ❌ Apollo.io hatası: {e}")

    return []


def find_personal_emails(domain: str) -> list[str]:
    """Sırayla Hunter ve Apollo kullanarak kişisel email arar."""
    if not domain:
        return []
    
    # 1. Hunter.io dene
    emails = search_hunter_emails(domain)
    if emails:
        return emails
    
    # 2. Apollo.io dene (Hunter bulamazsa)
    print("  bitmeye yakın veya limit yok -> Apollo devreye giriyor...") # Debug
    emails = search_apollo_emails(domain)
    return emails

    return emails


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Halihazırda çalışılan markaları yükle
    existing_handles, existing_names = load_existing_brands()
    print(f"[INFO] {len(existing_names)} mevcut marka hariç tutulacak.")

    # İş birliği yapılan ve diğer AI markaları birleştir
    all_ai = {}
    all_ai.update(data.get("ai_brands_collab", {}))
    all_ai.update(data.get("ai_brands_other", {}))

    # CSV satırları
    rows = []
    messages = {}
    duplicates_seen = set()  # handle bazlı
    brand_names_seen = set()  # isim bazlı duplicate kontrolü
    skipped_existing = []

    for handle, brand_data in all_ai.items():
        # False positive filtresi
        if handle in FALSE_POSITIVES:
            continue
        # Büyük şirket filtresi
        if handle in SKIP_BIG_COMPANIES:
            continue

        info = BRAND_INFO.get(handle, {})
        brand_name = info.get("brand_name", handle)

        # Halihazırda çalışılan marka filtresi
        if handle.lower() in existing_handles:
            skipped_existing.append(f"@{handle} ({brand_name})")
            continue
        # İsim bazlı kontrol (fuzzy)
        name_lower = brand_name.lower().strip()
        if any(existing in name_lower or name_lower in existing for existing in existing_names if len(existing) > 2):
            skipped_existing.append(f"@{handle} ({brand_name})")
            continue

        # Duplicate kontrolü (handle)
        dup_of = info.get("duplicate_of")
        if dup_of:
            if dup_of in duplicates_seen:
                continue
        duplicates_seen.add(handle)

        # Duplicate kontrolü (brand_name)
        if brand_name.lower() in brand_names_seen:
            continue
        brand_names_seen.add(brand_name.lower())

        website = info.get("website", "")
        general_email = info.get("general_email", "")
        description = info.get("description", "")
        is_target = info.get("is_target", True)
        skip_reason = info.get("skip_reason", "")

        if not is_target:
            continue

        instagram_url = f"https://www.instagram.com/{handle}/"
        mention_count = brand_data.get("mention_count", 0)
        has_collab = brand_data.get("has_collab_marker", False)
        source_profiles = list(set(s["profil"] for s in brand_data.get("sources", [])))
        
        # Kişisel Email Bulma (Hunter -> Apollo)
        domain = get_domain_from_url(website)
        personal_emails = find_personal_emails(domain)
        personal_email_str = ", ".join(personal_emails)
        
        # En iyi iletişim adresi (Kişisel varsa onu kullan, yoksa genel)
        # Birden fazla kişisel varsa ilkini al
        best_email = personal_emails[0].split()[0] if personal_emails else general_email

        rows.append({
            "Marka Adı": brand_name,
            "Instagram Handle": f"@{handle}",
            "Instagram URL": instagram_url,
            "Website": website,
            "Genel Email": general_email,
            "Kişisel Email": personal_email_str,
            "Açıklama": description,
            "Mention Sayısı": mention_count,
            "İş Birliği Belirteci": "Evet" if has_collab else "Hayır",
            "Kaynak Profiller": ", ".join(source_profiles),
        })

        # Kişiselleştirilmiş mesajlar
        messages[handle] = {
            "brand_name": brand_name,
            "instagram_url": instagram_url,
            "dm_message": DM_TEMPLATE.format(brand_name=brand_name),
            "email_subject": GENERAL_EMAIL_SUBJECT.format(brand_name=brand_name),
            "email_body": GENERAL_EMAIL_BODY.format(brand_name=brand_name),
            "general_email": best_email, # En iyi emaili kullan
        }

    # Mention sayısına göre sırala
    rows.sort(key=lambda x: -x["Mention Sayısı"])

    # CSV yaz
    fieldnames = [
        "Marka Adı", "Instagram Handle", "Instagram URL",
        "Website", "Genel Email", "Kişisel Email", "Açıklama",
        "Mention Sayısı", "İş Birliği Belirteci", "Kaynak Profiller",
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[INFO] ✅ Outreach listesi kaydedildi → {OUTPUT_CSV} ({len(rows)} marka)")

    # Mesajları kaydet
    with open(OUTPUT_MESSAGES, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    print(f"[INFO] ✅ Outreach mesajları kaydedildi → {OUTPUT_MESSAGES}")

    # Özet
    print(f"\n{'='*60}")
    print(f"📋 OUTREACH LİSTESİ")
    print(f"{'='*60}")
    for i, row in enumerate(rows, 1):
        collab_icon = "🤝" if row["İş Birliği Belirteci"] == "Evet" else "🤖"
        print(f"  {i:2d}. {collab_icon} {row['Marka Adı']:20s} | @{row['Instagram Handle']:20s} | {row['Genel Email']}")
    print(f"{'='*60}")
    print(f"  Toplam hedef marka: {len(rows)}")

    if skipped_existing:
        print(f"\n⚠️  HARIÇ TUTULAN (halihazırda çalışılan) markalar:")
        for s in skipped_existing:
            print(f"    ↳ {s}")


if __name__ == "__main__":
    main()

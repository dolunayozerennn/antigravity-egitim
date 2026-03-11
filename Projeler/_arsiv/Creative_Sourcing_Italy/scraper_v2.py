import requests
import time
import json
import re
import csv

API_KEY = os.environ.get("APIFY_API_KEY", "")

# Fan page / business page filtreleme kelimeleri
BLACKLIST_BIO_KEYWORDS = [
    "fan page", "fanpage", "fan_page", "unofficial", "non ufficiale",
    "pagina fan", "pagina di", "meme", "funny page", "best of",
    "profilo ufficiale", "edizioni", "associazione", "s.r.l", "srl",
    "agenzia", "brand", "shop", "store", "negozio", "azienda",
    "compilation", "raccolta", "repost", "daily", "best moments"
]

def run_apify(actor_id, payload, max_poll=600):
    actor_id = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    print(f"🚀 Başlatılıyor: {actor_id}")
    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]
        print(f"✅ Run ID: {run_id}")
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

    start = time.time()
    while True:
        try:
            s = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=headers).json()["data"]
            if s["status"] == "SUCCEEDED":
                ds = s["defaultDatasetId"]
                print(f"✅ Tamamlandı! Dataset: {ds}")
                return requests.get(f"https://api.apify.com/v2/datasets/{ds}/items", headers=headers).json()
            elif s["status"] in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"❌ Durum: {s['status']}")
                return None
        except:
            pass
        if time.time() - start > max_poll:
            print("❌ Zaman aşımı!")
            return None
        time.sleep(10)

def extract_email(text):
    if not text:
        return None
    emails = re.findall(r'[\w\.\-\+]+@[\w\.\-]+\.\w+', text)
    # Filter out common non-personal emails
    for e in emails:
        if not any(x in e.lower() for x in ["example.com", "email.com", "test.com"]):
            return e
    return None

def is_personal_account(bio, username, full_name):
    """Fan page, meme page, business page DEĞİL gerçek kişi mi?"""
    if not bio:
        return True  # Bio yoksa geç, sonra email ile filtreleyeceğiz
    bio_lower = bio.lower()
    for keyword in BLACKLIST_BIO_KEYWORDS:
        if keyword in bio_lower:
            return False
    # Kullanıcı adında "page", "daily", "best", "memes" vs varsa reddet
    username_lower = (username or "").lower()
    bad_username = ["page", "daily", "best", "memes", "funny", "compilation", "fanpage", "fan_"]
    for b in bad_username:
        if b in username_lower:
            return False
    return True

def extract_website(bio, external_url):
    """Bio'dan veya external_url'den website linki çıkar"""
    if external_url:
        return external_url
    if not bio:
        return None
    url_match = re.search(r'https?://[\w\.\-/]+', bio)
    return url_match.group(0) if url_match else None

# ============ TIKTOK ARAMA ============
def search_tiktok():
    print("\n" + "="*50)
    print("📱 TIKTOK ARAMA BAŞLIYOR")
    print("="*50)
    
    all_results = []
    search_queries = [
        "italian comedian",
        "comico italiano",
        "attore comico italia",
        "sketch comedy italia",
        "skit italiano",
        "comedian italy",
        "comedy creator italy"
    ]
    
    for query in search_queries:
        print(f"\n🔍 TikTok arama: '{query}'")
        payload = {
            "searchQuery": query,
            "maxProfiles": 50,
            "resultsPerPage": 30
        }
        results = run_apify("clockworks/tiktok-user-search-scraper", payload)
        if results:
            all_results.extend(results)
        time.sleep(2)  # Rate limit
    
    # Deduplicate by username
    seen = set()
    unique = []
    for item in all_results:
        name = item.get("name", "")
        if name and name not in seen:
            seen.add(name)
            unique.append(item)
    
    print(f"\n📊 TikTok toplam unique profil: {len(unique)}")
    
    # Filter: 10k-300k followers + personal account
    filtered = []
    for item in unique:
        fans = item.get("fans", 0)
        if 10000 <= fans <= 300000:
            bio = item.get("signature", "")
            nickname = item.get("nickName", "")
            username = item.get("name", "")
            
            if is_personal_account(bio, username, nickname):
                email = extract_email(bio)
                website = item.get("bioLink", None)
                if isinstance(website, dict):
                    website = website.get("link", None)
                
                filtered.append({
                    "username": username,
                    "nickname": nickname,
                    "platform": "TikTok",
                    "followers": fans,
                    "bio": bio,
                    "email": email,
                    "website": website,
                    "profile_url": item.get("profileUrl", f"https://www.tiktok.com/@{username}")
                })
    
    print(f"✅ TikTok filtreli (10k-300k, kişisel): {len(filtered)}")
    return filtered

# ============ INSTAGRAM ARAMA ============
def search_instagram():
    print("\n" + "="*50)
    print("📸 INSTAGRAM ARAMA BAŞLIYOR")
    print("="*50)
    
    # Adım 1: Hashtag araması ile kullanıcı adları topla
    hashtags = [
        "comediante", "comicoitaliano", "attorecomico", 
        "comedyitalia", "sketchitalia", "comedianitaliano",
        "humoristitaliano", "standupitalia", "comicoitalianoo"
    ]
    
    all_usernames = set()
    
    for tag in hashtags:
        print(f"\n🔍 Instagram hashtag: #{tag}")
        payload = {"hashtags": [tag], "resultsLimit": 50}
        results = run_apify("apify/instagram-hashtag-scraper", payload)
        if results:
            for item in results:
                owner = item.get("ownerUsername")
                if owner and "error" not in item:
                    all_usernames.add(owner)
        time.sleep(2)
    
    print(f"\n📊 Instagram toplam unique kullanıcı: {len(all_usernames)}")
    
    if not all_usernames:
        return []
    
    # Adım 2: Profilleri çek (50'şerli batch'ler halinde)
    username_list = list(all_usernames)
    all_profiles = []
    
    for i in range(0, len(username_list), 30):
        batch = username_list[i:i+30]
        print(f"\n📋 Instagram profil batch {i//30 + 1}: {len(batch)} profil çekiliyor...")
        payload = {"usernames": batch}
        results = run_apify("apify/instagram-profile-scraper", payload)
        if results:
            all_profiles.extend(results)
        time.sleep(2)
    
    # Adım 3: Filtrele
    filtered = []
    for prof in all_profiles:
        if "error" in prof:
            continue
        
        followers = prof.get("followersCount", 0)
        if not (10000 <= followers <= 300000):
            continue
        
        bio = prof.get("biography", "")
        username = prof.get("username", "")
        full_name = prof.get("fullName", "")
        
        # İşletme hesabı mı?
        is_business = prof.get("isBusinessAccount", False)
        
        if not is_personal_account(bio, username, full_name):
            continue
        
        email = extract_email(bio) or prof.get("businessEmail")
        website = prof.get("externalUrl") or prof.get("externalLynkUrl")
        
        filtered.append({
            "username": username,
            "nickname": full_name,
            "platform": "Instagram",
            "followers": followers,
            "bio": bio,
            "email": email,
            "website": website,
            "profile_url": prof.get("url", f"https://www.instagram.com/{username}/")
        })
    
    print(f"✅ Instagram filtreli (10k-300k, kişisel): {len(filtered)}")
    return filtered

# ============ WEBSITE ENRICHMENT ============
def enrich_with_contact_scraper(influencers):
    """Website linki olup email'i olmayanları contact-info-scraper ile zenginleştir"""
    to_enrich = [inf for inf in influencers if inf["website"] and not inf["email"]]
    
    if not to_enrich:
        print("\n⏭️ Zenginleştirilecek profil yok (hepsinin ya emaili var ya da website'i yok)")
        return influencers
    
    print(f"\n🔍 {len(to_enrich)} profil website üzerinden zenginleştiriliyor...")
    
    urls = [inf["website"] for inf in to_enrich]
    payload = {"startUrls": [{"url": u} for u in urls[:20]]  # Max 20
    }
    
    results = run_apify("vdrmota/contact-info-scraper", payload)
    
    if results:
        # URL -> email mapping oluştur
        url_email_map = {}
        for r in results:
            found_emails = r.get("emails", [])
            source_url = r.get("url", "")
            if found_emails:
                url_email_map[source_url] = found_emails[0]
        
        # Influencer listesini güncelle
        for inf in influencers:
            if not inf["email"] and inf["website"]:
                for url_key, email_val in url_email_map.items():
                    if inf["website"] in url_key or url_key in (inf["website"] or ""):
                        inf["email"] = email_val
                        print(f"  📧 {inf['username']}: {email_val}")
                        break
    
    return influencers

# ============ ANA İŞLEV ============
if __name__ == "__main__":
    # 1. TikTok ara
    tiktok_results = search_tiktok()
    
    # 2. Instagram ara
    instagram_results = search_instagram()
    
    # 3. Birleştir
    all_influencers = tiktok_results + instagram_results
    print(f"\n📊 Toplam (filtreli, kişisel): {len(all_influencers)}")
    
    # 4. Website enrichment
    all_influencers = enrich_with_contact_scraper(all_influencers)
    
    # 5. SADECE EMAIL'İ OLANLARI AL
    with_email = [inf for inf in all_influencers if inf["email"]]
    without_email = [inf for inf in all_influencers if not inf["email"]]
    
    print(f"\n📧 Email'i olan: {len(with_email)}")
    print(f"🚫 Email'i olmayan (elenecek): {len(without_email)}")
    
    # 6. CSV'ye kaydet - sadece email'i olanlar
    csv_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/influencers_v2.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "nickname", "platform", "followers", "email", "website", "profile_url", "bio"])
        writer.writeheader()
        for inf in with_email:
            writer.writerow(inf)
    
    print(f"\n🎉 Sonuçlar kaydedildi: {csv_file}")
    print(f"📋 Toplam {len(with_email)} influencer (sadece email'i olanlar)")
    
    # Ayrıca tüm listeyi de JSON olarak kaydet (referans için)
    json_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/all_results_v2.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({"with_email": with_email, "without_email": without_email}, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Tüm sonuçlar (referans): {json_file}")

import requests
import time
import json
import re
import csv

API_KEY = os.environ.get("APIFY_API_KEY", "")

def run_apify(actor_id, payload, max_poll=600):
    actor_id = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    print(f"🚀 {actor_id}")
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 201:
        print(f"  ❌ HTTP {resp.status_code}: {resp.text[:200]}")
        return None
    run_id = resp.json()["data"]["id"]
    print(f"  Run ID: {run_id}")
    start = time.time()
    while True:
        s = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=headers).json()["data"]
        if s["status"] == "SUCCEEDED":
            ds = s["defaultDatasetId"]
            return requests.get(f"https://api.apify.com/v2/datasets/{ds}/items", headers=headers).json()
        elif s["status"] in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print(f"  ❌ {s['status']}")
            return None
        if time.time() - start > max_poll:
            return None
        time.sleep(8)

def extract_email(text):
    if not text:
        return None
    emails = re.findall(r'[\w\.\-\+]+@[\w\.\-]+\.\w{2,}', text)
    for e in emails:
        if not any(x in e.lower() for x in ["sentry", "example", "test", "facebook", "instagram",
                                              "cdninstagram", "fbcdn", "noreply", "privacy"]):
            return e
    return None

# Fan page / business page / non-creator filtreleme
BLACKLIST_BIO = [
    "fan page", "fanpage", "pagina fan", "non ufficiale", "unofficial",
    "meme", "funny page", "best of", "compilation", "repost",
    "s.r.l", "srl", "agenzia", "brand", "shop", "store", "negozio",
    "pallavolo", "volley", "serie a", "calcio", "football",
    "bigletteria", "biglietti", "edizioni", "associazione",
    "ristorante", "osteria", "bar ", "pizzeria", "trattoria",
    "news", "gossip", "notizie", "magazine", "rivista", "giornale",
    "makeup", "trucco", "beauty salon", "parrucchier",
    "corsi", "master class", "accademia", "scuola",
    "self-service", "online per eventi",
]

BLACKLIST_USERNAME = [
    "page", "daily", "best", "memes", "fan", "news", "magazine",
    "official_page", "club", "team", "events"
]

def is_personal_creator(bio, username):
    bio_lower = (bio or "").lower()
    username_lower = (username or "").lower()
    for kw in BLACKLIST_BIO:
        if kw in bio_lower:
            return False
    for kw in BLACKLIST_USERNAME:
        if kw in username_lower:
            return False
    return True

# ===== ADIM 1: DAHA GENİŞ HASHTAG TARAMASI =====
print("="*60)
print("📸 ADIM 1: GENİŞ HASHTAG TARAMASI")
print("="*60)

hashtags = [
    "comedyitalia", "comicoitaliano", "comicitaitaliana",
    "sketchcomedy", "skitcomedy", "viralitalia",
    "comedyvideo", "funnyvideo", "ridere",
    "tiktokitalia", "contentcreator", "creatoritaliano",
    "attorecomico", "standupcomedy", "humoritaliano",
    "videodivertenti", "parodia", "imitazione"
]

all_owners = set()

for tag in hashtags:
    print(f"\n🔍 #{tag}")
    results = run_apify("apify/instagram-hashtag-scraper", {
        "hashtags": [tag],
        "resultsLimit": 30
    })
    if results:
        for item in results:
            owner = item.get("ownerUsername")
            if owner and "error" not in item:
                all_owners.add(owner)
    time.sleep(1)

print(f"\n📊 Toplam unique kullanıcı: {len(all_owners)}")

# ===== ADIM 2: PROFİLLERİ ÇEK =====
print(f"\n{'='*60}")
print("📋 ADIM 2: PROFİL TARAMASI")
print(f"{'='*60}")

owner_list = list(all_owners)
all_profiles = []

for i in range(0, len(owner_list), 25):
    batch = owner_list[i:i+25]
    print(f"\nBatch {i//25+1}: {len(batch)} profil")
    results = run_apify("apify/instagram-profile-scraper", {"usernames": batch})
    if results:
        all_profiles.extend(results)
    time.sleep(1)

print(f"\n📊 Toplam profil çekildi: {len(all_profiles)}")

# ===== ADIM 3: FİLTRELE =====
print(f"\n{'='*60}")
print("🔧 ADIM 3: FİLTRELEME")
print(f"{'='*60}")

final_list = []
seen_emails = set()

for p in all_profiles:
    if "error" in p:
        continue
    
    followers = p.get("followersCount", 0)
    if not (10000 <= followers <= 300000):
        continue
    
    username = p.get("username", "")
    bio = p.get("biography", "")
    full_name = p.get("fullName", "")
    
    # Kişisel hesap mı?
    if not is_personal_creator(bio, username):
        print(f"  ❌ @{username} - kişisel değil (filtrelendi)")
        continue
    
    # Email bul
    email = extract_email(bio) or p.get("businessEmail")
    if not email:
        continue
    
    if email in seen_emails:
        continue
    seen_emails.add(email)
    
    ext_url = p.get("externalUrl", "")
    
    final_list.append({
        "Username": f"@{username}",
        "İsim": full_name,
        "Platform": "Instagram",
        "Takipçi": followers,
        "Email": email,
        "Website": ext_url or "",
        "Profil": f"https://www.instagram.com/{username}/",
        "Bio": bio.replace("\n", " | ")[:200]
    })
    print(f"  ✅ @{username} ({full_name}) | {followers:,} | 📧 {email}")

# Önceki sonuçları da ekle (duplicate email kontrolüyle)
prev_results = [
    {"Username": "@simonettamusitano", "İsim": "Simonetta Musitano", "Platform": "Instagram", "Takipçi": 40543,
     "Email": "simonetta.m@wontymedia.com", "Website": "https://www.altrascena.com/ticket-cerco-solo-divertimento/",
     "Profil": "https://www.instagram.com/simonettamusitano/",
     "Bio": "🦄 🏳️‍⚧️ Stand up comedy🎤 | Live show @altrascena_artmanagement | Digital: @wontymedia"},
    {"Username": "@andreasaleri_standup", "İsim": "Andrea Saleri", "Platform": "Instagram", "Takipçi": 26025,
     "Email": "andrea.saleri91@gmail.com", "Website": "https://linktr.ee/andreasaleri.standup",
     "Profil": "https://www.instagram.com/andreasaleri_standup/",
     "Bio": "📧 per info spettacoli/collaborazioni andrea.saleri91@gmail.com | 🤝 membro dei @potaboyzcomedy"},
    {"Username": "@queenbenedetto", "İsim": "Lorena Benedetto", "Platform": "Instagram", "Takipçi": 25719,
     "Email": "esti@lahuta.org", "Website": "https://www.lorenabenedetto.com/",
     "Profil": "https://www.instagram.com/queenbenedetto/",
     "Bio": "Queen Of Comedy Self-Proclaimed but accurate | Immigrant humor Savage honesty | manager: esti@lahuta.org"}
]

for prev in prev_results:
    if prev["Email"] not in seen_emails:
        final_list.append(prev)
        seen_emails.add(prev["Email"])

# Sırala
final_list.sort(key=lambda x: x["Takipçi"], reverse=True)

# CSV kaydet
csv_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/influencers_final.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Username", "İsim", "Platform", "Takipçi", "Email", "Website", "Profil", "Bio"])
    writer.writeheader()
    writer.writerows(final_list)

print(f"\n{'='*60}")
print(f"🎉 SONUÇ: {len(final_list)} influencer (gerçek kişi + email)")
print(f"📁 CSV: {csv_file}")
print(f"{'='*60}")
for r in final_list:
    print(f"  👤 {r['Username']} ({r['İsim']}) | {r['Takipçi']:,} | 📧 {r['Email']}")

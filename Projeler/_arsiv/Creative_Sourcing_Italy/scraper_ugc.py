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
        el = e.lower()
        if not any(x in el for x in ["sentry", "example", "test", "facebook", "instagram",
                                      "cdninstagram", "fbcdn", "noreply", "privacy", "support@",
                                      "redazione@", "info@wordpress"]):
            return e
    return None

# ===== PROFESYONEL SANATÇI FİLTRESİ =====
# Bunlar kendi kariyerleri olan insanlar — UGC deal'e gelmezler
ARTIST_KEYWORDS = [
    "stand-up", "stand up", "standup", "comedian", "comico", "comica",
    "attore", "attrice", "actor", "actress",
    "cantante", "singer", "musicista", "rapper", "dj ",
    "regista", "director", "scrittore", "scrittrice", "writer", "autore", "autrice",
    "teatro", "theatre", "theater", "spettacolo", "spettacoli", "tour ",
    "biglietti", "ticket", "comedy club", "live show",
    "sag award", "oscar", "golden globe", "film", "cinema",
    "conduttore", "conduttrice", "presenter", "tv host",
    "giornalista", "journalist",
]

# ===== BUSINESS / NON-CREATOR FİLTRESİ =====
BUSINESS_KEYWORDS = [
    "fan page", "fanpage", "pagina fan", "non ufficiale", "unofficial",
    "meme", "funny page", "best of", "compilation", "repost",
    "s.r.l", "srl", "agenzia", "brand", "shop", "store", "negozio",
    "pallavolo", "volley", "serie a", "calcio", "football",
    "ristorante", "osteria", "pizzeria", "trattoria", "bar ",
    "news", "gossip", "notizie", "magazine", "rivista", "giornale", "testata",
    "makeup", "trucco", "beauty salon", "parrucchier",
    "corsi", "master class", "accademia", "scuola",
    "ricette", "cucina", "cooking", "recipe", "chef",
    "fitness", "palestra", "gym", "personal trainer",
    "fotografo", "photographer", "videographer",
    "avvocato", "lawyer", "medico", "doctor", "psicologo",
    "immobiliare", "real estate",
    "azienda", "company", "impresa", "ditta",
    "associazione", "onlus", "no profit",
    "edizioni", "editore", "publishing",
    "lusso", "luxury", "rich", "wealth", "millionaire", "billionaire",
    "lifestyle", "glamour", "yacht", "travel blogger",
]

USERNAME_BLACKLIST = [
    "page", "daily", "best", "memes", "fan", "news", "magazine",
    "official_page", "club", "team", "events", "radio", "tv_",
    "_official", "media", "group", "agency", "luxury", "lusso",
]

# ===== İÇERİK ÜRETICI İŞARETLERİ =====
# Bunlar kişinin gerçek bir content creator olduğunu gösterir
CREATOR_SIGNALS = [
    "content creator", "creator", "ugc", "influencer",
    "collaborazioni", "collab", "collaborazione",
    "per info", "per collab", "business", "partnership",
    "digital creator", "video creator",
    "pov", "skit", "sketch",
    "tiktok", "reels", "youtube", "coppia", "vitadicoppia", "divertente"
]

def classify_profile(bio, username, full_name):
    """Profili sınıfla: 'creator', 'artist', 'business', 'unknown'"""
    bio_lower = (bio or "").lower()
    username_lower = (username or "").lower()
    
    # Business/page/luxury mi?
    for kw in BUSINESS_KEYWORDS:
        if kw in bio_lower:
            return "business", kw
    for kw in USERNAME_BLACKLIST:
        if kw in username_lower:
            return "business", f"username:{kw}"
    
    # Profesyonel sanatçı mı? (stand-up, aktör, şarkıcı vs.)
    for kw in ARTIST_KEYWORDS:
        if kw in bio_lower:
            return "artist", kw
    
    # Creator sinyalleri var mı?
    creator_score = 0
    for kw in CREATOR_SIGNALS:
        if kw in bio_lower:
            creator_score += 1
    
    if creator_score >= 1:
        return "creator", f"score={creator_score}"
    
    return "unknown", "no signal"

def evaluate_engagement(profile_data):
    """
    Kullanıcının latestPosts (eğer varsa) analizini yapar.
    Takipçiye oranla view ve like oranlarını çıkarır.
    """
    followers = profile_data.get("followersCount", 1)
    posts = profile_data.get("latestPosts", [])
    if not posts:
        return False, "no posts"
    
    views = []
    likes = []
    
    for post in posts:
        # get playCount veya viewCount for video/reels
        vc = post.get("videoPlayCount") or post.get("videoViewCount") or 0
        if vc > 0:
            views.append(vc)
        lc = post.get("likesCount", 0)
        likes.append(lc)
    
    med_views = sorted(views)[len(views)//2] if views else 0
    med_likes = sorted(likes)[len(likes)//2] if likes else 0
    
    # Minimal eşikler (%15+ organik izlenme oranı ve %0.8+ beğeni oranı)
    view_rate = med_views / followers if followers > 0 else 0
    like_rate = med_likes / followers if followers > 0 else 0
    
    # Hard limit view: > 5000 views medyan
    if view_rate < 0.15 or like_rate < 0.008 or med_views < 5000:
        return False, f"low engagement: vr={view_rate:.2f}, lr={like_rate:.2f}, mv={med_views}"
        
    return True, f"good metric: vr={view_rate:.2f}, mv={med_views}"

# ===== ADIM 1: HASHTAG TARAMASI =====
# Bu sefer gerçek UGC/skit creatorlarının kullandığı hashtag'lere odaklanıyoruz
print("="*60)
print("🇮🇹 İTALYAN YÜKSEK ETKİLEŞİMLİ UGC & KOMEDİ TARAMASI")
print("   (Stand-up/Aktör/Lüks HARİÇ, Reel Etkileşimi Yüksek)")
print("="*60)

hashtags = [
    # Yüksek etkileşimli niş komedi/coppia tagleri
    "coppiadivertente", "vitadicoppia", "ragazziitaliani",
    "fidanzatidivertenti", "amiciitaliani", "ragazzeitaliane",
    "ugccomedy", "vitadastudenti", "storiecoppia", "ridiamoinsieme",
    "ragazzechefacosescem", "cosemaledettamentedivertenti",
    "fidanzato", "fidanzata", "mammadisimone", "vitadamamma",
    "situazionimbarazzanti", "situazionicomiche", "povcoppia", "povstudenti",
    "studentiincrisi", "ragazzesingle", "vitasociale", "battutesquallide",
    "ragazzestupende", "vitadasingle", "amichepazze", "comiciitaliani",
    "scherzidivertenti", "coppieitaliane", "ironiaportamivia", "maiunagioia"
]

all_owners = set()

# Grup halinde tarayalım, her run için Apify API açılıp kapanma süresini azaltır
for i in range(0, len(hashtags), 5):
    batch_tags = hashtags[i:i+5]
    print(f"\n🔍 Batch Tags: {', '.join(batch_tags)}")
    results = run_apify("apify/instagram-hashtag-scraper", {
        "hashtags": batch_tags,
        "resultsLimit": 750  # 5 hashtag x 150 = 750'e kadar post çeksin
    })
    
    if results:
        for item in results:
            owner = item.get("ownerUsername")
            if owner:
                all_owners.add(owner)
        print(f"  → {len(results)} post bulundu, toplam unique username: {len(all_owners)}")
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
    print(f"\nBatch {i//25+1}/{(len(owner_list)+24)//25}: {len(batch)} profil")
    results = run_apify("apify/instagram-profile-scraper", {"usernames": batch})
    if results:
        all_profiles.extend(results)
    time.sleep(1)

print(f"\n📊 Toplam profil çekildi: {len(all_profiles)}")

# Ham veriyi kaydet (debug için)
with open("/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/all_profiles_v2.json", "w") as f:
    json.dump(all_profiles, f, ensure_ascii=False, indent=2)

# ===== ADIM 3: AKILLI FİLTRELEME =====
print(f"\n{'='*60}")
print("🔧 ADIM 3: AKILLI FİLTRELEME")
print(f"{'='*60}")

final_list = []
seen_emails = set()
stats = {"total": 0, "no_followers": 0, "artist": 0, "business": 0, "no_email": 0, "accepted": 0}

for p in all_profiles:
    if "error" in p:
        continue
    stats["total"] += 1
    
    followers = p.get("followersCount", 0)
    if not (10000 <= followers <= 300000):
        stats["no_followers"] += 1
        continue
    
    username = p.get("username", "")
    bio = p.get("biography", "")
    full_name = p.get("fullName", "")
    
    # Sınıflandır
    category, reason = classify_profile(bio, username, full_name)
    
    if category == "artist":
        print(f"  🎭 @{username} ({followers:,}) - SANATÇI ({reason}) → ATLA")
        stats["artist"] += 1
        continue
    
    if category == "business":
        print(f"  🏢 @{username} ({followers:,}) - BUSINESS ({reason}) → ATLA")
        stats["business"] += 1
        continue
    
    # Email bul
    email = extract_email(bio) or p.get("businessEmail")
    if not email:
        # Bio'da email yok, businessEmail de yok → atla
        stats["no_email"] += 1
        continue
        
    # Engagement check
    is_good_engagement, eng_reason = evaluate_engagement(p)
    if not is_good_engagement:
        print(f"  📉 @{username} ({followers:,}) - DÜŞÜK ETKİLEŞİMLİ ({eng_reason}) → ATLA")
        if "low_engagement" not in stats:
            stats["low_engagement"] = 0
        stats["low_engagement"] += 1
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
        "Kategori": category,
        "Bio": bio.replace("\n", " | ")[:200]
    })
    stats["accepted"] += 1
    print(f"  ✅ @{username} ({full_name}) | {followers:,} | {category} | 📧 {email}")

# Sırala
final_list.sort(key=lambda x: x["Takipçi"], reverse=True)

# CSV kaydet
csv_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/influencers_final.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Username", "İsim", "Platform", "Takipçi", "Email", "Website", "Profil", "Kategori", "Bio"])
    writer.writeheader()
    writer.writerows(final_list)

print(f"\n{'='*60}")
print(f"📊 İSTATİSTİKLER")
print(f"{'='*60}")
print(f"  Toplam profil: {stats['total']}")
print(f"  Takipçi aralığı dışı: {stats['no_followers']}")
print(f"  Sanatçı (stand-up, aktör vs.): {stats['artist']}")
print(f"  Business/meme page: {stats['business']}")
print(f"  E-posta yok: {stats['no_email']}")
print(f"  ✅ Kabul edilen: {stats['accepted']}")

print(f"\n{'='*60}")
print(f"🎉 SONUÇ: {len(final_list)} UGC creator (gerçek kişi + email + sanatçı DEĞİL)")
print(f"📁 CSV: {csv_file}")
print(f"{'='*60}")
for r in final_list:
    print(f"  👤 {r['Username']} ({r['İsim']}) | {r['Takipçi']:,} | 📧 {r['Email']}")
    print(f"     Bio: {r['Bio'][:120]}...")

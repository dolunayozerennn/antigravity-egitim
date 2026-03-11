import json
import re

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

CREATOR_SIGNALS = [
    "content creator", "creator", "ugc", "influencer",
    "collaborazioni", "collab", "collaborazione",
    "per info", "per collab", "business", "partnership",
    "digital creator", "video creator",
    "pov", "skit", "sketch",
    "tiktok", "reels", "youtube", "coppia", "vitadicoppia", "divertente"
]

def classify_profile(bio, username, full_name):
    bio_lower = (bio or "").lower()
    username_lower = (username or "").lower()
    
    for kw in BUSINESS_KEYWORDS:
        if kw in bio_lower: return "business", kw
    for kw in USERNAME_BLACKLIST:
        if kw in username_lower: return "business", f"username:{kw}"
    for kw in ARTIST_KEYWORDS:
        if kw in bio_lower: return "artist", kw
    
    creator_score = sum(1 for kw in CREATOR_SIGNALS if kw in bio_lower)
    if creator_score >= 1: return "creator", f"score={creator_score}"
    
    return "unknown", "no signal"

def extract_email(text):
    if not text: return None
    emails = re.findall(r'[\w\.\-\+]+@[\w\.\-]+\.\w{2,}', text)
    for e in emails:
        el = e.lower()
        if not any(x in el for x in ["sentry", "example", "test", "facebook", "instagram",
                                      "cdninstagram", "fbcdn", "noreply", "privacy", "support@",
                                      "redazione@", "info@wordpress"]):
            return e
    return None

def evaluate_engagement(profile_data):
    followers = profile_data.get("followersCount", 1)
    posts = profile_data.get("latestPosts", [])
    if not posts: return False, "no posts"
    
    views = []
    likes = []
    for post in posts:
        vc = post.get("videoPlayCount") or post.get("videoViewCount") or 0
        if vc > 0: views.append(vc)
        lc = post.get("likesCount", 0)
        likes.append(lc)
    
    med_views = sorted(views)[len(views)//2] if views else 0
    med_likes = sorted(likes)[len(likes)//2] if likes else 0
    
    view_rate = med_views / followers if followers > 0 else 0
    like_rate = med_likes / followers if followers > 0 else 0
    
    if view_rate < 0.15 or like_rate < 0.008 or med_views < 5000:
        return False, f"low engagement: vr={view_rate:.2f}, lr={like_rate:.2f}, mv={med_views}"
    return True, f"good metric: vr={view_rate:.2f}, lr={like_rate:.2f}, mv={med_views}"

with open('/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/all_profiles_v2.json', 'r') as f:
    all_profiles = json.load(f)

final_list = []
seen_emails = set()
stats = {"total": 0, "no_followers": 0, "artist": 0, "business": 0, "no_email": 0, "low_engagement": 0, "accepted": 0}

for p in all_profiles:
    if "error" in p: continue
    stats["total"] += 1
    
    followers = p.get("followersCount", 0)
    if not (10000 <= followers <= 300000):
        stats["no_followers"] += 1
        continue
    
    username = p.get("username", "")
    bio = p.get("biography", "")
    full_name = p.get("fullName", "")
    
    category, reason = classify_profile(bio, username, full_name)
    if category in ["artist", "business"]:
        stats[category] += 1
        continue
        
    email = extract_email(bio) or p.get("businessEmail")
    if not email:
        stats["no_email"] += 1
        continue
        
    if email in seen_emails: continue
    seen_emails.add(email)
    
    is_good_engagement, eng_reason = evaluate_engagement(p)
    if not is_good_engagement:
        stats["low_engagement"] += 1
        continue
        
    final_list.append(f"@{username} ({followers:,}) | {category} | {eng_reason} | {email}")
    stats["accepted"] += 1

print("\n".join(final_list))
print(stats)

import requests
import re
import csv
import time
import json

# İtalyan skit/komedi influencerları - web araştırmasından derlenen liste
# Sadece gerçek kişiler (personal creators), meme/fan page DEĞİL
CREATORS = [
    # Hypetrace.com 2025 listesinden (İtalyan TikTok komedi micro-influencer)
    {"username": "ettoreianni", "platform": "TikTok+IG", "note": "Duet comedy, ~50k followers"},
    {"username": "sonoalessiorusso", "platform": "TikTok+IG", "note": "Comedy creator, ~40k followers"},
    {"username": "rtpiccolo", "platform": "TikTok+IG", "note": "Duet comedy, ~30k followers"},
    {"username": "gabriele_benatti_art", "platform": "TikTok+IG", "note": "Comedy + arts, ~30k followers"},
    {"username": "michele.97_", "platform": "TikTok+IG", "note": "Comedy creator, ~30k followers"},
    {"username": "itsme.rina", "platform": "TikTok+IG", "note": "Comedy + arts skits, ~20k followers"},
    
    # Favikon/web araştırmasından - skit yaratıcıları  
    {"username": "paolocamilli", "platform": "IG+TikTok", "note": "Attore, sketch comedy, char parodies"},
    {"username": "mattisstanga", "platform": "IG+TikTok", "note": "POV video clips, everyday comedy"},
    {"username": "valentinabarbieri_", "platform": "IG+TikTok", "note": "Digital imitator, celebrity mimics"},
    {"username": "edoardoferrarioofficial", "platform": "IG+YouTube", "note": "Comedian, skit actor"},
    {"username": "arnaldomangini", "platform": "IG+TikTok", "note": "Magic tricks + comedy"},
    {"username": "roccothecomic", "platform": "IG+TikTok", "note": "Italian-American comedy sketches"},
    {"username": "lionfield_", "platform": "IG+TikTok", "note": "Duo: music + Italian cuisine comedy"},
    
    # İtalyan stand-up/skit - önceki aramadan doğrulanan kişisel hesaplar
    {"username": "queenbenedetto", "platform": "Instagram", "note": "Lorena Benedetto, immigrant humor stand-up"},
    {"username": "simonettamusitano", "platform": "Instagram", "note": "Stand-up comedy, live show"},
    {"username": "andreasaleri_standup", "platform": "Instagram", "note": "Stand-up comedian"},
    {"username": "renato.coppotelli", "platform": "Instagram", "note": "ER TIGNA, attore comico, serie TV"},
    
    # Ek İtalyan komedi/skit yaratıcıları
    {"username": "ciromarzella_", "platform": "IG+TikTok", "note": "Stand-up comedian napoletano"},
    {"username": "marcellomacchia", "platform": "IG+TikTok", "note": "Comedian, content creator"},
    {"username": "filippogiardina_", "platform": "Instagram", "note": "Stand-up comedian"},
    {"username": "leilamantineo", "platform": "Instagram", "note": "Comedian, actress"},
    {"username": "giu_trainotti", "platform": "IG+TikTok", "note": "Comedy content creator"},
    {"username": "emanuelaridolfo", "platform": "Instagram", "note": "Comediana, attrice"},
    {"username": "lucadelvecchiocomic", "platform": "Instagram", "note": "Comedian"},
    {"username": "marcoalagna_", "platform": "Instagram", "note": "Comedy content creator"},
    
    # Monica Ward - web'den bulunan İtalyan komedyen
    {"username": "monica.ward_official", "platform": "IG+TikTok", "note": "Entertainment, comedy, travel"},
]

def extract_emails_from_text(text):
    if not text:
        return []
    return re.findall(r'[\w\.\-\+]+@[\w\.\-]+\.\w{2,}', text)

def scrape_instagram_bio(username):
    """Instagram profilinden bio ve e-posta çekmeye çalış (web scraping)"""
    try:
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return None, None
        
        # Meta description'dan bio çek
        bio_match = re.search(r'<meta\s+(?:property="og:description"|name="description")\s+content="([^"]*)"', resp.text)
        bio = bio_match.group(1) if bio_match else ""
        
        # Takipçi sayısı
        followers_match = re.search(r'(\d[\d,\.]*)\s*[Ff]ollowers', resp.text)
        follower_count = 0
        if followers_match:
            follower_str = followers_match.group(1).replace(",", "").replace(".", "")
            try:
                follower_count = int(follower_str)
            except:
                pass
        
        # E-posta regex
        emails = extract_emails_from_text(bio)
        emails += extract_emails_from_text(resp.text[:50000])  # İlk 50k karakter
        
        # Filtreleme (çöp e-postaları at)
        clean_emails = []
        for e in emails:
            e_lower = e.lower()
            if any(x in e_lower for x in ["sentry", "example", "test", "facebook", "instagram", "fbcdn", "cdninstagram"]):
                continue
            clean_emails.append(e)
        
        return bio, list(set(clean_emails)), follower_count
    except Exception as ex:
        return None, [], 0

print("="*60)
print("🇮🇹 İTALYAN SKİT/KOMEDİ INFLUENCER TARAMASI")
print("   Web scraping yöntemiyle (Apify limiti aşıldı)")
print("="*60)

results = []

for creator in CREATORS:
    username = creator["username"]
    print(f"\n🔍 @{username}...", end="", flush=True)
    
    bio, emails, followers = scrape_instagram_bio(username)
    
    if bio is None:
        print(" ❌ profil bulunamadı/erişilemedi")
        continue
    
    if emails:
        print(f" ✅ {followers:,} takipçi | 📧 {emails[0]}")
        results.append({
            "Username": f"@{username}",
            "Platform": creator["platform"],
            "Takipçi": followers if followers else creator["note"],
            "Email": emails[0],
            "Profil": f"https://www.instagram.com/{username}/",
            "Not": creator["note"],
            "Bio": (bio or "")[:200]
        })
    else:
        print(f" ⚠️ {followers:,} takipçi | e-posta yok")
    
    time.sleep(1.5)  # Rate limiting

# Sonuçları kaydet
csv_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/influencers_final.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Username", "Platform", "Takipçi", "Email", "Profil", "Not", "Bio"])
    writer.writeheader()
    writer.writerows(results)

print(f"\n{'='*60}")
print(f"🎉 SONUÇ: {len(results)} influencer (gerçek kişi + e-postası var)")
print(f"📁 CSV: {csv_file}")
print(f"{'='*60}")
for r in results:
    print(f"  👤 {r['Username']} | {r['Platform']} | {r['Takipçi']} | 📧 {r['Email']}")

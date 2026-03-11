import requests
import time
import json
import re
import csv

API_KEYS = [
    os.environ.get("APIFY_API_KEY_1", ""),  # Yeni hesap (kredili)
    os.environ.get("APIFY_API_KEY_2", ""),  # Ana hesap
]
current_key_idx = 0

def get_headers():
    return {"Authorization": f"Bearer {API_KEYS[current_key_idx]}", "Content-Type": "application/json"}

def run_apify(actor_id, payload, max_poll=600):
    global current_key_idx
    actor_id = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    
    print(f"🚀 {actor_id}")
    
    # Try with current key, fallback to next
    for attempt in range(len(API_KEYS)):
        headers = get_headers()
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 403:
            print(f"  ⚠️ API key {current_key_idx} 403 hatası, yedek anahtara geçiliyor...")
            current_key_idx = (current_key_idx + 1) % len(API_KEYS)
            continue
        resp.raise_for_status()
        break
    else:
        print("  ❌ Tüm API anahtarları reddedildi!")
        return None
    
    run_id = resp.json()["data"]["id"]
    print(f"  Run ID: {run_id}")
    
    headers = get_headers()
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
    emails = re.findall(r'[\w\.\-\+]+@[\w\.\-]+\.\w+', text)
    for e in emails:
        if not any(x in e.lower() for x in ["example.com", "sentry", "test.com"]):
            return e
    return None

# ===== WEB ARAŞTIRMASINDAN GELEN İSİMLER =====
# Micro/Mid influencer İtalyan skit/komedi yaratıcıları
target_usernames_ig = [
    # Hypetrace listesinden
    "ettoreianni",
    "uybavolley", 
    "navdeep.lubani",
    "sonoalessiorusso",
    "rtpiccolo",
    "gabriele_benatti_art",
    "jjfra___",
    "yasserbenjillali",
    "michele.97_",
    "itsme.rina",
    # Favikon / web araştırması
    "paolocamilli",
    "mattisstanga",  # mattia stanga
    "valentinabarbieri_",
    # Ek İtalyan skit yaratıcıları - keyword search ile bulunabilenler
    "renato.coppotelli",  # ER TIGNA - skit/komedi aktörü (önceki aramada çıktı)
    "monicawardofficial",
    # Ek araştırma sonuçları
    "roccothecomic",
    "lionfield_",
    "arnaldomangini",
    # Daha fazla İtalyan skit yaratıcısı
    "leilamantineo",
    "giu_trainotti",
    "edoardoferrarioofficial",
    "marcoalagna_",
    "andreasaleri_standup",
    "simonettamusitano",
    "lucadelvecchiocomic",
    "emanuelaridolfo",
    "queenbenedetto",
    "ciromarzella_",
    "marcellomacchia",
    "filippogiardina_",
]

target_usernames_tiktok = [
    "ettoreianni",
    "sonoalessiorusso",
    "rtpiccolo",
    "paolocamilli",
    "mattisstanga",
    "valentinabarbieri_",
    "er.tigna",
    "roccothecomic",
    "arnaldomangini",
    "edoardoferrario",
    "ciromarzella",
    "marcellomacchia",
    "giu_trainotti",
]

# ===== INSTAGRAM PROFİLLERİNİ ÇEK =====
print("="*50)
print("📸 INSTAGRAM PROFİL TARAMASI")
print("="*50)

# Batch halinde çek
ig_profiles = []
for i in range(0, len(target_usernames_ig), 25):
    batch = target_usernames_ig[i:i+25]
    print(f"\nBatch {i//25 + 1}: {len(batch)} profil")
    results = run_apify("apify/instagram-profile-scraper", {"usernames": batch})
    if results:
        ig_profiles.extend(results)
    time.sleep(2)

print(f"\n📊 Toplam Instagram profil çekildi: {len(ig_profiles)}")

# ===== TIKTOK PROFİLLERİNİ ÇEK =====
print("\n" + "="*50)
print("📱 TIKTOK PROFİL TARAMASI")  
print("="*50)

# TikTok için profile araması
tiktok_profiles = []
for username in target_usernames_tiktok:
    print(f"\n🔍 TikTok arama: '{username}'")
    results = run_apify("clockworks/tiktok-user-search-scraper", {
        "searchQuery": username,
        "maxProfiles": 5,
        "resultsPerPage": 5
    })
    if results:
        # En uygun eşleşmeyi bul
        for r in results:
            if r.get("name", "").lower() == username.lower() or username.lower() in r.get("name", "").lower():
                tiktok_profiles.append(r)
                break
    time.sleep(2)

print(f"\n📊 Toplam TikTok profil eşleşti: {len(tiktok_profiles)}")

# ===== BİRLEŞTİR VE FİLTRELE =====
print("\n" + "="*50)
print("🔧 FİLTRELEME VE BİRLEŞTİRME")
print("="*50)

final_list = []
seen_emails = set()

# Instagram sonuçları
for prof in ig_profiles:
    if "error" in prof:
        continue
    
    followers = prof.get("followersCount", 0)
    if not (10000 <= followers <= 300000):
        continue
    
    bio = prof.get("biography", "")
    username = prof.get("username", "")
    full_name = prof.get("fullName", "")
    
    email = extract_email(bio) or prof.get("businessEmail")
    if not email:
        continue
    
    if email in seen_emails:
        continue
    seen_emails.add(email)
    
    website = prof.get("externalUrl", "")
    
    final_list.append({
        "Username": f"@{username}",
        "İsim": full_name,
        "Platform": "Instagram",
        "Takipçi": followers,
        "Email": email,
        "Website": website or "",
        "Profil": f"https://www.instagram.com/{username}/",
        "Bio": bio.replace("\n", " | ")[:200]
    })

# TikTok sonuçları
for prof in tiktok_profiles:
    fans = prof.get("fans", 0)
    if not (10000 <= fans <= 300000):
        continue
    
    bio = prof.get("signature", "")
    username = prof.get("name", "")
    nickname = prof.get("nickName", "")
    
    email = extract_email(bio)
    if not email:
        continue
    
    if email in seen_emails:
        continue
    seen_emails.add(email)
    
    biolink = prof.get("bioLink")
    if isinstance(biolink, dict):
        biolink = biolink.get("link", "")
    
    final_list.append({
        "Username": f"@{username}",
        "İsim": nickname,
        "Platform": "TikTok",
        "Takipçi": fans,
        "Email": email,
        "Website": biolink or "",
        "Profil": prof.get("profileUrl", f"https://www.tiktok.com/@{username}"),
        "Bio": (bio or "").replace("\n", " | ")[:200]
    })

# Takipçi sayısına göre sırala (büyükten küçüğe)
final_list.sort(key=lambda x: x["Takipçi"], reverse=True)

# CSV'ye kaydet
csv_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/influencers_final.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Username", "İsim", "Platform", "Takipçi", "Email", "Website", "Profil", "Bio"])
    writer.writeheader()
    writer.writerows(final_list)

print(f"\n{'='*50}")
print(f"🎉 SONUÇ: {len(final_list)} influencer (gerçek kişi, e-postası var)")
print(f"📁 CSV: {csv_file}")
print(f"{'='*50}")
for inf in final_list:
    print(f"  👤 {inf['Username']} ({inf['İsim']}) | {inf['Platform']} | {inf['Takipçi']:,} | 📧 {inf['Email']}")

# JSON yedek
json_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/all_profiles_raw.json"
with open(json_file, "w", encoding="utf-8") as f:
    json.dump({"instagram": ig_profiles, "tiktok": tiktok_profiles}, f, ensure_ascii=False, indent=2)

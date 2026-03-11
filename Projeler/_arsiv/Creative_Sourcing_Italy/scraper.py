import os
import sys
import json
import time
import re
import requests
import csv

API_KEY = os.environ.get("APIFY_API_KEY", "")

def run_apify_task(actor_id, payload, max_polling_time=600):
    actor_id = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"🚀 Başlatılıyor: {actor_id}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ Görev oluşturuldu. Run ID: {run_id}")
    except Exception as e:
        print(f"❌ Görev başlatılamadı: {e}")
        return None

    poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    start_time = time.time()
    
    while True:
        try:
             status_response = requests.get(poll_url, headers=headers)
             status_response.raise_for_status()
             status_data = status_response.json()["data"]
             status = status_data["status"]
             
             if status == "SUCCEEDED":
                 default_dataset_id = status_data["defaultDatasetId"]
                 print(f"✅ Görev tamamlandı! Dataset ID: {default_dataset_id}")
                 
                 dataset_url = f"https://api.apify.com/v2/datasets/{default_dataset_id}/items"
                 results_response = requests.get(dataset_url, headers=headers)
                 results_response.raise_for_status()
                 
                 return results_response.json()
                 
             elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                 print(f"❌ Görev başarısız oldu. Durum: {status}")
                 return None
                 
        except Exception as e:
             pass
             
        if time.time() - start_time > max_polling_time:
            print(f"❌ Zaman aşımı! ({max_polling_time} saniye)")
            return None
            
        time.sleep(10)

def extract_email(text):
    if not text:
        return None
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else None

def get_tiktok_influencers():
    print("TikTok araması başlatılıyor...")
    payload = {
        "searchQuery": "italia commedia",
        "maxProfiles": 150,
        "resultsPerPage": 50
    }
    
    results = run_apify_task("clockworks/tiktok-user-search-scraper", payload)
    influencers = []
    
    if results:
        for item in results:
            followers = item.get("fans", 0)
            
            # Sadece 10k - 300k arası
            if 10000 <= followers <= 300000:
                bio = item.get("signature", "")
                email = extract_email(bio)
                
                influencers.append({
                    "Username": item.get("nickName", "") or item.get("name", ""),
                    "Platform": "TikTok",
                    "Followers": followers,
                    "Bio": bio,
                    "Email": email,
                    "Link": item.get("profileUrl", "")
                })
    return influencers

def get_instagram_influencers():
    print("Instagram araması başlatılıyor...")
    payload = {
        "hashtags": ["scherzi", "commediaitaliana"],
        "resultsLimit": 100
    }
    
    results = run_apify_task("apify/instagram-hashtag-scraper", payload)
    unique_users = set()
    
    if results:
        for item in results:
            owner = item.get("ownerUsername")
            if owner and "error" not in item:
                unique_users.add(owner)
                
    if not unique_users:
        return []
        
    print(f"Instagram profiling: {len(unique_users)} kişi için profiller çekiliyor...")
    prof_payload = {
        "usernames": list(unique_users)[:50],
        "resultsLimit": 50
    }
    prof_results = run_apify_task("apify/instagram-profile-scraper", prof_payload)
    
    influencers = []
    if prof_results:
        for prof in prof_results:
            if "error" in prof:
                continue
            followers = prof.get("followersCount", 0)
            if 10000 <= followers <= 300000:
                bio = prof.get("biography", "")
                email = extract_email(bio)
                influencers.append({
                    "Username": prof.get("username", ""),
                    "Platform": "Instagram",
                    "Followers": followers,
                    "Bio": bio,
                    "Email": email,
                    "Link": prof.get("url", "")
                })
                
    return influencers

if __name__ == "__main__":
    tiktok_list = get_tiktok_influencers()
    insta_list = get_instagram_influencers()
    
    all_influencers = tiktok_list + insta_list
    
    # Sadece e-postası olanları öne çıkaralım (şu an için ikisi de geçerli)
    
    csv_file = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Creative_Sourcing_Italy/influencers.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Username", "Platform", "Followers", "Email", "Link", "Bio"])
        writer.writeheader()
        writer.writerows(all_influencers)
        
    print(f"Toplam {len(all_influencers)} influencer bulundu. CSV: {csv_file}")

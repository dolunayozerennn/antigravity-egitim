import os
import re
import json
import pandas as pd
from apify_client import ApifyClient
from langdetect import detect, DetectorFactory

# For deterministic langdetect
DetectorFactory.seed = 0

# Using the active key (lwsa...)
APIFY_TOKEN = "apify_api_lwsaQjTTemCehNTswvPxyCE5L9R8Ey12MI25"
client = ApifyClient(APIFY_TOKEN)

# Italian Hashtags
HASHTAGS = [
    "intervisteperstrada",
    "comicitàitaliana",
    "skititaliani",
    "sketchcomici",
    "voxpopitalia",
    "risateitaliane",
    "comediansitaly",
    "standupcomedyitalia",
    "intervistestrada",
    "milanointerviste"
]

FOLLOWERS_MIN = 10000
FOLLOWERS_MAX = 200000

def extract_email(bio):
    if not bio: return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', bio)
    return match.group(0) if match else ""

def is_italian_or_relevant(profile):
    bio = profile.get("biography", "").lower()
    fullName = profile.get("fullName", "").lower()
    
    # Simple check for Italian language/location
    it_keywords = ["milano", "roma", "napoli", "torino", "italia", "it", "🇮🇹", "italiano", "comico", "attore", "creator"]
    if any(kw in bio for kw in it_keywords) or any(kw in fullName for kw in it_keywords):
        return True
    
    # Langdetect as fallback
    if len(bio) > 10:
        try:
            return detect(bio) == 'it'
        except:
            return False
    return False

def is_not_meme_page(username, bio, fullName):
    u, b, f = username.lower(), bio.lower(), fullName.lower()
    meme_sigs = ["meme", "videos", "clip", "post", "best", "daily", "community", "fanpage", "page", "raccolta", "pubblicità"]
    creator_sigs = ["creator", "actor", "attore", "comico", "comedian", "personal", "official", "scrittore", "per info", "collaborazioni", "gestito da", "official page of"]
    
    # If it has meme signatures and NO creator signatures, it's likely a meme page
    if any(s in u for s in ["meme", "best", "video"]) or any(s in b for s in ["video divertenti", "migliori video"]):
        if not any(s in b for s in creator_sigs) and not any(s in f for s in creator_sigs):
            return False
    return True

def main():
    all_usernames = set()
    
    print("Step 1: Scraping hashtags to find creator usernames...")
    try:
        hashtag_run = client.actor("apify/instagram-hashtag-scraper").call(
            run_input={
                "hashtags": HASHTAGS,
                "resultsLimit": 150 # 15 users per hashtag roughly
            }
        )
        for item in client.dataset(hashtag_run["defaultDatasetId"]).iterate_items():
            u = item.get("ownerUsername")
            if u: all_usernames.add(u)
    except Exception as e:
        print(f"Error scraping hashtags: {e}")

    print(f"Found {len(all_usernames)} unique candidates. Fetching profile details...")
    
    if not all_usernames:
        print("No usernames found.")
        return

    # Process candidates
    usernames_to_check = list(all_usernames)[:300]
    profile_urls = [f"https://www.instagram.com/{u}/" for u in usernames_to_check]
    
    results = []
    try:
        profile_run = client.actor("apify/instagram-scraper").call(
            run_input={
                "directUrls": profile_urls,
                "resultsType": "details",
                "resultsLimit": 150 # limit the run size for budget
            }
        )
        
        for profile in client.dataset(profile_run["defaultDatasetId"]).iterate_items():
            username = profile.get("username")
            if not username: continue
            
            followers = profile.get("followersCount", 0)
            bio = profile.get("biography", "")
            fullName = profile.get("fullName", "")
            
            # Filter 1: Followers (10k - 200k)
            if not (FOLLOWERS_MIN <= followers <= FOLLOWERS_MAX):
                continue
            
            # Filter 2: Italian/Relevant
            if not is_italian_or_relevant(profile):
                continue
                
            # Filter 3: No meme pages
            if not is_not_meme_page(username, bio, fullName):
                continue
                
            email = extract_email(bio)
            
            results.append({
                "Username": username,
                "Full Name": fullName,
                "Followers": followers,
                "Niche": "Comedy/Skit/Street Interview",
                "Bio": bio,
                "Instagram URL": f"https://instagram.com/{username}",
                "Email": email
            })
            
            if len(results) >= 55:
                break
                
    except Exception as e:
        print(f"Error fetching profiles: {e}")

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Followers", ascending=False)
        output_file = "Italian_Influencers_Final_50.csv"
        df.head(50).to_csv(output_file, index=False)
        print(f"Successfully saved {len(df.head(50))} influencers to {output_file}")
    else:
        print("No influencers matched the criteria. Check if there were results in the scraper.")

if __name__ == "__main__":
    main()

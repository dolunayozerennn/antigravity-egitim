import os
import re
import datetime
import pandas as pd
from apify_client import ApifyClient
from langdetect import detect, DetectorFactory

# For deterministic langdetect
DetectorFactory.seed = 0

API_KEY = "apify_api_oouPGgkmSJZ0K7PrpBfLx6FwxH4hD23SlgQP"
client = ApifyClient(API_KEY)

# Italian hashtags for skit, comedy, street interview
HASHTAGS = [
    # Street Interview
    "intervisteperstrada", "voxpopitalia", "domandepazzesche", "intervistestrada",
    "microfono", "milanointerviste", "domandeeperstrada", "interviste",
    # Comedy/Skit
    "comicitàitaliana", "skititaliani", "battuteitaliane", "comicoitaliano",
    "risateitaliane", "divertenteitaliano", "commedia", "ironiaitaliana",
    "parodia", "divertentemolto", "comiciitaliani"
]

# Keywords for keyword search
KEYWORDS = [
    "interviste per strada",
    "interviste milano",
    "interviste roma",
    "comico milano",
    "comico roma",
    "content creator italia",
    "comedy milano",
    "comedy roma",
    "sketch italiani",
    "skit italia"
]

# Settings
FOLLOWERS_MIN = 10000
FOLLOWERS_MAX = 200000

def extract_email(bio):
    if not bio:
        return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', bio)
    return match.group(0) if match else ""

def is_italian_or_it_bio(bio):
    if not bio or len(bio.strip()) < 5:
        # Check for Italian cities or keywords if too short
        it_keywords = ["milano", "roma", "napoli", "torino", "italia", "it", "🇮🇹"]
        if any(kw in bio.lower() for kw in it_keywords):
            return True
        return False
    try:
        lang = detect(bio)
        return lang == 'it'
    except:
        return False

def is_meme_page(username, bio, fullName):
    username = username.lower()
    bio = bio.lower()
    fullName = fullName.lower()
    
    meme_indicators = ["meme", "videos", "clip", "post", "best", "daily", "community", "fanpage", "page"]
    
    # If the username is very generic
    if any(ind in username for ind in meme_indicators):
        # But if bio says "creator" or "actor", it might be a person
        person_indicators = ["creator", "actor", "attore", "comico", "comedian", "personal", "official"]
        if not any(p_ind in bio for p_ind in person_indicators):
            return True
            
    return False

def main():
    usernames = set()
    
    print(f"Step 1: Scrapping hashtags...")
    hashtag_input = {
        "hashtags": HASHTAGS,
        "resultsLimit": 200, # 200 per hashtag
    }
    hashtag_run = client.actor("apify/instagram-hashtag-scraper").call(run_input=hashtag_input)
    
    for item in client.dataset(hashtag_run["defaultDatasetId"]).iterate_items():
        if item.get("ownerUsername"):
            usernames.add(item["ownerUsername"])
            
    print(f"Total usernames from hashtags: {len(usernames)}")
    
    # Also keywords
    print(f"Step 2: Scrapping keywords...")
    for kw in KEYWORDS:
        kw_input = {
            "searchQuery": kw,
            "resultsLimit": 100,
        }
        # Using a search actor (checking if crawler-bros/instagram-keyword-search-scraper is better or just search)
        # Actually instagram-scraper has searchQuery
        kw_run = client.actor("apify/instagram-scraper").call(run_input={"search": kw, "resultsType": "details", "resultsLimit": 50})
        for item in client.dataset(kw_run["defaultDatasetId"]).iterate_items():
            if item.get("username"):
                usernames.add(item["username"])
    
    print(f"Total unique usernames to check: {len(usernames)}")
    
    if not usernames:
        print("No creators found. Exiting.")
        return

    # Fetch profile details for all found usernames
    # To avoid huge runs, let's process in batches or just run once if not too many
    profile_urls = [f"https://www.instagram.com/{user}/" for user in list(usernames)]
    
    print(f"Step 3: Fetching profile details for {len(profile_urls)} profiles...")
    
    profile_run_input = {
        "directUrls": profile_urls,
        "resultsType": "details",
        "resultsLimit": len(profile_urls)
    }
    
    profile_run = client.actor("apify/instagram-scraper").call(run_input=profile_run_input)
    
    results = []
    for profile in client.dataset(profile_run["defaultDatasetId"]).iterate_items():
        if not profile.get("username"):
            continue
            
        username = profile.get("username")
        fullName = profile.get("fullName", "")
        followers = profile.get("followersCount", 0)
        bio = profile.get("biography", "")
        url = profile.get("url", f"https://instagram.com/{username}")
        
        # Filter 1: Followers
        if not (FOLLOWERS_MIN <= followers <= FOLLOWERS_MAX):
            continue
            
        # Filter 2: Italian
        if not is_italian_or_it_bio(bio):
            # Check fullname
            if not is_italian_or_it_bio(fullName):
                continue
        
        # Filter 3: No meme pages
        if is_meme_page(username, bio, fullName):
            continue
            
        email = extract_email(bio)
        
        results.append({
            "Username": username,
            "Full Name": fullName,
            "Followers": followers,
            "Bio": bio,
            "Instagram URL": url,
            "Email": email
        })
        
    df = pd.DataFrame(results)
    df = df.drop_duplicates(subset=["Username"])
    
    # Save the top 50
    final_list = df.head(50)
    
    output_file = "Italian_Influencers_50.csv"
    final_list.to_csv(output_file, index=False)
    
    print(f"Done! Found {len(df)} Italian creators. Saved top 50 to {output_file}.")

if __name__ == "__main__":
    main()

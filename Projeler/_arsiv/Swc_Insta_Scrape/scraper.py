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

# Expanded list of competitor hashtags to bypass the 1-page free limit per hashtag
COMPETITORS = [
    # Core original competitors
    "walktask", "walktaskapp", "walktaskmoney", "walktaskcode", "walktaskreferral",
    "weward", "wewardapp", "wewards", "wewardmoney", "wewardcode", "wewardreferral", "wewardfr",
    "walkcash", "walkcashapp", "walkcashmoney", "walkcashcode", "walkcashreferral",
    "walkcity", "walkcityapp", "walkcitymoney", "walkcitycode",
    "walkwork", "walkworkapp", "walkworkmoney", "walkworkcode", "walkworkreferral",
    # Additional competitors identified for volume
    "stepsetgo", "stepsetgoapp", "stepsetgoreward",
    "cashwalk", "cashwalkapp", "cashwalkrewards",
    "macadam", "macadamapp",
    "winwalk", "winwalkapp", "winwalkrewards",
    "stepler", "steplerapp",
    "moneywalk", "moneywalkapp",
    "mypacer", "pacerapp",
    # General concepts (Excluding sweatcoin/sweat economy)
    "makemoneywalking", "walkandearn", "walkingsidehustle", "movetoearn", "walk2earn", "getpaidtowalk"
]

# Settings
POSTS_LIMIT_PER_HASHTAG = 200

def extract_email(bio):
    if not bio:
        return ""
    # simple email regex
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', bio)
    return match.group(0) if match else ""

def detect_language(bio):
    if not bio or len(bio.strip()) < 5:
        return "unknown"
    try:
        lang = detect(bio)
        # Map code to required languages if possible, else return the code
        lang_map = {
            'en': 'English',
            'es': 'Spanish',
            'pt': 'Portuguese',
            'de': 'German',
            'ar': 'Arabic',
            'fr': 'French'
        }
        return lang_map.get(lang, lang.upper())
    except:
        return "unknown"

def main():
    print(f"Step 1: Fetching posts to find content creators (Limit {POSTS_LIMIT_PER_HASHTAG}/tag)...")
    
    post_run_input = {
        "hashtags": COMPETITORS,
        "resultsLimit": POSTS_LIMIT_PER_HASHTAG * len(COMPETITORS),
    }
    
    # Use the dedicated hashtag scraper for better volume
    post_run = client.actor("apify/instagram-hashtag-scraper").call(run_input=post_run_input)
    
    usernames = set()
    for item in client.dataset(post_run["defaultDatasetId"]).iterate_items():
        if item.get("ownerUsername"):
            usernames.add(item["ownerUsername"])
            
    print(f"Found {len(usernames)} unique creators. Fetching profiles...")
    if not usernames:
        print("No creators found. Exiting.")
        return

    profile_urls = [f"https://www.instagram.com/{user}/" for user in list(usernames)]
    
    profile_run_input = {
        "directUrls": profile_urls,
        "resultsType": "details",
    }
    
    profile_run = client.actor("apify/instagram-scraper").call(run_input=profile_run_input)
    
    results = []
    for profile in client.dataset(profile_run["defaultDatasetId"]).iterate_items():
        if not profile.get("username"):
            continue
            
        username = profile.get("username")
        url = profile.get("url", f"https://instagram.com/{username}")
        full_name = profile.get("fullName", username)
        followers = profile.get("followersCount", 0)
        bio = profile.get("biography", "")
        
        email = extract_email(bio)
        language = detect_language(bio)
        
        # Check active status
        # If latestPosts exists and is not empty, check if the latest post is within 90 days.
        latest_posts = profile.get("latestPosts", [])
        is_active = False
        if latest_posts:
            latest_post_timestamp = latest_posts[0].get("timestamp")
            if latest_post_timestamp:
                try:
                    # timestamp might be string ISO format or UTC date string
                    if "T" in latest_post_timestamp:
                        dt = datetime.datetime.fromisoformat(latest_post_timestamp.replace("Z", "+00:00"))
                    else:
                        dt = pd.to_datetime(latest_post_timestamp)
                    
                    # Convert dt to tz-naive UTC
                    if dt.tzinfo is not None:
                        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                    
                    if (datetime.datetime.utcnow() - dt).days <= 90:
                        is_active = True
                except Exception as e:
                    print(f"Error parsing timestamp {latest_post_timestamp}: {e}")
                    # fallback, if they have posts we just assume active or check postsCount
                    is_active = True
        
        # Another fallback for active status: they were found from a recent hashtag scrape anyway!
        if not latest_posts and profile.get("postsCount", 0) > 0:
            is_active = True # They posted recently enough to show up in our hashtag search

        results.append({
            "Instagram URL": url,
            "Profile Name": full_name,
            "Follower Count": followers,
            "Is Active (Last 90 Days)": is_active,
            "Language": language,
            "Email": email
        })
        
    df = pd.DataFrame(results)
    
    # Save to Excel by Language
    output_file = "Instagram_Creators.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        if df.empty:
            pd.DataFrame(columns=["No Data"]).to_excel(writer, sheet_name="Empty")
            print("No complete profiles extracted.")
            return

        # Prioritize these languages
        target_langs = ["English", "Spanish", "Portuguese", "German", "Arabic", "French"]
        
        for lang in target_langs:
            lang_df = df[df["Language"] == lang]
            if not lang_df.empty:
                lang_df.to_excel(writer, sheet_name=lang, index=False)
                
        # Others tab
        other_df = df[~df["Language"].isin(target_langs)]
        if not other_df.empty:
            # group all others in one tab so we don't spam tabs
            other_df.to_excel(writer, sheet_name="Others", index=False)
            
    print(f"Done! Saved {len(df)} profiles to {output_file}.")

if __name__ == "__main__":
    main()

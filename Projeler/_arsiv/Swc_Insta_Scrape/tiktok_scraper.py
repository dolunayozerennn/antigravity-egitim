import pandas as pd
from apify_client import ApifyClient
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

API_KEY = "apify_api_oouPGgkmSJZ0K7PrpBfLx6FwxH4hD23SlgQP"
client = ApifyClient(API_KEY)

COMPETITORS = ["walktask", "weward", "walkcash", "walkcity", "walkwork"]

def detect_language(bio):
    if not bio or len(bio.strip()) < 5:
        return "unknown"
    try:
        lang = detect(bio)
        lang_map = {
            'en': 'English', 'es': 'Spanish', 'pt': 'Portuguese',
            'de': 'German', 'ar': 'Arabic', 'fr': 'French'
        }
        return lang_map.get(lang, lang.upper())
    except:
        return "unknown"

def main():
    print("Fetching TikTok videos to find content creators...")
    run_input = {
        "hashtags": COMPETITORS,
        "resultsPerPage": 200,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    }
    
    # Run the generic TikTok scraper
    # Note: we use varying hashtag scrapers; 'clockworks/tiktok-scraper' is a popular one, or 'sebastiene/tiktok-scraper'
    # We will try 'clockworks/tiktok-scraper'
    try:
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    except Exception as e:
        print("Fallback to normal tiktok-scraper:", e)
        run_input = {
            "hashtags": COMPETITORS,
            "resultsPerPage": 200
        }
        run = client.actor("apify/tiktok-scraper").call(run_input=run_input)

    usernames = set()
    results = []
    
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        author = item.get("authorMeta") or item.get("author")
        if not author:
            continue
            
        username = author.get("name") or item.get("authorMeta", {}).get("name")
        if not username or username in usernames:
            continue
        usernames.add(username)
        
        full_name = author.get("nickName") or author.get("nickname") or username
        followers = author.get("fans") or author.get("followers") or 0
        bio = author.get("signature") or author.get("bio") or ""
        
        url = f"https://www.tiktok.com/@{username}"
        language = detect_language(bio)
        
        # In TikTok, bio rarely has email, but we can try
        import re
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', bio)
        email = match.group(0) if match else ""
        
        # Because they posted about our hashtag, they are considered active
        is_active = True 
        
        results.append({
            "TikTok URL": url,
            "Profile Name": full_name,
            "Follower Count": followers,
            "Is Active (Last 90 Days)": is_active,
            "Language": language,
            "Email": email
        })
        
    df = pd.DataFrame(results)
    
    output_file = "TikTok_Creators.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        if df.empty:
            pd.DataFrame(columns=["No Data"]).to_excel(writer, sheet_name="Empty")
            print("No complete profiles extracted for TikTok.")
            return

        target_langs = ["English", "Spanish", "Portuguese", "German", "Arabic", "French"]
        for lang in target_langs:
            lang_df = df[df["Language"] == lang]
            if not lang_df.empty:
                lang_df.to_excel(writer, sheet_name=lang, index=False)
                
        other_df = df[~df["Language"].isin(target_langs)]
        if not other_df.empty:
            other_df.to_excel(writer, sheet_name="Others", index=False)
            
    print(f"Done! Saved {len(df)} profiles to {output_file}.")

if __name__ == "__main__":
    main()

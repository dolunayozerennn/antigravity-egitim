import requests
import re
import time
from bs4 import BeautifulSoup
from ddgs import DDGS

# Strict Filters
MIN_FOLLOWERS = 10000
MAX_FOLLOWERS = 300000

BANNED_KEYWORDS = [
    "booking", "management", "artisti", "founder", "ceo", "musician", 
    "attore", "attrice", "manager", "agency", "actor", "cantante", 
    "music", "label", "business", "company"
]

def fetch_tiktok_profile(username):
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,it;q=0.8"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            html = r.text
            
            followers = 0
            # Try to find followers in meta tags
            meta_match = re.search(r'content="([^"]+) Followers, ([^"]+) Following, ([^"]+) Likes', html)
            if meta_match:
                f_str = meta_match.group(1).lower().replace(',', '')
                multiplier = 1
                if 'k' in f_str:
                    multiplier = 1000
                    f_str = f_str.replace('k', '')
                elif 'm' in f_str:
                    multiplier = 1000000
                    f_str = f_str.replace('m', '')
                try:
                    followers = int(float(f_str) * multiplier)
                except:
                    pass
            else:
                # Try script block
                follower_m = re.search(r'"followerCount":(\d+)', html)
                if follower_m:
                    followers = int(follower_m.group(1))

            bio = ""
            bio_m = re.search(r'"signature":"([^"]*)"', html)
            if bio_m:
                bio = bio_m.group(1).replace('\\n', ' ')
            if not bio:
                bio_desc = re.search(r'<meta name="description" content=".*?\((@[a-zA-Z0-9_.]+)\) on TikTok\. (.*?)Watch the latest', html)
                if bio_desc:
                    bio = bio_desc.group(2)
            
            return followers, bio
    except Exception:
        pass
    
    return None, None

def search_and_filter_tiktokers():
    queries = [
        'site:tiktok.com @gmail.com comico italy',
        'site:tiktok.com @gmail.com scherzi italy',
        'site:tiktok.com @gmail.com divertenza italia',
        'site:tiktok.com @gmail.com intrattenimento italia'
    ]
    
    candidates = {}
    
    try:
        results = DDGS().text('site:tiktok.com @gmail.com comico italia', max_results=50)
        for q in queries:
            print(f"Searching: {q}")
            res = DDGS().text(q, max_results=50)
            if not res: continue
            for r in res:
                url = r.get('href', '')
                if 'tiktok.com/@' in url:
                    m = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', url)
                    if m:
                        uname = m.group(1)
                        if 'video/' not in url:
                            candidates[uname] = url
            time.sleep(1)
    except Exception as e:
        print(f"Search error: {e}")
            
    print(f"Found {len(candidates)} unique candidates. Verifying...")
    
    approved_creators = []
    
    for uname, url in candidates.items():
        print(f"Checking {uname}...")
        followers, bio = fetch_tiktok_profile(uname)
        time.sleep(1) 
        
        if followers is None and bio is None:
            continue
            
        print(f"  Followers: {followers} | Bio: {bio[:30]}...")
        
        # 1. Strict Follower Limit
        if followers < MIN_FOLLOWERS:
            print(f"  -> REJECTED: Low followers")
            continue
            
        status = "Approved"
        if followers > MAX_FOLLOWERS:
            status = f"FLAGGED (> {MAX_FOLLOWERS})"

        # 2. Persona/Niche Filter 
        bio_lower = bio.lower() if bio else ""
        has_banned = False
        for kw in BANNED_KEYWORDS:
            if kw in bio_lower:
                has_banned = True
                print(f"  -> REJECTED: Banned kw '{kw}'")
                break
        if has_banned: continue
            
        # 3. Explicit Email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@(?:gmail|hotmail|yahoo|outlook|libero|virgilio|icloud)\.[a-zA-Z]{2,}', bio) if bio else None
        if not email_match:
            print(f"  -> REJECTED: No email")
            continue
            
        email = email_match.group(0)
        print(f"  -> SUCCESS! Email: {email}")
        
        approved_creators.append({
            'username': uname,
            'url': url,
            'email': email,
            'followers': followers,
            'status': status,
            'bio': bio.replace('\n', ' ')[:100]
        })

    print(f"\nTotal Approved: {len(approved_creators)}")
    
    # Write to CSV tracking
    if len(approved_creators) > 0:
        md_file = '/Users/dolunayozeren/Desktop/Antigravity/Projeler/Sweatcoin_Email_Automation/creator_outreach_tracking.md'
        with open(md_file, 'a', encoding='utf-8') as f:
            for c in approved_creators:
                # Add to markdown tracking
                row = f"| **{c['username']}** | [TikTok]({c['url']}) | {c['email']} | {c['followers']} | TBD | Ready to Contact | - | Target range: 100€-300€ | {c['status']} |\n"
                f.write(row)
        print("Updated creator_outreach_tracking.md")

if __name__ == "__main__":
    search_and_filter_tiktokers()

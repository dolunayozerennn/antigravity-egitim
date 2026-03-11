import requests
import re
import time
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
                try: followers = int(float(f_str) * multiplier)
                except: pass
            else:
                follower_m = re.search(r'"followerCount":(\d+)', html)
                if follower_m: followers = int(follower_m.group(1))

            bio = ""
            bio_m = re.search(r'"signature":"([^"]*)"', html)
            if bio_m: bio = bio_m.group(1).replace('\\n', ' ')
            if not bio:
                bio_desc = re.search(r'<meta name="description" content=".*?\((@[a-zA-Z0-9_.]+)\) on TikTok\. (.*?)Watch the latest', html)
                if bio_desc: bio = bio_desc.group(2)
            
            return followers, bio
    except: pass
    return None, None

def mega_search():
    queries = [
        'site:tiktok.com "collab" OR "business" "commedia" "italia"',
        'site:tiktok.com "collab" OR "pr" "risate" "italy"',
        'site:tiktok.com "@virgilio.it" OR "@libero.it" "divertente"',
        'site:tiktok.com "@gmail.com" "intrattenimento" "italia"',
        'site:tiktok.com "@gmail.com" "scherzo" OR "ironia"',
        'site:tiktok.com "@gmail.com" "milano" OR "roma" "comedy"',
        'site:tiktok.com "ugc" "@gmail.com" "italia" OR "italy"'
    ]
    
    candidates = {}
    try:
        for q in queries:
            print(f"Searching: {q}")
            res = DDGS().text(q, max_results=40)
            if not res: continue
            for r in res:
                url = r.get('href', '')
                if 'tiktok.com/@' in url:
                    m = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', url)
                    if m:
                        uname = m.group(1)
                        if 'video/' not in url:
                            candidates[uname] = url
            time.sleep(2)
    except Exception as e:
        print(f"Search error: {e}")
            
    approved = []
    
    for uname, url in candidates.items():
        if len(approved) >= 50:
            break
            
        followers, bio = fetch_tiktok_profile(uname)
        time.sleep(1) 
        
        if followers is None or bio is None: continue
        
        if followers < MIN_FOLLOWERS: continue
            
        status = "Approved"
        if followers > MAX_FOLLOWERS:
            status = f"FLAGGED (> {MAX_FOLLOWERS})"

        bio_lower = bio.lower() if bio else ""
        if any(kw in bio_lower for kw in BANNED_KEYWORDS):
            continue
            
        email_m = re.search(r'[a-zA-Z0-9._%+-]+@(?:gmail|hotmail|yahoo|outlook|libero|virgilio|icloud)\.[a-zA-Z]{2,}', bio) if bio else None
        if not email_m: continue
            
        email = email_m.group(0)
        approved.append({
            'username': uname,
            'url': url,
            'email': email,
            'followers': followers,
            'status': status,
        })
        print(f"Added: {uname} ({followers}) - {email}")

    if approved:
        md_file = '/Users/dolunayozeren/Desktop/Antigravity/Projeler/Sweatcoin_Email_Automation/creator_outreach_tracking.md'
        with open(md_file, 'a', encoding='utf-8') as f:
            for c in approved:
                row = f"| **{c['username']}** | [TikTok]({c['url']}) | {c['email']} | {c['followers']} | TBD | Ready to Contact | - | Target range: 100€-300€ | {c['status']} |\n"
                f.write(row)
        print(f"Added {len(approved)} creators to MD file.")

if __name__ == "__main__":
    mega_search()

import re
import time
from duckduckgo_search import DDGS

def estimate_followers_from_snippet(snippet, title):
    # Instagram usually puts '15.2k Followers, 201 Following' in the snippet or title
    text = (snippet + " " + title).lower()
    
    # regex to find patterns like '15k followers', '15.2k followers', '1.5m followers', '150k takipçi'
    # Since it's Italian, it might be 'follower' or 'followers' or 'seguaci'
    pattern = r'([0-9.,]+)\s*[km]?\s*(?:followers|follower|seguaci)'
    matches = re.findall(pattern, text)
    
    if not matches:
        return None
        
    best_estimate = 0
    for match in matches:
        num_str = match.replace(',', '.')
        multiplier = 1
        if 'k' in text[text.find(match):text.find(match)+15]:
            multiplier = 1000
        elif 'm' in text[text.find(match):text.find(match)+15]:
            multiplier = 1000000
            
        try:
            val = float(num_str) * multiplier
            if val > best_estimate:
                best_estimate = val
        except ValueError:
            continue
            
    return best_estimate if best_estimate > 0 else None

def search_influencers():
    queries = [
        'site:instagram.com "@gmail.com" "comico" OR "risate" OR "scherzi" italy',
        'site:instagram.com "@gmail.com" "intrattenimento" OR "stand up" italy',
        'site:tiktok.com "@gmail.com" "comico" OR "divertente" italy',
        'site:tiktok.com "@gmail.com" "scherzi" OR "risate" italy',
        'site:instagram.com "creator" "@gmail.com" "milano" OR "roma" comedy',
        'site:instagram.com "ugc" "@gmail.com" italy'
    ]
    
    results = []
    seen_urls = set()
    
    with DDGS() as ddgs:
        for query in queries:
            print(f"Searching: {query}")
            try:
                search_results = ddgs.text(query, max_results=40)
                for res in search_results:
                    url = res.get('href', '')
                    title = res.get('title', '')
                    snippet = res.get('body', '')
                    
                    if url in seen_urls:
                        continue
                        
                    # Find email
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet + " " + title)
                    email = email_match.group(0) if email_match else None
                    
                    if not email:
                        continue
                        
                    # Filter junk URLs
                    if any(x in url.lower() for x in ['/p/', '/reel/', '/explore/', '/tags/', '/stories/', '/video/']):
                        continue
                        
                    # Extract username
                    username = ""
                    if 'instagram.com/' in url:
                        m = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', url)
                        if m: username = m.group(1)
                    elif 'tiktok.com/@' in url:
                        m = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', url)
                        if m: username = m.group(1)
                        
                    if not username:
                        continue
                        
                    followers = estimate_followers_from_snippet(snippet, title)
                    
                    # Store candidate
                    results.append({
                        'username': username,
                        'url': url,
                        'email': email,
                        'followers': followers,
                        'snippet': snippet[:100] + "..."
                    })
                    seen_urls.add(url)
                    
            except Exception as e:
                print(f"Query failed: {e}")
            time.sleep(2)
            
    # Filter and categorize
    valid_micro = []
    needs_review = []
    for r in results:
        f = r['followers']
        if f is not None:
            if 10000 <= f <= 300000:
                valid_micro.append(r)
        else:
            needs_review.append(r)
            
    print(f"\nFound {len(valid_micro)} valid micro-influencers (estimated 10k-300k).")
    print(f"Found {len(needs_review)} potential influencers (unknown followers).")
    
    with open('robust_dork_results.md', 'w') as f:
        f.write("# Valid Micro-Influencers (10k-300k)\n")
        f.write("| Username | URL | Email | Est. Followers | Snippet |\n")
        f.write("|---|---|---|---|---|\n")
        for m in valid_micro:
            f.write(f"| {m['username']} | [Link]({m['url']}) | {m['email']} | {m['followers']} | {m['snippet']} |\n")
            
        f.write("\n# Needs Follower Count Review\n")
        f.write("| Username | URL | Email | Snippet |\n")
        f.write("|---|---|---|---|\n")
        for m in needs_review:
            f.write(f"| {m['username']} | [Link]({m['url']}) | {m['email']} | {m['snippet']} |\n")

if __name__ == "__main__":
    search_influencers()

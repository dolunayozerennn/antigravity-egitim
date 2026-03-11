import re
import json
import csv
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse

def extract_profiles_from_bing(query):
    print(f"Searching Bing: {query}")
    results = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&count=30"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Iterate over search result blocks
        for li in soup.find_all('li', class_='b_algo'):
            link_tag = li.find('a')
            snippet_tag = li.find('div', class_='b_caption') or li.find('p')
            
            if not link_tag or not snippet_tag:
                continue
                
            clean_link = link_tag.get('href', '')
            snippet = snippet_tag.get_text()
            
            match = re.search(r'instagram\.com/([a-zA-Z0-9_\.]+)/?', clean_link)
            if match:
                username = match.group(1)
                # Exclude common paths
                if username.lower() in ['p', 'reel', 'reels', 'tv', 'explore', 'tags', 'stories']:
                    continue
                
                # Check for email in snippet
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                email = email_match.group(0) if email_match else None
                
                if email:
                    results.append({
                        'username': username,
                        'url': f"https://instagram.com/{username}",
                        'email': email,
                        'snippet': snippet.strip()
                    })
    except Exception as e:
        print(f"Search error: {e}")
        
    return results

queries = [
    'site:instagram.com ("ugc" OR "comedy" OR "skit" OR "divertente") ("italia" OR "milano" OR "roma") "@gmail.com" -"stand up" -"actor" -"attrice"',
    'site:instagram.com "ugc creator" "italia" "@gmail.com" -"agency" -"business"',
    'site:instagram.com "video ironici" "italia" "@gmail.com"',
    'site:instagram.com "commedia" "@gmail.com" ("milano" OR "roma" OR "napoli")',
    'site:instagram.com "vita di coppia" "@gmail.com" "italia"',
    'site:instagram.com ("ragazza italiana" OR "ragazzo italiano") "divertente" "@gmail.com"'
]

all_creators = []
seen_usernames = set()
# Blacklists from previous iterations to pre-filter
USERNAME_BLACKLIST = [
    "memes", "meme", "pagina", "ufficiale", "official", "quote", "citazioni", "frasi",
    "the_irony", "dailymemes", "crazy", "funniest", "laugh", "lol", "laughing", "humor", "humour",
    "standup", "actor", "actress", "attore", "attrice", "teatro", "cinema", "film", "movie",
    "tv", "show", "radio", "podcast", "news", "notizie", "magazine", "media",
    "agency", "management", "business", "company", "srl", "spa", "brand", "shop", "store",
    "luxury", "million", "billion", "rich", "wealth", "yacht", "lifestyle", "photographer"
]

print("Starting Google Dorking Scraper...")
for q in queries:
    found = extract_profiles_from_bing(q)
    for creator in found:
        uname = creator['username'].lower()
        if uname not in seen_usernames:
            # Check blacklist
            if not any(word in uname for word in USERNAME_BLACKLIST):
                seen_usernames.add(uname)
                all_creators.append(creator)
    time.sleep(3) # Be nice to the search engine

print(f"\nFound {len(all_creators)} potential UGC creators with emails.")

# Save directly to tracking markdown format for user review
with open('dork_results.md', 'w') as f:
    f.write("# Dorking Results - Unverified Creators\n\n")
    f.write("| Creator Username | Profile Link | Email | Snippet Info |\n")
    f.write("| :--- | :--- | :--- | :--- |\n")
    for c in all_creators:
        snippet_text = str(c['snippet']).replace('\n', ' ')[:100]
        f.write(f"| **{c['username']}** | [{c['username']}]({c['url']}) | {c['email']} | {snippet_text}... |\n")

print("Results saved to dork_results.md")

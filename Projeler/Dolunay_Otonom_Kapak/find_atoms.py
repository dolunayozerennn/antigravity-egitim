import os
import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv('/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env')

token = os.getenv('NOTION_SOCIAL_TOKEN')
if not token:
    token = os.getenv('NOTION_API_TOKEN')

db_reels = os.getenv('NOTION_DB_REELS_KAPAK')
db_yt = os.getenv('NOTION_DB_YOUTUBE_ISBIRLIKLERI')

def search_notion(db_id, title_prop):
    url = f'https://api.notion.com/v1/databases/{db_id}/query'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Notion-Version': '2022-06-28'}
    payload = {'filter': {'property': title_prop, 'title': {'contains': 'Atoms'}}}
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if 'results' not in data:
        print("Error:", data)
    return data.get('results', [])

print("Searching Reels...")
reels_res = search_notion(db_reels, 'Name')
for r in reels_res:
    title = r['properties']['Name']['title'][0]['plain_text'] if r['properties']['Name']['title'] else ''
    status = r['properties']['Status']['select']['name'] if r['properties']['Status']['select'] else ''
    print(f"Reels: {title} | Status: {status} | ID: {r['id']}")

print("Searching YouTube...")
yt_res = search_notion(db_yt, 'Video Adı')
for r in yt_res:
    title = r['properties']['Video Adı']['title'][0]['plain_text'] if r['properties']['Video Adı']['title'] else ''
    status = r['properties']['Durum']['select']['name'] if r['properties']['Durum']['select'] else ''
    print(f"YouTube: {title} | Status: {status} | ID: {r['id']}")

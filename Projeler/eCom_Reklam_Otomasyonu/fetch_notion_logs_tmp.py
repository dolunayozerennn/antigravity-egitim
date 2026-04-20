import os
import requests
import json
import sys

env_path = "/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k] = v.strip('"\'')

token = os.environ.get("NOTION_API_TOKEN")
db_id = os.environ.get("NOTION_DB_ECOM_REKLAM", "33f95514-0a32-8146-9cad-dbe66f07b15e")

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

payload = {
    "sorts": [{"timestamp": "created_time", "direction": "descending"}],
    "page_size": 3
}

res = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers, json=payload)
data = res.json()

if res.status_code != 200:
    print(f"Error querying Notion API_TOKEN: {res.status_code} {res.text}")
    print("Trying NOTION_SOCIAL_TOKEN instead...")
    token = os.environ.get("NOTION_SOCIAL_TOKEN")
    headers["Authorization"] = f"Bearer {token}"
    res = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers, json=payload)
    data = res.json()
    if res.status_code != 200:
        print(f"Error querying Notion SOCIAL_TOKEN: {res.status_code} {res.text}")
        sys.exit(1)

for r in data.get('results', []):
    props = r.get('properties', {})
    print("-------------")
    for k, v in props.items():
        if v['type'] == 'title':
            val = v['title'][0]['text']['content'] if v['title'] else ""
            print(f"{k}: {val}")
        elif v['type'] == 'rich_text':
            val = v['rich_text'][0]['text']['content'] if v['rich_text'] else ""
            print(f"{k}: {val}")
        elif v['type'] == 'select':
            val = v['select']['name'] if v['select'] else ""
            print(f"{k}: {val}")
        elif v['type'] == 'date':
            val = v['date']['start'] if v.get('date') else ""
            print(f"{k}: {val}")
        elif v['type'] == 'url':
            val = v['url'] if 'url' in v and v['url'] else ""
            print(f"{k}: {val}")
        elif v['type'] == 'checkbox':
            print(f"{k}: {v['checkbox']}")
        elif v['type'] == 'status':
            val = v['status']['name'] if v['status'] else ""
            print(f"{k}: {val}")
        else:
            print(f"{k}: (type {v['type']})")

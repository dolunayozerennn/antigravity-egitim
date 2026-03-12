import os
import json
import urllib.request
import ssl
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Load env
env_path = Path("../../_knowledge/credentials/master.env")
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k] = v.strip('"\' ')

NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN")
NOTION_DATABASE_ID = "31226924bb82800e9adad6f16399eba0"

def get_recent_duplicates():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    
    # Using UTC time threshold just before the run (10:39 TS = 07:39 UTC)
    # Give it a margin: 07:30:00Z
    payload = {
        "page_size": 100,
        "filter": {
            "property": "Eklendi",
            "created_time": {
                "on_or_after": "2026-03-12T07:30:00Z"
            }
        }
    }
    
    page_ids = []
    has_more = True
    start_cursor = None
    
    while has_more:
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {NOTION_API_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                data = json.loads(response.read().decode("utf-8"))
                for result in data.get("results", []):
                    page_ids.append(result["id"])
                
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
        except Exception as e:
            print(f"Error fetching from Notion: {e}")
            break
            
    print(f"Found {len(page_ids)} recently created items.")
    return page_ids

def delete_pages(page_ids):
    count = 0
    for pid in page_ids:
        url = f"https://api.notion.com/v1/pages/{pid}"
        req = urllib.request.Request(
            url,
            data=json.dumps({"archived": True}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {NOTION_API_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            method="PATCH"
        )
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                count += 1
                if count % 10 == 0:
                    print(f"Archived {count}/{len(page_ids)}")
        except Exception as e:
            print(f"Error archiving {pid}: {e}")
            
    print(f"Done. Archived {count} pages.")

if __name__ == "__main__":
    ids = get_recent_duplicates()
    if ids:
        delete_pages(ids)

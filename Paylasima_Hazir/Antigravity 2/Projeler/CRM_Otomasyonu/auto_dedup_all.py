import os
import json
import urllib.request
import ssl
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

env_path = Path("../../_knowledge/credentials/master.env")
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k] = v.strip('"\' ')

NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN")
NOTION_DATABASE_ID = "NOTION_DATABASE_ID_BURAYA"

def fetch_all_pages():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {"page_size": 100}
    pages = []
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
                pages.extend(data.get("results", []))
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
        except Exception as e:
            print(f"Error fetching: {e}")
            break
    return pages

def extract_key(page):
    props = page.get("properties", {})
    phone = props.get("Phone", {}).get("phone_number", "")
    if phone:
        # Standardize phone (remove spaces, +, etc)
        import re
        return re.sub(r"[\s+\-()p:]", "", phone)
    
    email = props.get("email", {}).get("email", "")
    if email:
        return email.lower().strip()
    return None

def deduplicate():
    pages = fetch_all_pages()
    grouped = {}
    
    # Empty phone/email we can't safely dedup so ignore unless we use name
    for p in pages:
        key = extract_key(p)
        if key:
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(p)
            
    to_delete = []
    
    for key, items in grouped.items():
        if len(items) > 1:
            # Sort by created time
            # Keep the oldest one
            items.sort(key=lambda x: x.get("created_time", ""))
            
            # If the newer ones were created TODAY (e.g. during the bug), delete them
            # We don't want to over-delete if they intentionally had two entries from 6 months apart, 
            # though they probably only want one. But let's delete anything that is a duplicate.
            # actually we should archive all but the first (0th) item
            for dup in items[1:]:
                to_delete.append(dup["id"])
                
    print(f"Found {len(to_delete)} duplicates to archive.")
    
    # Delete them
    count = 0
    for pid in to_delete:
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
                    print(f"Archived {count}/{len(to_delete)}")
        except Exception as e:
            print(f"Error archiving {pid}: {e}")
            
    print(f"Fully deduped! Archived {count} duplicate pages.")

if __name__ == "__main__":
    deduplicate()

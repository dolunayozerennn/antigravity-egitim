import os
import requests
import json

old_id = "33f95514-0a32-8146-9cad-dbe66f07b15e"
new_id = "33f955140a328041932edfb0ef84a890"

token = os.environ.get("NOTION_API_TOKEN") or os.environ.get("NOTION_SOCIAL_TOKEN")
if not token:
    raise ValueError("NOTION_SOCIAL_TOKEN missing")
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def check_id(target_id):
    print(f"Checking {target_id}...")
    
    # Try as database
    res = requests.get(f"https://api.notion.com/v1/databases/{target_id}", headers=headers)
    if res.status_code == 200:
        print(f"  -> It is a DATABASE. Title: {res.json().get('title', [{}])[0].get('plain_text', '')}")
        return True
    
    # Try as page
    res2 = requests.get(f"https://api.notion.com/v1/pages/{target_id}", headers=headers)
    if res2.status_code == 200:
        print(f"  -> It is a PAGE.")
        
        # If it's a page, let's list blocks to find the inline database
        res_blocks = requests.get(f"https://api.notion.com/v1/blocks/{target_id}/children", headers=headers)
        if res_blocks.status_code == 200:
            for block in res_blocks.json().get('results', []):
                if block['type'] == 'child_database':
                    print(f"     -> FOUND INLINE DB INSIDE PAGE: ID = {block['id']}, Title = {block['child_database']['title']}")
        return True
    
    print(f"  -> Failed. Status db: {res.status_code}, page: {res2.status_code}")
    print(res.text)
    return False

check_id(old_id)
check_id(new_id)


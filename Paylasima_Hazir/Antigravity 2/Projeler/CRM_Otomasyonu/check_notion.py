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
NOTION_DATABASE_ID = "NOTION_DATABASE_ID_BURAYA"

def get_latest_notion_entries():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    
    payload = {
        "page_size": 20,
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ]
    }
    
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
                props = result.get("properties", {})
                
                # İsim
                name_prop = props.get("İsim", {})
                name = name_prop.get("title", [{}])[0].get("plain_text", "") if name_prop.get("title") else "İsim Yok"
                
                # Phone
                phone_prop = props.get("Phone", {})
                phone = phone_prop.get("phone_number", "") if phone_prop.get("phone_number") else ""
                
                # email
                email = props.get("email", {}).get("email", "")
                
                # Bütçe
                budget = props.get("Bütçe", {}).get("select", {})
                budget_name = budget.get("name", "") if budget else ""
                
                print(f"isim: {name} | tel: {phone} | e-posta: {email} | bütçe: {budget_name}")
                
    except Exception as e:
        print(f"Error fetching from Notion: {e}")

if __name__ == "__main__":
    get_latest_notion_entries()

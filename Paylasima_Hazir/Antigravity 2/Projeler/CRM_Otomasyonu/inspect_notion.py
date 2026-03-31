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

def inspect_database_schema():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {NOTION_API_TOKEN}",
            "Notion-Version": "2022-06-28"
        },
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode("utf-8"))
            props = data.get("properties", {})
            for key in props:
                print(f"Prop '{key}' -> type: {props[key].get('type')}")
                
    except Exception as e:
        print(f"Error fetching from Notion: {e}")

if __name__ == "__main__":
    inspect_database_schema()

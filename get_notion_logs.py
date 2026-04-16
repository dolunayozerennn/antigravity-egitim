import urllib.request
import json
import ssl

import os
token = os.environ.get("NOTION_API_TOKEN") or os.environ.get("NOTION_SOCIAL_TOKEN")
if not token:
    raise ValueError("Missing NOTION API TOKEN")
db_id = "33f95514-0a32-813d-819e-d8de281aea48" # NOTION_DB_YOUTUBE_OTOMASYON

# Fetch recent entries
url = f"https://api.notion.com/v1/databases/{db_id}/query"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
data = json.dumps({"sorts": [{"timestamp": "created_time", "direction": "descending"}], "page_size": 10}).encode()

req = urllib.request.Request(url, data=data, headers=headers)
context = ssl._create_unverified_context()

try:
    with urllib.request.urlopen(req, context=context) as response:
        res = json.loads(response.read().decode())
        
        for result in res.get("results", []):
            props = result.get("properties", {})
            title_prop = props.get("Topic", {})
            title = ""
            if title_prop.get("title"):
                title = title_prop["title"][0].get("plain_text", "")
            
            status_prop = props.get("Status", {})
            status = status_prop.get("status", {}).get("name", "") if "status" in status_prop else ""
            if not status and "select" in status_prop and status_prop["select"]:
                status = status_prop["select"].get("name", "")
                
            error_prop = props.get("Error Message", {})
            error = ""
            if "rich_text" in error_prop and error_prop["rich_text"]:
                error = error_prop["rich_text"][0].get("plain_text", "")
                
            vid_prop = props.get("Video URL", {})
            vid = ""
            if "url" in vid_prop and vid_prop["url"]:
                vid = vid_prop["url"]
                
            created_time = result.get("created_time", "")
            print(f"[{created_time}] Topic: {title} | Status: {status} | Error: {error} | Video: {vid}")
            
except Exception as e:
    print(f"Failed: {e}")

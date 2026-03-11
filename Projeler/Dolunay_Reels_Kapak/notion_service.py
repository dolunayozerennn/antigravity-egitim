import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def get_page_content(page_id: str) -> str:
    """
    Fetches the blocks of a Notion page and extracts all text content 
    to be used as the video script context.
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    # We use requests directly for simplicity and robustness
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return ""
            
        data = response.json()
        script_text = ""
        
        for block in data.get("results", []):
            block_type = block.get("type")
            if block_type in block:
                rich_text = block[block_type].get("rich_text", [])
                for text_item in rich_text:
                    script_text += text_item.get("plain_text", "")
                script_text += "\n"
        
        return script_text.strip()
    except Exception as e:
        print(f"Error fetching page content for {page_id}: {e}")
        return ""

def get_ready_videos():
    """
    Fetches videos from the Notion database that have their status set to 'Çekildi - Edit YOK'.
    """
    if not NOTION_TOKEN or not DATABASE_ID:
        print("Notion Token or Database ID is missing. Check .env")
        return []

    print(f"Querying Notion database: {DATABASE_ID} for 'Çekildi - Edit YOK' videos...")
    try:
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        payload = {
            "filter": {
                "property": "Status",
                "select": {
                    "equals": "Çekildi - Edit YOK"
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Error querying Notion API: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        results = data.get("results", [])
        videos = []
        
        for item in results:
            props = item.get("properties", {})
            
            # This extracts the title/name. Property name might need adjustment based on the DB.
            name_prop = props.get("Name", {}).get("title", [])
            name = name_prop[0].get("plain_text", "Unknown Video") if name_prop else "Unknown Video"
            
            # Extract Drive URL (Update property name 'Drive' if different in user's DB)
            drive_url = props.get("Drive", {}).get("url", "")
            
            # Extract the page content (script)
            script_text = get_page_content(item["id"])

            videos.append({
                "id": item["id"],
                "name": name,
                "drive_url": drive_url,
                "script_text": script_text
            })
            
        print(f"Found {len(videos)} videos ready for cover generation.")
        return videos

    except Exception as e:
        print(f"Exception querying Notion API: {e}")
        return []

if __name__ == "__main__":
    ready_videos = get_ready_videos()
    print(json.dumps(ready_videos, indent=2, ensure_ascii=False))

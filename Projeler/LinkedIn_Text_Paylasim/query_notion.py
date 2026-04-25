import os
import requests
from dotenv import load_dotenv

env_path = "/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env"
load_dotenv(env_path)

token = os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")
db_id = "33095514-0a32-81b4-858a-ff81a77b6d48"

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

payload = {
    "filter": {
        "property": "Project",
        "select": {
            "equals": "LinkedIn_Text_Paylasim"
        }
    },
    "sorts": [
        {
            "property": "Zaman",
            "direction": "descending"
        }
    ],
    "page_size": 20
}

response = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers, json=payload)
data = response.json()

for result in data.get("results", []):
    props = result.get("properties", {})
    
    title = props.get("Title", {}).get("title", [{}])
    title_text = title[0].get("plain_text", "") if title else ""
    
    level = props.get("Level", {}).get("select", {})
    level_text = level.get("name", "") if level else ""
    
    component = props.get("Component", {}).get("select", {})
    component_text = component.get("name", "") if component else ""
    
    zaman = props.get("Zaman", {}).get("date", {})
    zaman_text = zaman.get("start", "") if zaman else ""
    
    message = props.get("Message", {}).get("rich_text", [{}])
    message_text = message[0].get("plain_text", "") if message else ""
    
    details = props.get("Details", {}).get("rich_text", [{}])
    details_text = details[0].get("plain_text", "") if details else ""
    
    print(f"[{zaman_text}] [{level_text}] [{component_text}] {title_text}: {message_text}")
    if details_text:
        print(f"Details: {details_text}")

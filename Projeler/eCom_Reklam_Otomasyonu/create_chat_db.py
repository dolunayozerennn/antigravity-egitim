import os
import requests
import json

NOTION_SOCIAL_TOKEN = os.environ.get("NOTION_SOCIAL_TOKEN")
if not NOTION_SOCIAL_TOKEN:
    raise ValueError("NOTION_SOCIAL_TOKEN missing")
PAGE_ID = "33f95514-0a32-8041-932e-dfb0ef84a890"
url = "https://api.notion.com/v1/databases"

headers = {
    "Authorization": f"Bearer {NOTION_SOCIAL_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

data = {
    "parent": {
        "type": "page_id",
        "page_id": PAGE_ID
    },
    "title": [
        {
            "type": "text",
            "text": {
                "content": "E-Com Reklam Otomasyonu - Chat Hafızası"
            }
        }
    ],
    "properties": {
        "Session ID": {
            "title": {}
        },
        "Kullanıcı Mesajı": {
            "rich_text": {}
        },
        "Bot Yanıtı": {
            "rich_text": {}
        },
        "Bot": {
            "select": {
                "options": [
                    {
                        "name": "E-Com Bot",
                        "color": "blue"
                    }
                ]
            }
        },
        "Tarih": {
            "created_time": {}
        }
    }
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print(f"Database created successfully!")
    print(f"Database ID: {response.json()['id']}")
else:
    print(f"Failed to create database. Status code: {response.status_code}")
    print(response.text)

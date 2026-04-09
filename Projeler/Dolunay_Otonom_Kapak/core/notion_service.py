import os
import json
import requests
import re
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_knowledge", "credentials", "master.env"))

def get_config(cover_type: str) -> dict:
    if cover_type == "reels":
        return {
            "token": os.getenv("NOTION_SOCIAL_TOKEN") or os.getenv("NOTION_API_TOKEN") or os.getenv("NOTION_TOKEN"),
            "db_id": os.getenv("NOTION_DB_REELS_KAPAK", os.getenv("NOTION_DATABASE_ID")),
            "title_prop": "Name",
            "status_prop": "Status",
            "ready_status": "Çekildi - Edit YOK",
            "drive_prop": "Drive",
            "panel_title": "📸 REELS KAPAK REVİZYON PANELİ"
        }
    elif cover_type == "youtube":
        return {
            "token": os.getenv("NOTION_SOCIAL_TOKEN") or os.getenv("NOTION_API_TOKEN") or os.getenv("NOTION_TOKEN"),
            "db_id": os.getenv("NOTION_DB_YOUTUBE_ISBIRLIKLERI", os.getenv("NOTION_DATABASE_ID")),
            "title_prop": "Video Adı",
            "status_prop": "Durum",
            "ready_status": "Çekildi",
            "drive_prop": "Drive",
            "panel_title": "🎬 YOUTUBE KAPAK REVİZYON PANELİ"
        }
    else:
        raise ValueError("Invalid cover type. Use 'reels' or 'youtube'.")

def get_page_content(page_id: str, token: str) -> str:
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
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

def get_ready_videos(cover_type: str) -> list:
    cfg = get_config(cover_type)
    token = cfg["token"]
    db_id = cfg["db_id"]

    if not token or not db_id:
        print(f"[{cover_type.upper()}] Notion Token or Database ID is missing.")
        return []

    print(f"[{cover_type.upper()}] Querying database: {db_id} for '{cfg['ready_status']}' videos...")
    try:
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        payload = {
            "filter": {
                "property": cfg["status_prop"],
                "select": {
                    "equals": cfg["ready_status"]
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"Error querying Notion API: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        results = data.get("results", [])
        videos = []
        
        for item in results:
            props = item.get("properties", {})
            name_prop = props.get(cfg["title_prop"], {}).get("title", [])
            name = name_prop[0].get("plain_text", "Unknown Video") if name_prop else "Unknown Video"
            drive_url = props.get(cfg["drive_prop"], {}).get("url", "")
            script_text = get_page_content(item["id"], token)

            videos.append({
                "id": item["id"],
                "name": name,
                "drive_url": drive_url,
                "script_text": script_text
            })
            
        print(f"Found {len(videos)} ready videos.")
        return videos

    except Exception as e:
        print(f"Exception querying Notion API: {e}")
        return []

def _build_revision_blocks(themes_with_links: list, panel_title: str) -> list:
    blocks = []
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": panel_title}}]
        }
    })
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": "Aşağıdaki kapakları inceleyip, revize etmek istediğin kapağın "}, "annotations": {"color": "gray"}},
                {"type": "text", "text": {"content": "✏️ Revize:"}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": " satırına feedback yaz. Antigravity bu feedback'i okuyup görseli revize edecek."}, "annotations": {"color": "gray"}},
            ]
        }
    })
    
    for theme in themes_with_links:
        t_idx = theme["theme_index"]
        t_name = theme.get("theme_name", f"theme{t_idx}")
        cover_text = theme.get("cover_text", "?")
        drive_links = theme.get("drive_links", [])
        
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"🎨 Tema {t_idx} ({t_name}) — \"{cover_text}\""}}
                ]
            }
        })
        
        link_parts = []
        for dl in drive_links:
            variant = dl.get("variant", "?")
            url = dl.get("url", "")
            if url:
                link_parts.append({"type": "text", "text": {"content": f"V{variant}", "link": {"url": url}}, "annotations": {"bold": True, "color": "blue"}})
                link_parts.append({"type": "text", "text": {"content": "  |  "}})
        
        if link_parts and link_parts[-1]["text"]["content"] == "  |  ":
            link_parts.pop()
        
        link_parts.insert(0, {"type": "text", "text": {"content": "📎 Kapaklar: "}})
        
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": link_parts}})
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "✏️ Revize: "}, "annotations": {"bold": True, "color": "orange"}},
                ]
            }
        })
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}})
    
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def add_revision_panel(cover_type: str, page_id: str, themes_with_links: list) -> bool:
    cfg = get_config(cover_type)
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    blocks = _build_revision_blocks(themes_with_links, cfg["panel_title"])
    
    try:
        response = requests.patch(url, headers=headers, json={"children": blocks}, timeout=30)
        if response.status_code == 200:
            print(f"✅ [{cover_type.upper()}] Revizyon paneli eklendi: {page_id}")
            return True
        else:
            print(f"❌ Revizyon paneli eklenemedi: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Revizyon paneli ekleme hatası: {e}")
        return False

def read_revision_feedback(cover_type: str, page_id: str) -> list:
    cfg = get_config(cover_type)
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Notion blokları okunamadı: {response.status_code}")
            return []
        
        blocks = response.json().get("results", [])
        feedbacks = []
        i = 0
        while i < len(blocks):
            block = blocks[i]
            if block.get("type") == "heading_3":
                heading_text = "".join([rt.get("plain_text", "") for rt in block.get("heading_3", {}).get("rich_text", [])])
                if heading_text.startswith("🎨 Tema"):
                    match = re.match(r'🎨 Tema (\d+) \((\w+)\) — "(.+)"', heading_text)
                    if match:
                        theme_index = int(match.group(1))
                        theme_name = match.group(2)
                        cover_text = match.group(3)
                    else:
                        theme_index, theme_name, cover_text = 0, "unknown", heading_text
                    
                    drive_links, feedback_text, feedback_block_id = [], "", None
                    j = i + 1
                    while j < len(blocks) and j <= i + 4:
                        next_block = blocks[j]
                        if next_block.get("type") == "paragraph":
                            para_text = "".join([rt.get("plain_text", "") for rt in next_block.get("paragraph", {}).get("rich_text", [])])
                            if "📎 Kapaklar:" in para_text:
                                for rt in next_block.get("paragraph", {}).get("rich_text", []):
                                    link = rt.get("text", {}).get("link")
                                    if link and link.get("url"):
                                        drive_links.append(link["url"])
                            if "✏️ Revize:" in para_text:
                                feedback_block_id = next_block["id"]
                                raw_feedback = para_text.replace("✏️ Revize:", "").strip()
                                if raw_feedback and not raw_feedback.startswith("✅") and not raw_feedback.startswith("⚠️"):
                                    feedback_text = raw_feedback
                        j += 1
                    
                    if feedback_text:
                        feedbacks.append({
                            "theme_index": theme_index,
                            "theme_name": theme_name,
                            "cover_text": cover_text,
                            "feedback": feedback_text,
                            "drive_links": drive_links,
                            "block_id": feedback_block_id,
                        })
            i += 1
        return feedbacks
    except Exception as e:
        print(f"❌ Feedback okuma hatası: {e}")
        return []

def update_feedback_block(cover_type: str, block_id: str, new_text: str, is_error: bool = False) -> bool:
    cfg = get_config(cover_type)
    url = f"https://api.notion.com/v1/blocks/{block_id}"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    prefix_text = "⚠️ HATA: " if is_error else "✅ Revize tamamlandı — "
    prefix_color = "red" if is_error else "green"
    
    payload = {
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": prefix_text}, "annotations": {"bold": True, "color": prefix_color}},
                {"type": "text", "text": {"content": new_text}},
            ]
        }
    }
    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Feedback bloğu güncellenemedi: {e}")
        return False

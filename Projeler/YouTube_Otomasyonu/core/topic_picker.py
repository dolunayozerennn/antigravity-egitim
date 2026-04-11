"""
Konu Seçici — topics.json'dan rastgele konu seçer.
Son N üretimi tekrar etmemek için basit dedup mantığı uygular.
"""
import json
import random
import os
from logger import get_logger

log = get_logger("TopicPicker")

TOPICS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "topics.json")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".topic_history.json")
MAX_HISTORY = 5  # Son 5 konuyu tekrarlama


def load_topics() -> dict:
    """topics.json dosyasını yükler."""
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    log.info(f"📚 {len(data['topics'])} konu yüklendi (niş: {data['channel_niche']})")
    return data


def load_history() -> list:
    """Geçmiş konu ID'lerini yükler."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history: list):
    """Geçmiş konu ID'lerini kaydeder."""
    # Son MAX_HISTORY kaydı tut
    trimmed = history[-MAX_HISTORY:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(trimmed, f)


def pick_topic() -> dict:
    """
    Rastgele bir konu seçer, son kullanılanları atlar.
    
    Returns:
        dict: Seçilen konu objesi (id, category, description, style_hints vb.)
    """
    data = load_topics()
    topics = data["topics"]
    history = load_history()

    # Son kullanılan konuları filtrele
    available = [t for t in topics if t["id"] not in history]

    # Eğer tüm konular kullanıldıysa, geçmişi sıfırla
    if not available:
        log.info("🔄 Tüm konular kullanıldı, geçmiş sıfırlanıyor...")
        history = []
        available = topics

    # Rastgele seç
    selected = random.choice(available)

    # Geçmişe ekle
    history.append(selected["id"])
    save_history(history)

    log.info(f"🎯 Konu seçildi: [{selected['id']}] {selected['category']} — {selected['title_hint']}")

    # Channel niche ve default style bilgisini de ekle
    selected["channel_niche"] = data["channel_niche"]
    selected["default_style"] = data["default_style"]

    return selected

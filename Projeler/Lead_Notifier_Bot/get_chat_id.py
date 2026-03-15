import os
import requests
from config import Config

def get_latest_chat_id():
    """Telegram botuna gelen en son mesajın CHAT_ID'sini bulur."""
    token = Config.TELEGRAM_BOT_TOKEN
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN yapılandırmadan bulunamadı.")
        return
        
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("ok"):
            print(f"❌ Telegram API Hata Döndürdü: {data}")
            return
            
        results = data.get("result", [])
        if not results:
            print("📭 Hiç yeni mesaj bulunamadı.")
            print("Lütfen önce Telegram botunuza cihazınızdan herhangi bir mesaj (ör. /start veya 'merhaba') gönderin.")
            print("Bunu yaptıktan sonra bu betiği bir daha çalıştırın.")
            return
            
        # En sonuncu mesajin detayları:
        last_item = results[-1]
        
        if "message" in last_item:
            chat_info = last_item["message"]["chat"]
            chat_id = chat_info["id"]
            title_or_name = chat_info.get("title", chat_info.get("first_name", "Bilinmeyen Başlık"))
            
            print("✅ BAŞARILI: En güncel mesaj bulundu.")
            print("-" * 40)
            print(f"Chat Adı / Başlığı: {title_or_name}")
            print(f"TELEGRAM_CHAT_ID: {chat_id}")
            print("-" * 40)
            print("💡 Bu numarayı .env veya environment variables içerisine kopyalayabilirsiniz.")
        else:
            print("Kanal mesajı (channel_post) veya farklı bir update türü gelmiş olabilir. Son veri:")
            print(last_item)
            
    except Exception as e:
        print(f"❌ Ağa Bağlanamadı: {e}")

if __name__ == "__main__":
    get_latest_chat_id()

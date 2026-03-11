import os
import sys
import json
from dotenv import load_dotenv

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# sys.path ayarlaması ki src modülleri bulunabilsin
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.apollo import ApolloClient
from src.services.hunter import HunterClient

def test_apollo():
    apollo = ApolloClient()
    hunter = HunterClient()

    if not apollo.api_key:
        print("HATA: Apollo API anahtarı (.env) bulunamadı!")
        return
        
    if not hunter.api_key:
        print("HATA: Hunter API anahtarı (.env) bulunamadı!")
        return

    # Senaryo Parametreleri:
    # Lokasyon: New York, New Jersey, Chicago
    # Sektör/Konsept: Fast food, fine dine, cafe, bakery
    # Pozisyon: Owner, Founder, Purchasing, Procurement (Ambalaj alımına karar verecek profiller)
    
    query = {
        "person_titles": ["Owner", "Founder", "Co-Founder", "Purchasing Manager", "Procurement Manager", "Supply Chain Manager", "General Manager", "Director of Operations"],
        "person_locations": ["New York, NY", "New Jersey, US", "Chicago, IL"],
        "q_organization_keyword_tags": ["fast food", "restaurant", "cafe", "bakery", "fine dining", "food and beverage"],
        "per_page": 10
    }

    print("Senaryo Parametrelerine Göre Apollo'da Arama Yapılıyor:\n", json.dumps(query, indent=2, ensure_ascii=False))
    
    people = apollo.search_people(query)
    
    print(f"\nApollo'dan {len(people)} kişi bulundu. Hunter ile doğrulamaları yapılıyor...\n")
    
    results = []
    
    for i, person in enumerate(people, 1):
        email = person.get("email")
        isim = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
        sirket = person.get("organization", {}).get("name", "Bilinmiyor")
        pozisyon = person.get("title", "Bilinmiyor")
        
        if not email:
            print(f"{i}. [E-POSTA BULUNAMADI] {isim} - {sirket} ({pozisyon})")
            continue
            
        print(f"{i}. [DOĞRULANIYOR...] {email} ({isim} - {sirket})")
        
        # Hunter verification (Eğer hunter limitinize takılmazsa)
        status = hunter.verify_email(email)
        
        results.append({
            "Ad Soyad": isim,
            "Sirket": sirket,
            "Pozisyon": pozisyon,
            "Email": email,
            "Dogrulama": status,
            "LinkedIn": person.get("linkedin_url", "")
        })
        
    print("\n" + "="*50)
    print("🎯 TOPLANAN LEAD'LER (DOĞRULANMIŞ)")
    print("="*50)
    
    for r in results:
        dogrulama_icon = "✅" if r['Dogrulama'] in ["deliverable", "valid"] else "⚠️" if r['Dogrulama'] in ["risky", "accept_all"] else "❌"
        print(f"👤 {r['Ad Soyad']} | {r['Pozisyon']}")
        print(f"🏢 {r['Sirket']}")
        print(f"📧 {r['Email']} {dogrulama_icon} ({r['Dogrulama']})")
        if r['LinkedIn']:
            print(f"🔗 {r['LinkedIn']}")
        print("-" * 30)

if __name__ == "__main__":
    test_apollo()

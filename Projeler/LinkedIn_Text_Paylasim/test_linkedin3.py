import os
import requests
from config import settings

text = """İçerik üretiminin zorluklarını unutun! 🎉

Yeni geliştirdiğim 'Yapay Zeka Destekli LinkedIn Paylaşım Asistanı' ile sadece tek bir tıklamayla,
hem profesyonel bir makale hem de dikkat çekici bir görsel oluşturup, anında paylaşabilirsiniz.

Sistem nasıl çalışıyor?
1️⃣ Ben sadece konuyu "merhaba" diye yazıyorum.
2️⃣ Yapay zeka asistanı devreye girip SEO uyumlu, ilgi çekici bir metin oluşturuyor.
3️⃣ Ardından, metne uygun harika bir görsel üretiyor.
4️⃣ Ve tek tıkla LinkedIn'de yayında! 🚀

Bu sayede saatlerce içerik düşünmek, görsel tasarlamak veya metin düzenlemek yerine enerjimi asıl işime odaklayabiliyorum.

Eğer siz de içerik üretim süreçlerinizi otomatikleştirmek ve profesyonel paylaşımlar yapmak isterseniz, bu asistan tam size göre!

Detaylar için bana mesaj atabilirsiniz. 📩

#YapayZeka #AI #İçerikÜretimi #Otomasyon #LinkedInAsistanı #DijitalPazarlama #SEO"""

url = f"https://api.linkedin.com/rest/posts"
headers = {
    "Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202503",
    "X-Restli-Protocol-Version": "2.0.0",
}

# 1. TEXT ONLY POST
payload = {
    "author": settings.LINKEDIN_PERSON_URN,
    "commentary": text,
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False,
}
print("TESTING LINKEDIN POST...")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print("STATUS:", resp.status_code)
    print("BODY:", resp.text)
except Exception as e:
    print("ERROR:", e)

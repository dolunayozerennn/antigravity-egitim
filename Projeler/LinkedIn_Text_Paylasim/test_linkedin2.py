import os
import json
import requests
from config import settings

text = """İçerik üretiminin zorluklarını unutun! 🎉

Yeni geliştirdiğim 'Yapay Zeka Destekli LinkedIn Paylaşım Asistanı' ile sadece tek bir tıklamayla, 
hem profesyonel bir makale hem de dikkat çekici bir görsel oluşturup, anında paylaşabilirsiniz.

Sistem nasıl çalışıyor?
1️⃣ Ben sadece konuyu "merhaba" diye yazıyorum."""

url = f"https://api.linkedin.com/rest/posts"
headers = {
    "Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202503",
    "X-Restli-Protocol-Version": "2.0.0",
}
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
resp = requests.post(url, headers=headers, json=payload)
print(resp.status_code)
print(resp.text)

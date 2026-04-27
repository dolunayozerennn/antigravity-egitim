import json
text = """İçerik üretiminin zorluklarını unutun! 🎉

Yeni geliştirdiğim 'Yapay Zeka Destekli LinkedIn Paylaşım Asistanı' ile sadece tek bir tıklamayla, 
hem profesyonel bir makale hem de dikkat çekici bir görsel oluşturup, anında paylaşabilirsiniz.

Sistem nasıl çalışıyor?
1️⃣ Ben sadece konuyu "merhaba" diye yazıyorum"""

payload = {
    "author": "urn:li:person:123",
    "commentary": text,
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False,
    "content": {
        "media": {
            "title": text[:100],
            "id": "urn:li:image:456"
        }
    }
}
print(json.dumps(payload, indent=2, ensure_ascii=False))

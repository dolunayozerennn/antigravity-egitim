"""
Gemini Vision — Supplement Etiket Analiz Motoru
Fotoğrafı alır, Gemini'ye gönderir, JSON sonuç döndürür.
"""

import base64
import json
import re

from google import genai
from google.genai import types

from logger import get_logger

log = get_logger("gemini_analyzer")

# ── Yapılandırılmış çıkarma prompt'u ──
SUPPLEMENT_ANALYSIS_PROMPT = """
Sen bir profesyonel ürün etiketi analizcisisin. Sana verilen fotoğrafta bir takviye edici gıda,
vitamin, supplement veya benzeri bir ürünün etiketi/ambalajı görünüyor.

Görevin: Fotoğraftaki TÜM bilgileri titizlikle oku ve aşağıdaki yapılandırılmış formatta çıkar.

## ÇIKARILACAK BİLGİLER:

### 1. ÜRÜN BİLGİSİ
- Ürün adı (tam isim)
- Marka
- Ürün türü (tablet, kapsül, toz, sıvı vb.)
- Porsiyon büyüklüğü (serving size)
- Toplam porsiyon/servis sayısı

### 2. İÇERİK TABLOSU (Supplement Facts / Besin Değerleri)
Her bir madde için:
- Madde adı (Türkçe ve varsa İngilizce)
- Miktar (mg, mcg, IU vb.)
- %BRD / %DV (Beslenme Referans Değeri / Daily Value)

Bu tabloyu eksiksiz ve düzgün formatlanmış olarak ver.

### 3. BİLEŞİM (Ingredients)
Tüm bileşenleri virgülle ayrılmış liste olarak ver.

### 4. KULLANIM ÖNERİSİ
- Önerilen kullanım şekli
- Günlük doz
- Kullanım koşulları/uyarıları

### 5. DİĞER BİLGİLER
- Üretici firma adı/adresi
- Sertifikalar (GMP, Halal, ISO vb.)
- Saklama koşulları
- Son kullanma tarihi (görünüyorsa)
- Barkod numarası (görünüyorsa)

## KURALLAR:
1. SADECE fotoğrafta açıkça okunan bilgileri yaz. Tahmin etme, uyarlama.
2. Okunamayan kısımlar için "[okunamadı]" yaz.
3. Fotoğrafta olmayan bölümler için "Bu bilgi fotoğrafta mevcut değil" yaz.
4. Sayısal değerleri tam olarak aktar (birim dahil).
5. Yanıtını Türkçe olarak ver.

## ÇIKTI FORMATI:
Yanıtını aşağıdaki JSON yapısında ver:

```json
{
  "urun_bilgisi": {
    "urun_adi": "",
    "marka": "",
    "urun_turu": "",
    "porsiyon_buyuklugu": "",
    "toplam_porsiyon": ""
  },
  "icerik_tablosu": [
    {
      "madde_adi": "",
      "madde_adi_en": "",
      "miktar": "",
      "birim": "",
      "brd_yuzde": ""
    }
  ],
  "bilesim": "",
  "kullanim_onerisi": {
    "onerilen_kullanim": "",
    "gunluk_doz": "",
    "uyarilar": ""
  },
  "diger_bilgiler": {
    "uretici": "",
    "sertifikalar": [],
    "saklama_kosullari": "",
    "son_kullanma_tarihi": "",
    "barkod": ""
  }
}
```
"""


def extract_json_from_response(text: str) -> dict | None:
    """Gemini yanıtından JSON bloğunu çıkar."""
    # 1. ```json ... ``` bloğu
    json_match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Doğrudan { ... } bloğu
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def analyze_image_bytes(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    model_name: str = "gemini-2.5-flash",
    api_key: str = "",
) -> dict:
    """
    Ham görsel byte'larını Gemini Vision ile analiz et.

    Returns:
        dict: {
            "model": str,
            "raw_text": str,
            "parsed": dict | None,
            "success": bool,
        }
    """
    client = genai.Client(api_key=api_key)

    log.info(f"Analyzing image ({len(image_bytes)} bytes) with {model_name}")

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Content(
                parts=[
                    types.Part(text=SUPPLEMENT_ANALYSIS_PROMPT),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_bytes,
                        )
                    ),
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=8192,
        ),
    )

    raw_text = response.text
    log.info(f"Response length: {len(raw_text)} chars")

    parsed = extract_json_from_response(raw_text)

    return {
        "model": model_name,
        "raw_text": raw_text,
        "parsed": parsed,
        "success": parsed is not None,
    }


def chat_with_gemini(
    message: str,
    api_key: str,
    model_name: str = "gemini-2.5-flash",
) -> str:
    """
    Gemini ile genel sohbet — supplement dışı sorular için.
    """
    client = genai.Client(api_key=api_key)

    system_prompt = """Sen Antigravity ekibinin yardımcı asistanısın. 
Adın "Supplement Buddy". Görevin:
1. Supplement fotoğraflarını analiz etmek (fotoğraf gönderildiğinde otomatik yaparsın)
2. Supplement, vitamin ve sağlık takviyeleri hakkında sorulara yanıt vermek
3. Genel sohbet: kullanıcıya yardımcı ve samimi olmak

Yanıtlarını Türkçe ver. Kısa, öz ve faydalı ol. Emoji kullan."""

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Content(
                parts=[
                    types.Part(text=message),
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2048,
            system_instruction=system_prompt,
        ),
    )

    return response.text

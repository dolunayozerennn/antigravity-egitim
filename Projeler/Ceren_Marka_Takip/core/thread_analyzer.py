"""
Ceren_Marka_Takip — Thread LLM Analizi
=========================================
Groq LLM ile thread'lerin marka işbirliği olup olmadığını analiz eder.
"""

import logging
from typing import Dict, Any, Optional

from services.groq_client import analyze_thread

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Sen bir e-posta thread analiz asistanısın. Sana bir e-posta thread'inin son mesajlarını vereceğim.

Görevin:
1. Bu thread'in bir MARKA İŞBİRLİĞİ ile ilgili olup olmadığını belirle.
   - Marka işbirliği: Bir şirket/marka, bir influencer ile sponsorlu içerik, ürün tanıtımı, 
     reklam, PR paketi, etkinlik daveti vb. konularda iletişim kuruyorsa → marka işbirliği
   - Marka işbirliği DEĞİL: Kişisel e-postalar, haber bültenleri, sipariş onayları, 
     sosyal medya bildirimleri, spam, fatura, banka bildirimleri vb.

2. Thread'in durumunu analiz et.

Önemli bilgi:
- ceren@dolunay.ai = Marka ilişkileri yöneticisi (Ceren)
- dolunay@dolunay.ai = Influencer (Dolunay)
- ozerendolunay@gmail.com = Influencer (Dolunay, alternatif mail)
- Bunların dışındaki e-postalar = Marka / Dış taraf

Yanıtını SADECE aşağıdaki JSON formatında ver. Başka bir şey yazma:

{
  "is_brand_collaboration": true/false,
  "brand_name": "Marka adı veya null",
  "last_sender": "brand" | "ceren" | "dolunay" | "other",
  "action_needed_by_ceren": true/false,
  "reason": "Kısa Türkçe açıklama (max 100 karakter)",
  "thread_status": "active" | "closed" | "waiting_for_brand",
  "urgency": "high" | "medium" | "low"
}

Kurallar:
- "is_brand_collaboration" marka işbirliği ise true, değilse false
- "last_sender" thread'deki SON mesajı kimin attığını belirler
- "action_needed_by_ceren" = true sadece şu durumlarda:
  - Son mesajı marka attıysa VE cevap bekleniyorsa
  - Son mesajı Dolunay attıysa VE Ceren'in haberi olmayabilirse
- "thread_status":
  - "closed" = İşbirliği reddedildi, iptal edildi, veya tamamlandı
  - "waiting_for_brand" = Ceren/Dolunay yazdı, markadan cevap bekleniyor
  - "active" = Devam eden aktif konuşma
- "urgency": high = fiyat/brief bekleyen, medium = genel takip, low = bilgilendirme
"""


def analyze(thread_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Tek bir thread'i LLM ile analiz et.
    
    Args:
        thread_data: gmail_scanner'dan gelen thread bilgisi
    
    Returns:
        Analiz sonucu (LLM çıktısı + thread meta) veya None
    """
    # Mesaj snippet'lerini metin haline getir
    snippets = thread_data.get("message_snippets", [])
    if not snippets:
        logger.debug(f"Thread {thread_data['thread_id']}: snippet yok, atlanıyor")
        return None

    thread_text = f"Konu: {thread_data['subject']}\n"
    thread_text += f"Katılımcılar: {', '.join(thread_data['participants'])}\n"
    thread_text += f"Mesaj sayısı: {thread_data['message_count']}\n"
    thread_text += "\n---\n\n"
    thread_text += "\n\n---\n\n".join(snippets)

    # LLM analiz
    result = analyze_thread(thread_text, SYSTEM_PROMPT)
    
    if result is None:
        logger.warning(f"Thread {thread_data['thread_id']} LLM analizi başarısız")
        return None

    # Thread meta bilgisini sonuca ekle
    result["thread_id"] = thread_data["thread_id"]
    result["subject"] = thread_data["subject"]
    result["gmail_link"] = thread_data["gmail_link"]
    result["last_message_date"] = thread_data["last_message_date"]
    result["last_sender_email"] = thread_data["last_sender_email"]
    result["message_count"] = thread_data["message_count"]

    logger.info(
        f"Thread analiz: '{thread_data['subject'][:50]}' → "
        f"marka={result.get('is_brand_collaboration')}, "
        f"aksiyon={result.get('action_needed_by_ceren')}, "
        f"durum={result.get('thread_status')}"
    )
    return result

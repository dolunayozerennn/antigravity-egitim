from groq import Groq
from logger import get_logger
from config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_report_summary(videos):
    """
    Kisa ve profesyonel bir özet metin olusturur.
    Örnek: Bu hafta Instagram Reels'te 2 video 200K barajını aştı... En iyisi 'Dubai Yatırım Rehberi'.
    """
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY tanimli degil, akilli özet atlanıyor.")
        return ""

    if not videos:
        return "Bu hafta hedeflenen izlenme barajlarını aşan yeni video bulunmamaktadır."

    try:
        import os
        # Eger master.env gibi dosyalarda GROQ_BASE_URL=https://api.groq.com/openai/v1 verilmişse
        # Groq client'i kendi default path'ini eklediğinde url /openai/v1/openai/v1 olarak bozuluyor.
        if "GROQ_BASE_URL" in os.environ:
            del os.environ["GROQ_BASE_URL"]
            
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Videolarla ilgili baglami hazirla
        context_lines = []
        for v in videos:
            context_lines.append(f"- Platform: {v['platform']}, Izlenme: {v['views']}, Tarih: {v['date']}, URL: {v['url']}")
            
        context_text = "\n".join(context_lines)
        
        prompt = f"""
Sen Ceren'e sosyal medya raporu sunan profesyonel ve enerjik bir dijital asistansın.
Aşağıda son 7 günde barajı aşan videoların bilgileri var:

{context_text}

Lütfen yukarıdaki verilere bakarak, Ceren için mailin en başında okunacak 2-3 cümlelik çok kısa, motive edici ve net bir Türkçe özet metin yaz.
Sadece metni döndür, selamlama veya ekstra açıklama yapma. Doğrudan özete gir.
Metin HTML formatında olacak, dolayısıyla kalın yapmak istediğin yerleri <b> ile sarabilirsin.
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_completion_tokens=250,
        )
        
        summary = chat_completion.choices[0].message.content.strip()
        logger.info("Groq ile akilli özet basariyla olusturuldu.")
        return summary
        
    except Exception as e:
        logger.error(f"Groq ile özet uretilirken hata olustu: {e}", exc_info=True)
        return ""

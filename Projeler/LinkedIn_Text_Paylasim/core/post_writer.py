"""
OpenAI gpt-4o-mini ile LinkedIn postu yazma.
n8n'deki "Post Yazarı" node'unun birebir karşılığı.
"""
from ops_logger import get_ops_logger
ops = get_ops_logger("LinkedIn_Text_Paylasim", "PostWriter")
from datetime import datetime
from openai import OpenAI

from config import settings


class PostWriter:
    """gpt-4o-mini kullanarak LinkedIn postu yazar."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def write_weekly_news_post(self, research_content: str) -> str:
        """
        Haftanın AI haberlerinden LinkedIn postu yazar.
        n8n Workflow 1 (LinkedIn Automation) — "Post Yazarı" node'u.
        """
        current_date = datetime.now().isoformat()

        system_message = (
            f"Bu haftanın yapay zeka gelişmeleri: \n{research_content}\n\n"
            f"Date: {current_date}"
        )

        user_message = (
            "Bu haftanın yapay zeka gelişmelerinden en önemli 3 tanesini seçerek kısa bir LinkedIn postu oluştur.\n\n"
            "KURALLAR (KESİNLİKLE UYULACAK):\n"
            "1. Gönderinin toplam uzunluğu KESİNLİKLE MAKSİMUM 500 KARAKTER (harf) olmalıdır. Daha uzun olması YASAKTIR.\n"
            "2. Sadece 3 haber seç ve her haberi SADECE 1 KISA CÜMLE (maksimum 10 kelime) ile madde işareti (-) kullanarak yaz.\n"
            "3. Metni ASLA yarıda kesme, bitmiş ve anlamlı bir şekilde sonlandır.\n"
            "4. YZ yerine AI kısaltmasını kullan.\n"
            "5. Boş giriş veya çıkış cümleleri kullanma ('Hey ağım', 'İşte haberler' vb. YASAK). Direkt haberlere gir.\n"
            "6. Emojileri minimumda tut (maksimum 2 adet).\n\n"
            "Sadece LinkedIn'de paylaşılacak yazıyı çıktı olarak ver. Başka hiçbir açıklama ekleme."
        )

        return self._generate(system_message, user_message)

    def write_weekly_tip_post(self, research_content: str) -> str:
        """
        AI tavsiyesinden LinkedIn postu yazar.
        n8n Workflow 2 (LinkedIn AI Tips) — "Post Yazarı" node'u.
        """
        current_date = datetime.now().isoformat()

        system_message = (
            f"Kullanman için araştırma: {research_content}\n\n"
            f"Date: {current_date}"
        )

        user_message = (
            "İnsanların günlük hayatlarında kullanabilecekleri değerli fakat az bilinen bir AI tavsiyesini LinkedIn postu olarak yaz.\n\n"
            "KURALLAR (KESİNLİKLE UYULACAK):\n"
            "1. Gönderinin toplam uzunluğu KESİNLİKLE MAKSİMUM 500 KARAKTER (harf) olmalıdır. Kesinlikle geçme.\n"
            "2. Çok kısa bir kanca (hook) cümlesiyle başla, ardından doğrudan uygulamanın adını vererek nasıl kullanılacağını 1-2 çok kısa cümle ile açıkla.\n"
            "3. Metni ASLA yarıda kesme, anlamlı bir şekilde bitir.\n"
            "4. YZ yerine AI kısaltmasını kullan.\n"
            "5. Boş giriş veya çıkış cümleleri kullanma ('Hey ağım', 'İşte harika ipucu' vb. YASAK).\n"
            "6. Emojileri minimumda tut (maksimum 2 adet).\n\n"
            "Sadece LinkedIn'de paylaşılacak yazıyı çıktı olarak ver. Başka hiçbir açıklama ekleme."
        )

        return self._generate(system_message, user_message)

    def _generate(self, system_message: str, user_message: str) -> str:
        """gpt-4o-mini ile post üretir."""
        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] gpt-4o-mini post yazma atlanıyor.")
            return "[DRY-RUN] 🚀 Bu hafta AI dünyasında neler oldu?\n\n1. OpenAI yeni modelini tanıttı\n2. Google Gemini güncellendi\n\n#AI #YapayZeka"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=200
            )
            content = response.choices[0].message.content.strip()
            
            # AI'nin yazdığı postu doğrudan döndür, yarım kesilmemesi için karakter kırpmasını kaldırdık.

            ops.info(f"Post yazıldı ({len(content)} karakter)")
            return content
        except Exception as e:
            ops.error(f"GPT-4o-mini post yazma hatası: {e}", exception=e)
            raise

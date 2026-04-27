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
            "Bu haftanın yapay zeka gelişmelerini baz alarak bir LinkedIn postu "
            "oluşturmanı istiyorum. Amacın \"Haftanın en önemli 3 yapay zeka "
            "gelişmesini\" çok kısa bir şekilde paylaşmak. Oluşturduğun LinkedIn postunda orta düzey "
            "bir Türkçe kullanmanı istiyorum. Herkesin anlayabileceği bir bilgi "
            "düzeyinde yazmanı istiyorum. Yazının insansı gözükmesini istiyorum.\n\n"
            "ÇOK ÖNEMLİ: Gönderinin toplam uzunluğu KESİNLİKLE MAKSİMUM 500 karakter (harf) olmalıdır. "
            "Bu yüzden sadece en çarpıcı 3 haberi seç ve her birini sadece 1 kısa cümle (maksimum 10 kelime) ile özetle. "
            "Daha uzun olması KESİNLİKLE YASAKTIR. YZ kısaltması yerine AI kısaltmasını kullan. "
            "Yazıyı ASLA cümlenin veya konunun ortasında yarıda kesme, 3 haberi de çok kısa verip bitir.\n\n"
            "Kolay okunabilmesi için paragraflar, başlıklar ve maddeler arasına mutlaka çift enter atarak (boş bir satır bırakarak) boşluk bırakmayı unutma. \n\n"
            "YASAKLI VE KAÇINILMASI GEREKENLER:\n"
            "- 'Hey ağım', 'Hey network', 'Hey bağlantılarım' gibi girişler YAPMA.\n"
            "- 'İnanılmaz bir haber', 'Büyük bir heyecanla duyuruyorum' gibi abartılı LinkedIn klişelerinden KAÇIN.\n"
            "- 'Dijital dünyada', 'Hızla değişen çağda' gibi boş giriş cümleleri YAZMA. Direkt habere gir.\n"
            "- Çok fazla emoji (🚀, 💡, 🔥) KULLANMA. Maksimum 2-3 emoji.\n\n"
            "Sadece LinkedIn'de paylaşılacak yazıyı çıktı olarak vermeni istiyorum. "
            "Başka hiçbir şey yazmanı istemiyorum."
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
            "Senin görevin, insanların günlük hayatlarında kullanabilecekleri "
            "değerli fakat herkes tarafından bilinmeyen AI tavsiyelerini LinkedIn "
            "postu aracılığı ile paylaşmak. Amacın, bu tavsiyeyi herhangi bir insanın "
            "kolaylıkla hayatına entegre edebilmesi için önce ona bunun neden "
            "değerli olduğunu (yani hook cümlesini) vermen; ardından nasıl hayatına "
            "çok hızlıca, kolayca ve detaya boğmadan entegre edebileceğini göstermek. "
            "Fakat hızlıca ve detaya boğmadan derken, günlük hayatına entegre "
            "edebilmesi için gerekli bir miktarda bilgi de paylaşmak zorundayız. "
            "Yani \"şunu şöyle yap\" demektense, \"şu uygulama üzerinden şöyle yap\" "
            "demek her zaman daha sağlıklı olacaktır; çünkü insanlar genellikle "
            "nereden, neyi ve nasıl yapacaklarını bilmiyorlar. Böylece çok bilinmeyen "
            "AI tavsiyelerini paylaşmış olacağız. \n\n"
            "ÇOK ÖNEMLİ: LinkedIn'de metnin yarıda kesilmemesi için gönderi çok uzun OLMAMALIDIR. "
            "Toplam metni KESİNLİKLE MAKSİMUM 500 karakter civarında tutmaya çalış. Daha uzun olması YASAKTIR. YZ kısaltması "
            "yerine AI kısaltmasını kullan. Konuyu ASLA yarıda kesme, tam ve anlaşılır şekilde bitirip bir kapanış yaptığından emin ol.\n\n"
            "Kolay okunabilmesi için paragraflar, başlıklar ve maddeler arasına mutlaka çift enter atarak (boş bir satır bırakarak) boşluk bırakmayı unutma. \n\n"
            "YASAKLI VE KAÇINILMASI GEREKENLER:\n"
            "- 'Hey ağım', 'Hey bağlantılarım', 'Bugün size harika bir ipucu vereceğim' gibi girişler YAPMA.\n"
            "- 'İnanılmaz', 'Muazzam', 'Devrim niteliğinde' gibi abartılı sıfatlardan KAÇIN.\n"
            "- 'Dijital dünyada', 'Hızla değişen çağda' gibi boş giriş cümleleri YAZMA. Direkt soruna ve çözüme gir.\n"
            "- Çok fazla emoji (🚀, 💡, 🔥) KULLANMA. Maksimum 2-3 emoji.\n\n"
            "Sadece LinkedIn'de paylaşılacak yazıyı çıktı olarak vermeni istiyorum. "
            "Başka hiçbir şey yazmanı istemiyorum."
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
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            ops.info(f"Post yazıldı ({len(content)} karakter)")
            return content
        except Exception as e:
            ops.error(f"GPT-4o-mini post yazma hatası: {e}", exception=e)
            raise

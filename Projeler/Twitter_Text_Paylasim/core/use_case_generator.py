"""B2B AI Kullanım Senaryosu Üretici.

Dolunay'ın "İş süreçlerinde AI nasıl efektif kullanılır?" serisi için.
LLM her seferinde yeni bir senaryo üretir. Stil rehberi: kullanıcının verdiği
3 örnek (MCP+CRM, AI agent+WhatsApp, Claude Code+CRM hatırlatma).

Notion'da son 30 gün üretilen use case'leri okur, çakışma kontrolü yapar
(LLM'e "şunlar zaten yazıldı, farklı senaryo bul" diye verir).
"""

import json

from openai import OpenAI

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "UseCaseGenerator")


STYLE_GUIDE = """Stil rehberi (örnek senaryolar — bu üçünü tekrar etme, başka senaryo bul):

1. **MCP + CRM**: MCP diye bir teknoloji var; CRM'inizi Claude'a bağlamanızı
sağlıyor. Böylece Claude ile chatleşerek CRM kullanabilirsiniz. Örnek: "Bu hafta
en çok hangi ürün satıldı?" diye sorabilirsiniz, otomatik raporlar.

2. **Şirket Dokümanları + AI Agent + WhatsApp**: Müşterilerinizin sürekli sorduğu
sorular şirket dokümanlarında varsa, bunları bir AI ajanın erişimine verirsiniz.
Bu ajanı WhatsApp hattına bağlarsınız. Müşteriniz mesaj atar, ajan dokümanlardan
cevap üretir, sizi rahatsız etmez.

3. **Claude Code + CRM Otomasyonu**: Satış ekibiniz müşterileri geri aramıyorsa,
hiç kod bilmeden Claude Code ile CRM'inize otomasyon yazdırabilirsiniz. Sistem
(a) satışçılara hatırlatma atar, (b) yapmazlarsa size raporlar.

ORTAK ÖRÜNTÜ:
- Hedef kitle: KOBİ sahipleri, satış/pazarlama yöneticileri, iş süreçleriyle
  uğraşan çalışanlar. Yazılımcı DEĞİL.
- Konu: AI'la spesifik bir iş ağrısının nasıl çözüldüğü.
- Dil: Sıradan, jargon yok. "API endpoint", "deployment" gibi kelimeler yasak.
"""


class UseCaseGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_new_use_case(self, recent_titles: list[str] | None = None) -> dict:
        """Yeni bir senaryo üretir. Returns: {title, scenario, takeaway}."""
        recent = recent_titles or []
        recent_str = "\n".join(f"- {t}" for t in recent[:20]) if recent else "(yok)"

        system = (
            STYLE_GUIDE
            + "\n\nGörev: KOBİ / iş süreçleri için yeni bir AI kullanım senaryosu üret. "
            "Yukarıdaki 3 örnek + son 30 günde paylaşılanları TEKRAR ETME. "
            "Çıktı JSON formatında olsun:\n"
            '{\n'
            '  "title": "kısa senaryo adı (max 60 char)",\n'
            '  "scenario": "1-2 cümlelik problem + çözüm açıklaması (Türkçe, sade)",\n'
            '  "takeaway": "1 cümle: kim için, ne zaman değer katar"\n'
            '}'
        )
        user = f"""Son 30 günde paylaşılan use case'ler (bunları TEKRAR ETME):
{recent_str}

Yeni bir senaryo üret. Stil rehberindeki 3 örneği de tekrar etme."""

        try:
            r = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.85,
                max_tokens=600,
            )
            data = json.loads(r.choices[0].message.content)
            ops.info(f"Use case üretildi: {data.get('title','?')[:60]}")
            return data
        except Exception as e:
            ops.error("Use case üretme hatası", exception=e)
            return {}

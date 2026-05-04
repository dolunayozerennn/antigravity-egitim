"""B2B AI Kullanım Senaryosu Üretici (v3 — gold-standard rehberi).

Dolunay'ın "İş süreçlerinde AI nasıl efektif kullanılır?" serisi için.
Her seferinde yeni bir senaryo üretir; çıktı yapısı tweet_writer.write_for_use_case'in
beklediği `{title, hook, problem, steps, tools, outcome}` formatı.

Notion'da son 30 gün üretilen use case'leri okur, çakışma kontrolü yapar.

v3 değişikliği: STYLE_GUIDE Dolunay'ın 4 gold-standard hook + somut adım örneğiyle
yeniden yazıldı. Üretim hook + numaralı adımlar + ölçülebilir sonuç odaklı.
"""

import json

from openai import OpenAI

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "UseCaseGenerator")


STYLE_GUIDE = """STIL REHBERI (Dolunay'ın gold-standard'ı — bunları TEKRAR ETME, bu kalitede yenisini bul):

═══ ÖRNEK 1 — Somut sayı + provoke ═══
Hook: "Instagram'ınızı personelinizin yönetme maliyeti ayda 10.000 TL."
Problem: KOBİ sahibi sosyal medya yönetimi için pahalı personel tutuyor; çoğunlukla
düzensiz ve düşük kaliteli içerik üretiliyor.
Adımlar:
  1. ManyChat / Make.com gibi otomasyon platformuna giriş yap.
  2. Instagram DM'lerini otomatik AI yanıtlama akışı kur (örnek prompt: "Müşteri sıkça
     sorduğu: fiyat, lokasyon, randevu sorularını şu formatta yanıtla …")
  3. Haftada 1 kez AI ile içerik takvimi üret.
Araçlar: ManyChat, Make.com, Claude Desktop
Sonuç: Personel maliyeti 10K TL → ~500 TL araç ücreti.

═══ ÖRNEK 2 — Ters köşe + sayı ═══
Hook: "10 dakikada bu yöntemle müşteri şikayetlerini 5 kat düşürün."
Problem: İnternette yapılan olumsuz yorumlar gözden kaçıyor; itibar yönetimi
geciktikçe potansiyel müşteri kaybediliyor.
Adımlar:
  1. Claude Desktop indir, Pro paketi ($20) al.
  2. Code sekmesine gir, şu prompt'ı yapıştır: "Benim işletmemin adı [İŞLETME ADI].
     İnternette hakkımda yapılan olumsuz bütün yorumların otomatik analiz edilip bana
     haftada bir mail atıldığı bir otomasyon kurmak istiyorum."
  3. Claude Code otomasyonu inşa eder; haftalık özet mailini bekle.
Araçlar: Claude Desktop, Claude Code
Sonuç: Şikayetlere 7 gün içinde geri dönüş; çözülen olumsuz yorum oranı 5×.

═══ ÖRNEK 3 — Tarihsel analoji ═══
Hook: "Sanayi devriminde makine satın alan fabrikatörle insan çalıştıran fabrikatör
yarışabilir mi? Bugün AI'da aynı kırılma noktasındayız."
Problem: Rakipler süreçlerini AI ile otomatikleştirip maliyetlerini düşürürken, geleneksel
işletmeler aynı işi insanla yapıp marjlarını eritiyor.
Adımlar:
  1. Şu hafta tek bir tekrarlayan operasyon seç (rapor üretimi, fatura kesimi, mail
     yanıtlama gibi).
  2. Claude Code'a aç, şu prompt'ı yaz: "Şu süreç [SÜREÇ AÇIKLAMASI] otomatik çalışsın."
  3. Bir hafta gözlem yap — kazanılan saati ölç.
Araçlar: Claude Code
Sonuç: 1 süreç başına haftalık 4-8 saat tasarruf.

═══ ÖRNEK 4 — Şaşırtıcı iddia ═══
Hook: "Ekiplerinizin gerçekten çalışıp çalışmadığını bilmiyorsunuz."
Problem: Satış / operasyon ekipleri raporlarını kendisi yazıyor; gerçek aktivite
verisi (aramalar, takipler, geri dönüşler) görünmüyor.
Adımlar:
  1. CRM'inize MCP ile Claude'ı bağla (örnek: HubSpot MCP).
  2. Claude'a sor: "Bu hafta hangi satışçı kaç müşteri aradı? Geri dönüş oranı?"
  3. Hatırlatma akışı kur: "Müşteriyi 3 gün içinde aramayan satışçıya WhatsApp at."
Araçlar: Claude Desktop, MCP, HubSpot/Pipedrive
Sonuç: Aktivite görünürlüğü %100; geri dönüş oranı 2×.

═══ ORTAK ÖRÜNTÜ ═══
- Hedef kitle: KOBİ sahipleri, satış/pazarlama yöneticileri, iş süreçleriyle uğraşan
  çalışanlar. Yazılımcı DEĞİL.
- Konu: AI'la spesifik bir iş ağrısının nasıl çözüldüğü.
- HOOK ZORUNLU: somut sayı / ters köşe / tarihsel analoji / şaşırtıcı iddia.
- Adımlar SOMUT: araç adı + Türkçe örnek prompt + ölçülebilir sonuç.
- Dil: sıradan, jargon yok ("API endpoint", "deployment" yasak).
- Aşikar tavsiye YASAK: "AI iletişimi kolaylaştırır", "geri bildirim önemlidir" gibi
  kitlenin zaten bildiği cümleler.
"""


class UseCaseGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_new_use_case(self, recent_titles: list[str] | None = None) -> dict:
        """Yeni bir senaryo üretir.
        Returns: {title, hook, problem, steps[], tools[], outcome}
        Eski uyumluluk için scenario+takeaway de doldurulur.
        """
        recent = recent_titles or []
        recent_str = "\n".join(f"- {t}" for t in recent[:20]) if recent else "(yok)"

        system = (
            STYLE_GUIDE
            + "\n\nGörev: KOBİ / iş süreçleri için yeni bir AI kullanım senaryosu üret. "
            "Yukarıdaki 4 örnek + son 30 günde paylaşılanları TEKRAR ETME. "
            "Aşikar / kitlenin zaten bildiği bir tavsiye verme.\n\n"
            "Çıktı JSON formatı:\n"
            '{\n'
            '  "title": "kısa senaryo adı (max 60 char)",\n'
            '  "hook": "1 cümlelik vurucu açılış (somut sayı / ters köşe / analoji / şaşırtıcı iddia)",\n'
            '  "problem": "1-2 cümle: kitlenin yaşadığı somut ağrı",\n'
            '  "steps": ["1. adım (araç + örnek prompt)", "2. adım", "3. adım"],\n'
            '  "tools": ["Claude Desktop", "Make.com", ...],\n'
            '  "outcome": "1 cümle: ölçülebilir sonuç (zaman/maliyet/oran)",\n'
            '  "scenario": "(uyumluluk) problem + adımların 1-2 cümle özeti",\n'
            '  "takeaway": "(uyumluluk) kim için, ne zaman değer katar — 1 cümle"\n'
            '}'
        )
        user = f"""Son 30 günde paylaşılan use case'ler (bunları TEKRAR ETME):
{recent_str}

Yukarıdaki 4 gold-standard örneği de TEKRAR ETME. Yeni bir KOBİ ağrısı + spesifik AI çözümü.
Hook, somut adımlar, araç adları ve ölçülebilir sonuç ZORUNLU."""

        try:
            r = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.85,
                max_tokens=1200,
            )
            data = json.loads(r.choices[0].message.content)
            ops.info(f"Use case üretildi: {data.get('title','?')[:60]}")
            return data
        except Exception as e:
            ops.error("Use case üretme hatası", exception=e)
            return {}

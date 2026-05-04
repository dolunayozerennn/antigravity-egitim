"""Perplexity Researcher — X-uygun AI haber özeti.

LinkedIn'deki uzun haber formatından farklı: X için kısa, somut, taktik odaklı
tek bir haber çekiyoruz (en güçlüsü). LLM later puanlayacak, geçmezse atlanır.
"""

from datetime import datetime

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "PerplexityResearcher")


class PerplexityResearcher:
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = settings.PERPLEXITY_BASE_URL
        self.model = "sonar"

    def research_x_news(self) -> str:
        """X için uygun, somut, son 3-5 günde çıkmış 1 AI haberi."""
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = f"""Bugün: {today}.

Son 3-5 gün içinde yayınlanmış, yapay zeka / AI agent / otomasyon dünyasından
TEK BİR önemli haber bul. Şu kritere uysun:

- Türkçe konuşan AI/otomasyon geliştirici kitlesi için pratik değer taşımalı
- Somut bir sayı, ürün adı, sürüm veya yetenek içermeli
- "AI gelecek" tarzı vizyon haberi DEĞİL, gerçek bir lansman/güncelleme/sonuç
- Tercihen yeni bir model, tool, açık kaynak proje, framework güncellemesi

ÇIKTI FORMATI (sade Türkçe, 200-400 kelime):
- Başlık: kısa, net
- Ne oldu: 2-3 cümle
- Kim için önemli + neden: 2-3 cümle
- Bir somut detay (sayı / fiyat / yetenek): 1-2 cümle
- Kaynak URL'si

Tek bir haber, en güçlüsünü seç."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
        }
        try:
            r = requests.post(f"{self.base_url}/chat/completions",
                            headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            ops.info("Perplexity araştırma tamam", f"{len(content)} karakter")
            return content
        except Exception as e:
            ops.error("Perplexity araştırma hatası", exception=e)
            return ""

    def research_b2b_use_case(self, recent_titles: list[str] | None = None) -> str:
        """Use Case generator için kaliteli kaynak: gerçek dünyadan KOBİ AI otomasyon
        örnekleri. Çıktı, use_case_generator'a girdi olarak geçer ki LLM kafasından
        senaryo uydurmasın — somut, doğrulanmış araç adları + akışlar üzerinden üretsin.
        """
        recent = recent_titles or []
        recent_str = "\n".join(f"- {t}" for t in recent[:15]) if recent else "(yok)"

        prompt = f"""KOBİ sahipleri ve iş süreçleri yöneticileri için, son 6-12 ayda
yayınlanmış GERÇEK ve UYGULANABİLİR yapay zeka / otomasyon kullanım örneklerinden
2 farklı senaryo bul. Neil Patel, HubSpot, Make.com blog, Zapier blog, Reforge,
First Round Review, ya da güvenilir AI/otomasyon kaynaklarından beslen.

Kriterler:
- KOBİ veya küçük ekip için uygulanabilir (büyük enterprise senaryosu DEĞİL)
- Kullanılan araç adı NET (Claude Desktop / ChatGPT / Make.com / ManyChat / Zapier / n8n /
  HubSpot / Pipedrive gibi gerçek araçlar — uydurma araç adı YOK)
- Somut bir akış var (girdi → AI → çıktı)
- Ölçülebilir bir sonuç var (kazanılan saat, düşürülen maliyet, artan oran)
- Aşağıdaki başlıklarla ÇAKIŞMASIN (bunlar son 30 günde işlendi):
{recent_str}

ÇIKTI FORMATI (sade Türkçe, 350-600 kelime, 2 senaryo):

SENARYO 1:
- Başlık: kısa
- Hedef kitle: hangi tip işletme (örn. "muayenehane", "küçük e-ticaret")
- Problem: 1-2 cümle, somut ağrı
- Akış (numaralı): araç adı + ne yaptığı + örnek kullanım
- Sonuç: ölçülebilir (saat / TL / oran)
- Kaynak URL: [varsa link]

SENARYO 2:
(Aynı şablon, farklı domain)

Önemli: araç özelliği veya yetenek UYDURMA. Emin değilsen jenerik kal.
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2500,
        }
        try:
            r = requests.post(f"{self.base_url}/chat/completions",
                            headers=headers, json=payload, timeout=90)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            ops.info("Perplexity B2B use case araştırma tamam", f"{len(content)} karakter")
            return content
        except Exception as e:
            ops.error("Perplexity B2B araştırma hatası", exception=e)
            return ""

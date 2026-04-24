# Antigravity Node Architecture (ANA) - Providers

Bu dizin, sistem genelindeki dış API entegrasyonlarının (Supabase, LinkedIn, Meta, Groq, vb.) merkezi, hataya dayanıklı (fault-tolerant) sarmalayıcı node modüllerini içerir.

## 🧱 ANA Standartları ZORUNLULUKLARI

Nisan 2026 itibarıyla herhangi bir Antigravity projesi dış bir servise veya bir veritabanına istek yapacağında sıfırdan `requests` kullanmaz. Bu klasör altında yer alan **Provider (Node)** yapılarını kullanır.

Bu Node'ların barındırması gereken ZORUNLU standartlar şunlardır:

1. **Exponential Retry:** Ağ hataları ve 5xx (500/502) Gateway hatalarına karşı `ana_retry_and_catch` kullanılarak (veya \`tenacity\` ile) en az 3 defa artan aralıklarla (exponential backoff) tekrar atılacak.
2. **Timeout:** Bütün HTTP isteklerinde kesinlikle bir `timeout` (ör: `timeout=10` veya max 30) parametresi olacaktır.
3. **Observable Catch:** Düz bir `Exception` yerine `🚨 [Node Adı] API Hatası: {detay}` şeklinde spesifik ve izlenebilir formatta hatalar loğlanacaktır.
4. **Fallback / Graceful Degradation:** Servis hiç cevap vermezse ana işlemler durdurulmaz. Mantıklı bir Fallback (B Planı) geliştirilir (Örn: Loglama yapılıyorsa ve DB ulaşılamıyorsa JSONL metin dosyasına yaz, resim upload servisi uçmuşsa sadece metin gönder vb.)
5. **Raw Payload Desteği (Shadow / Kıyamet Testi Modu):** Çökmelerin simüle edilebilmesi ve mock testler çalıştırılabilmesi için, eğer hata verirse/vermek üzereyse isteğin RAW JSON halinin (`raw_payload`) sisteme/loglara iz bırakması sağlanır.

## Örnek Kullanım

```python
from _skills.providers.supabase_logger import SupabaseLoggerNode

# Node örneği oluşturulur
logger_node = SupabaseLoggerNode(supabase_url="...", supabase_key="...")

# Ana akışı kilitlemeyen 'safe' metodlar çağrılır
logger_node.safe_log(
    project_name="eCom_Reklam",
    status="HATA",
    message="Telegram API limit aşıldı",
    details={"try_count": 5},
    raw_payload={"update_id": 12345, "message": {"text": "hello"}}
)
```

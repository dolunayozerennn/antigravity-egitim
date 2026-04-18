# Mimari Audit ve Sistem Analizi Workflow'u ( `/mimari-audit` )

Bu workflow, Antigravity AI tarafından otonom olarak çalıştırılarak bir projenin veri yapısını, loglama kalitesini, kalıcı durum (persistence) altyapısını ve genel hata toleransını analiz etmek için kullanılır.

**Kullanım:** `/mimari-audit [Proje_Dizini_Veya_Proje_Adı]`

---

## 🏗️ Adım 1: Keşif ve Kontekst Çıkarma
Kullanıcı bu komutu çağırdığında, hedef projenin kod yapısını anlamak için şu adımları izle:
1. `list_dir` ile hedef projenin ana dizinini analiz et.
2. `view_file` ile projenin çalışmasını kontrol eden ana kod dosyalarını (`main.py`, `app.js`, `config.py`, `services/` vb.) oku.
3. Özellikle verinin depolandığı, kullanıcı konuşmalarının işlendiği ve dış API çağrılarının yapıldığı dosyaları hedef al.

## 🕵️ Adım 2: Kritik Mimari Analiz Noktaları
Kod okumalarını tamamladıktan sonra, bir "Mimar" gözüyle şu 4 ana kategoride değerlendirme yap:

### 1. Durum Kalıcılığı (State Persistence)
- **Problem:** Chat geçmişi, kullanıcı oturumları veya işlem durumları Python `dict()` listeleri gibi ram üzerinde, "uçucu hafızada" mı tutuluyor? Program kapanıp açılsa veri uçar mı?
- **Beklenen:** Notion, Google Sheets, SQLite veya kalıcı bir disk JSON'una state'in yazılıyor olması.

### 2. Olay Loglaması ve İzlenebilirlik (Event Logging)
- **Problem:** Kritik transaction'lar sadece konsola `print()` ile mi atılıyor? Örneğin bir "chat konuşması" dışarıdan bir kaynaktan ulaşılabilir şekilde loglanıyor mu ("Geçmiş konuşmalarda ne dedi?" kontrol edilebiliyor mu)?
- **Beklenen:** Tüm ana business lojiklerinin ve konuşmaların okunabilir bir kalıcı log kaynağına düşmesi (`NotionLogger` vb).

### 3. Hata Toleransı & Retry Mekanizması (Fault Tolerance)
- **Problem:** API istekleri 500 dönerse sistem tamamen patlıyor mu? Gönderilemeyen veya failed olan görevler sonsuza kadar siliniyor mu?
- **Beklenen:** Global `try...except`, rate limit gecikmeleri (`time.sleep` callback'leri, backoff) ve failed işler için bir "Dead Letter" yapısının varlığı. 

### 4. Modülerlik & Standartlara Uyum
- İş mantığı (Business Logic) ile API entegrasyonları iç içe mi? (Spagetti mi?)

## 📊 Adım 3: Raporlama ve Düzeltme Puanlaması (KODA DOKUNMA)
Bulguları sentezleyerek kullanıcıya detaylı bir **Mimari Audit Raporu** sun (Örnek başlıklar: Mimar Puanı 6/10, Mevcut Durum, Anti-Patternler). Bu raporda "Düzeltme Planını" (Mimari Blueprint) çok net bir şekilde madde madde belirt.

*Örnek: "1. App'in State'i uçucu hafızada tutuluyor. Notion üzerinde yepyeni bir State-Table kurmalı ve NotionService'e geçmiş çekme fonksiyonu eklemeliyiz. 2. Loglama için... vs."*

## 🚀 Adım 4: Mimar Modu ve Onay 
Raporu sunduktan sonra kullanıcıya sor:
> *"Sistemdeki mimari zayıflıkları ve çözüm planımı sundum. Planı onaylıyorsan, kod yapısını loglama/persistence standartlarına uygun olarak refaktör etmeye başlayabilirim. Onaylıyor musun?"*

## 🛠️ Adım 5: Uygulama ve Self-Review (SADECE ONAY SONRASI)
Kullanıcı "Evet, uygula" veya "Planı şöyle değiştirerek uygula" dediğinde sırasıyla:
1. Planda belirtilen özellikleri (örneğin yeni veritabanı loglayıcısı entegrasyonu, retry modülü) tek tek ekle.
2. Entegreden sonra `/degisiklik-kontrol` ve `/self-review` workflow'larını tetikleyerek değişikliğin projeyi bozmadığını teyit et.

---
**AI TALİMATI:** Bu komut çağrıldığında bu dosyayı okuduğunu kullanıcıya belirt, dizini analiz et, raporu bas ve onaysız kesinlikle kodları doğrudan editleyip mimariyi değiştirme.

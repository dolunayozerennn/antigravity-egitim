---
description: Sub-Agent Prompt — Büyük görevleri alt chat'lere bölmek için kusursuz promptlar hazırlar
---

# Sub-Agent Prompt Workflow

Bu workflow, büyük görevleri izole "Sub-Agent" chat'lere devretmek için gereken **kusursuz promptları** hazırlar.

## Ne Zaman Kullanılmalı?
- Mimar chat'te (ana chat) analiz tamamlandığında ve çözüm yolu netleştiğinde.
- Görev birden fazla alt parçaya bölünüyorsa ve bunların yeni chat'lerde yapılması gerekiyorsa.
- `[Kullanıcı]: /sub-agent-prompt` komutu ile tetiklenir.

## Adımlar (AI İçin Talimatlar)

1. **İş Akışını Belirle (Paralel vs Sıralı):** Görevleri bölerken, bu görevlerin aynı anda (paralel) yapılıp yapılamayacağını veya birinin bitmesinin diğerini bekleyip beklemediğini (sıralı) netleştir. Bunu kullanıcıya açıkça bildir.
2. **Kısa ve Benzersiz Chat İsimleri:** Kullanıcının (ID veya URL göremediği için) chat'leri kolayca bulabilmesi adına kısa, öz ve ayırt edici isimler belirle (Örn: `WA_Onb_1`). Promptun en başında yapay zekaya bu ismi chat adı olarak ayarlaması için kesin talimat ver.
3. **Kapsamı Daralt:** Hangi dosyaların (tam yolları ile) değiştirileceğini ve hangilerine dokunulmayacağını kesin olarak belirt. Mimarın kararlarını ve V2 prensiplerini prompta dahil et.
4. **Çıktı Formatı:** Kopyalama butonunun UI'da bozulmaması için aşağıdaki kurallara **kesinlikle** uy:

   a) Her promptu **tek bir kopyalanabilir blok** olarak sun.
   b) Prompt içinde kod snippet'leri (javascript, bash, python vb.) varsa → dış fence'i **4 backtick** ( `````text` ) ile aç/kapat. İç snippet'leri normal 3 backtick ile yaz. Bu sayede iç backtick'ler dış bloğu kırmaz.
   c) Prompt içinde kod snippet'i yoksa → normal 3 backtick ( ` ```text ` ) yeterlidir.
   d) **Markdown syntax YASAK:** Prompt metninin içinde `**kalın**`, `` `kod` ``, `### başlık`, `> alıntı` gibi markdown işaretleri KULLANMA. Bunlar text bloğu içinde bile render edilir ve kopyalama butonunu böler. Bunların yerine:
      - Kalın yerine → BÜYÜK HARF veya [BAŞLIK]: formatı
      - Kod/dosya yolu yerine → tırnak içinde düz metin
      - Başlık yerine → numaralı satırlar veya [BÖLÜM] etiketleri
   e) ESKİ/YENİ karşılaştırma bloklarında backtick KULLANMA → tire veya düz metin ile göster.

---

### Çıktı Şablonu (Bu formata birebir uy):

Çalışma Stratejisi: [Bu görevler PARALEL olarak aynı anda farklı chatlerde çalıştırılabilir VEYA SIRALI çalıştırılmalıdır, çünkü...]

````text
CHAT ADI: [Örn: WA_Onb_1]
(Yapay Zeka: Lütfen ilk iş olarak bu chat'in adını tam olarak yukarıdaki isimle değiştir/ayarla)

Sen, "Antigravity V2 Mimari Kuralları"na sıkı sıkıya bağlı bir Uzman Geliştiricisin.
Amacımız: [Görevin kısa tanımı]

[KAPSAMDAKİ DOSYALAR]
- "path/to/file1.py" (Değiştirilecek)
- "path/to/file2.py" (Sadece referans)

[TEKNİK TALİMATLAR — BAŞ MİMARIN KARARLARI]
1. Sadece belirtilen dosyalara odaklan. Çalışan diğer sistemlere dokunma.
2. KESİNLİKLE GitHub'a push yapma veya projeyi deploy (/canli-yayina-al) etme! Değişiklikleri sadece lokalde yap.
3. Değişiklik sonrasında mutlaka syntax doğrulaması yap (örn: node -c veya python -m py_compile).

[GÖREV ADIMLARI]
1. Dosyaları oku ve durumu anla.
2. İstenen değişiklikleri uygula.
3. İşin bittiğinde, aşağıdaki formatta kısa bir özet çıktısı ver (Mimar bu özeti okuyacak):
   [SONUÇ_ÖZETİ]
   - Değişen dosyalar: ...
   - Çözülen mantık: ...
   - (Varsa) Kalan hatalar: ...
   [/SONUÇ_ÖZETİ]
````

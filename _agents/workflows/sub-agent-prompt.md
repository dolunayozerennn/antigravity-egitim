# Sub-Agent Prompt Workflow

Bu workflow, büyük görevleri izole "Sub-Agent" chat'lere devretmek için gereken **kusursuz promptları** hazırlar.

## Ne Zaman Kullanılmalı?
- Mimar chat'te (ana chat) analiz tamamlandığında ve çözüm yolu netleştiğinde.
- Görev birden fazla alt parçaya bölünüyorsa ve bunların yeni chat'lerde yapılması gerekiyorsa.
- `[Kullanıcı]: /sub-agent-prompt` komutu ile tetiklenir.

## Adımlar (AI İçin Talimatlar)

1. **İş Akışını Belirle (Paralel vs Sıralı):** Görevleri bölerken, bu görevlerin aynı anda (paralel) yapılıp yapılamayacağını veya birinin bitmesinin diğerini bekleyip beklemediğini (sıralı) netleştir. Bunu kullanıcıya açıkça bildir.
2. **Kısa ve Benzersiz Chat İsimleri:** Kullanıcının (ID veya URL göremediği için) chat'leri kolayca bulabilmesi adına kısa, öz ve ayırt edici isimler belirle (Örn: `Görev: WA_Onb_1`).
3. **Kapsamı Daralt:** Hangi dosyaların (tam yolları ile) değiştirileceğini ve hangilerine dokunulmayacağını kesin olarak belirt. Mimarın kararlarını ve V2 prensiplerini prompta dahil et.
4. **Çıktı Formatı:** Kopyalama butonunun UI'da bozulmaması için **üretilen her bir promptun tamamını** tek bir ` ```text ` bloğu içine al.

---

### Çıktı Şablonu (Bu formata birebir uy):

**Çalışma Stratejisi:** [Bu görevler PARALEL olarak aynı anda farklı chatlerde çalıştırılabilir VEYA SIRALI çalıştırılmalıdır, çünkü...]

```text
Görev: [Örn: WA_Onb_1]

Sen, "Antigravity V2 Mimari Kuralları"na sıkı sıkıya bağlı bir Uzman Geliştiricisin.
Amacımız: [Görevin kısa tanımı]

**Kapsamındaki Dosyalar:**
- `path/to/file1.py` (Değiştirilecek)
- `path/to/file2.py` (Sadece referans)

**Teknik Talimatlar (Baş Mimarın Kararları):**
1. Sadece belirtilen dosyalara odaklan. Çalışan diğer sistemlere dokunma.
2. 🚨 KESİNLİKLE GitHub'a push yapma veya projeyi deploy (/canli-yayina-al) etme! Değişiklikleri sadece lokalde yap.
3. Değişiklik sonrasında mutlaka syntax doğrulaması (örn: `node -c` veya `python -m py_compile`) yap.

**Görev Adımları:**
1. Dosyaları oku ve durumu anla.
2. İstenen değişiklikleri uygula.
3. İşin bittiğinde, aşağıdaki formatta kısa bir özet çıktısı ver (Mimar bu özeti okuyacak):
   [SONUÇ_ÖZETİ]
   - Değişen dosyalar: ...
   - Çözülen mantık: ...
   - (Varsa) Kalan hatalar: ...
   [/SONUÇ_ÖZETİ]
```

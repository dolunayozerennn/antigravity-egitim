# Sub-Agent Sonuç Workflow

Bu workflow, "Sub-Agent" chat'lerde yapılan işlemlerin sonuçlarını ana mimar chat'e manuel kopyala-yapıştır yapmadan, **otomatik olarak aktarmak** için kullanılır.

## Ne Zaman Kullanılmalı?
- Mimar chat'te dağıtılan görevler alt chat'lerde tamamlandığında.
- Mimar chat'e dönüp tüm yapılan değişiklikleri tek seferde raporlamak ve senkronize etmek istediğinizde.
- `[Kullanıcı]: /sub-agent-sonuc` komutu ile tetiklenir.

## Adımlar (AI İçin Talimatlar)

1. **Gerçeğin Kaynağını (Codebase) Kontrol Et:** Sub-agent'ların yazdığı kodlar *lokalde* olduğu için log okumak yerine doğrudan koda bakmalısın. `run_command` aracıyla çalışma dizininde `git status` ve (gerekirse kısa formatta) `git diff` çalıştır. Bu sana hangi alt chat'in hangi dosyayı değiştirdiğini kesin olarak gösterecektir.
2. **Kısa Log Kontrolü (Opsiyonel):** Eğer kodlarda beklenmedik bir değişiklik (çakışma) görürsen veya sub-agent'ın bir hatada takıldığını düşünürsen:
   - Hafızandaki `<conversation_summaries>` bölümünden sub-agent chat'inin ID'sini (örn: `WA_Onb_1` isminden yola çıkarak) bul.
   - Dosya okuma aracı (`view_file`) baştan okuduğu için uzun dosyalarda kaybolmamak adına bash üzerinden son satırları çek: `run_command` ile `tail -n 100 ~/.gemini/antigravity/brain/<ID>/.system_generated/logs/overview.txt` komutunu kullan. Bu sana alt chat'in bıraktığı son [SONUÇ_ÖZETİ] bloğunu gösterecektir.
3. **Değişiklikleri Sentezle ve Analiz Et:**
   - Hangi alt chat, hangi dosyaları değiştirdi?
   - Chat'ler arasında bir çakışma yaşanmış mı?
   - Alt chat'lerin kodda bıraktığı hata veya yarım kalan bir yer var mı?
4. **Ana Chat'i Güncelle ve Raporla:** 
   - Projenin yeni durumunu kafanda netleştir.
   - Kullanıcıya: *"Kodları (git diff) inceledim. WA_Onb_1 ve WA_Onb_2 görevleri başarıyla X ve Y dosyalarını güncellemiş. Çakışma yok. Sonraki adıma geçebiliriz."* formatında profesyonel ve kısa bir özet sun.

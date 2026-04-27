# MCP ve Tool Kullanımı Optimizasyon Rehberi

> **Kaynak:** LinkedIn Otomasyonu (Multi-Line Post) hata çözümü süreci analiz raporu (27 Nisan 2026).
> Bu rehber, Antigravity ekosisteminde hızı artırmak, token maliyetini düşürmek ve hata oranını minimize etmek için zorunludur.

## 1. Kod Okuma ve Arama Optimizasyonu (ZORUNLU)

*   **Cerrahi Okuma:** Sadece spesifik bir fonksiyon veya değişken aranıyorsa, `view_file` yerine kesinlikle `grep_search` kullanılmalıdır.
*   **Satır Sınırlandırması:** `view_file` kullanılacaksa mutlaka `StartLine` ve `EndLine` parametreleri ile sadece ilgili kod bloğu okunmalıdır. Bütün dosyayı okumak (özellikle büyük dosyalarda) yasaktır.
*   **Gereksiz Okuma Döngülerinden Kaçınma:** Aynı dosyanın farklı aşamalarda tekrar tekrar baştan sona okunması yerine, ilk okumada alınan önemli kısımlar hafızada tutulmalı veya sadece değişen kısımlar okunmalıdır.

## 2. Kod Yazma ve Müdahale Optimizasyonu (ZORUNLU)

*   **Cerrahi Müdahaleler:** Dosyaları baştan yazmak yerine `replace_file_content` (tek blok) veya `multi_replace_file_content` (çoklu blok) araçlarıyla sadece değişen satırlara müdahale edilmelidir.
*   **Doğru Tool Seçimi:** Dosya içeriğini değiştirmek için MCP araçları varken asla `run_command` (sed, echo vb.) kullanılmamalıdır.
*   **Lokal Test (Dry-Run):** Her kod değişikliğinden sonra doğrudan deploy yapmak yerine, lokalde küçük bir test dosyası (`scratch/test.js` veya `scratch/test_api.py`) oluşturulup mantık doğrulanmalıdır.

## 3. Terminal (Command) ve Log Optimizasyonu

*   **Sessiz Mod:** `npm install` veya `pip install` gibi komutlar çalıştırılırken her zaman `--silent` veya `> /dev/null` kullanılarak gereksiz log çıktılarının token tüketmesi engellenmelidir.
*   **Filtrelenmiş Çıktılar:** Terminalden veri çekerken `head -n 20` veya `tail -n 20` gibi filtreler kullanılarak sadece en anlamlı kısımlar işlenmelidir.
*   **Log Analizi:** "200 OK" dönmesi işlemin başarılı olduğu anlamına gelmez. API'nin metni kırpması veya sessiz hata vermesi durumlarına karşı loglar derinlemesine (yüzeysel değil) incelenmelidir.

## 4. Bilgi Bankası ve API Entegrasyonu

*   **Önce Dokümantasyon:** Herhangi bir dış servis (LinkedIn, Notion vb.) entegrasyonu yapılmadan önce deneme-yanılma yapmak yerine `_knowledge` klasöründeki ilgili API notları ve resmi dokümanlar okunmalıdır.
*   **KI (Knowledge Items) Kontrolü:** Varsa daha önce çözülmüş benzer hataların kontrol edilmesi şarttır.

---
*Bu rehber, Antigravity sistem talimatlarının ayrılmaz bir parçasıdır.*

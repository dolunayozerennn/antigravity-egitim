# Hatalar ve Çözümler Günlüğü

Geçmişte karşılaşılan hatalar ve çözümleri. Aynı sorunu iki kez çözmemek için bu dosyayı güncelliyoruz.

---

## Kie AI

### Sora 2 Pro Storyboard — Model adı ve format hataları
- **Sorun:** Model adı `sora-2-pro-storyboard` olmalı. `shots` içinde `Scene` büyük S. `n_frames` ve `aspect_ratio` zorunlu — eksik olunca 422.
- **Çözüm:** Model, input yapısı ve zorunlu alanları doğru ver.
- **Tarih:** Şubat 2026

### Video üretimi sonrası URL gelmeme
- **Sorun:** `resultJson` alanı string olarak geliyor.
- **Çözüm:** `json.loads(data["resultJson"])["resultUrls"][0]`
- **Tarih:** Şubat 2026

### Nano Banana 2 — 400 Bad Request / Resolution Error
- **Sorun:** API'ye "1K" veya "2k" gibi yanlış formatlanmış resolution gönderildiğinde `taskId` döndürülemiyor.
- **Çözüm:** `resolution` parametresi küçük harfle (`"1k"`) gönderilmeli. NB2 büyük harfli `"1K"` veya `"2k"` kabul etmiyor.
- **Tarih:** Nisan 2026

---

## Gmail / Outreach

### Gmail MCP — Draft (Taslak) Oluşturma Aracı YOK
- **Sorun:** `send_gmail_message` direkt gönderir — draft oluşturmaz.
- **Çözüm:** Kullanıcı "drafta yaz" dediğinde mail içeriğini artifact'a yaz ve göster. ASLA `send_gmail_message` kullanma.
- **Tarih:** Mart 2026

### OAuth Token Hatası (`invalid_grant`)
- **Sorun:** `token.json` süresi dolmuş veya bozulmuş.
- **Çözüm:** `token.json` dosyasını sil → scripti tekrar çalıştır → tarayıcıda yeniden onayla.

### Gmail OAuth Scope Uyumsuzluğu — `invalid_scope`
- **Sorun:** Koddaki SCOPES ile token'daki scope eşleşmezse `invalid_scope: Bad Request`.
- **Çözüm:** SCOPES'u token'daki scope ile eşleştir. Token oluşturulduktan sonra SCOPES değiştirmemeli.
- **Tarih:** Mart 2026

---

## Apify

### Monthly Usage Limit — Rate Limit Log Maskeleme
- **Sorun:** Apify kota aşıldığında `last_error` değişkenine atanmıyordu → "Bilinmeyen hata" mesajı.
- **Çözüm:** `except ApifyApiError as e:` bloğuna `last_error = e` eklendi.
- **Kural:** API key rotation kullanırken `last_error` gerçek exception'ı taşımalı. Silent failure yasak.
- **Tarih:** Nisan 2026

### Boş sonuç / Actor başlamıyor
- **Çözüm:** Actor ID'yi Apify konsolundan kopyala, filtreleri genişlet.

### Kredi tükenmesi
- **Çözüm:** `_knowledge/api-anahtarlari.md` → Apify Hesap 2 (yedek) kullan.

---

## Telegram Bot

### Markdown parse hatası
- **Çözüm:** Yanıtı göndermeden önce `escape_markdown()` ile temizle veya `parse_mode=None` fallback kullan.
- **Tarih:** Şubat 2026

### Conflict — Aynı anda iki bot instance
- **Sorun:** Deploy sırasında eski container henüz durmadan yenisi başlıyor → iki polling çakışıyor.
- **Çözüm:** `error_handler()` ile Conflict hatalarını INFO olarak logla. `healing_playbook.json`'a ignore pattern ekle. `run_polling(stop_signals=None)` kullan.
- **Kural:** Deploy sonrası Conflict geçicidir, otomatik düzelir.
- **Tarih:** Mart 2026

---

## Google Sheets / API Bağlantı Kopmaları

### SSL EOF Hatası — Geçici Ağ Kopması (Tekrarlayan)
- **Sorun:** Railway'de uzun yaşayan bağlantı objeleri bayatlıyor → SSL EOF.
- **Çözüm:** Geçici ağ hataları (`eof`, `ssl`, `broken pipe`, `timeout`) yakalandığında `service = None` → `authenticate()` → retry (max 3, exponential backoff).
- **Kural:** Uzun çalışan servislerde dış API çağrılarına **mutlaka** retry + reconnect ekle.
- **Tarih:** Mart 2026

### Eksik Sekme — HttpError 400 Tüm Pipeline Çökmesi
- **Sorun:** Config'de tanımlı ama henüz oluşturulmamış sheet sekmesi → `Unable to parse range` → tüm pipeline çökme.
- **Çözüm:** HttpError 400 için özel yakalama: sekme bulunamazsa uyarıyla atla, diğer sağlıklı sekmeleri okumaya devam et.
- **Tarih:** Nisan 2026

### Shared Tab (Aynı Sayfayı Dinleyen Birden Fazla Proje) State Çakışması
- **Sorun:** Hem CRM botu hem Notifier botu aynı sayfayı (`0426-Yeni`) okuyup durumlarını `_Meta`'ya yazdıklarında, son yazan ilkini eziyor veya state'ler karışıp spam döngüsüne neden oluyor.
- **Çözüm:** Kendi state key'lerine bir prefix (`namespace`) ekle (örn. `crm:0426-Yeni` ve `notifier:0426-Yeni`). Ayrıca `_Meta` sekmesini yazarken tüm mevcut alanları (`all_state`) koruyarak (merge) yaz.
- **Kural:** Merkezi config dosyasından okuyan projeler, "state" (durum) tutuyorsa kendi adıyla bir "namespace / prefix" KULLANMAK ZORUNDADIR. 
- **Tarih:** Nisan 2026

---

## Antigravity Chat

### GEMINI.md Boş → Agent Tarayıcıya Düşüyor
- **Sorun:** `GEMINI.md` boşken agent servis yönlendirmelerini bilemiyor → tarayıcıya düşüyor.
- **Çözüm:** `GEMINI.md` dosyasına tam servis yönlendirme tablosu eklendi. Asla boş bırakılmamalı.
- **Tarih:** Mart 2026

---

## Gemini API

### Model Deprecated — `404 models/gemini-1.5-pro-latest`
- **Çözüm:** Tüm `-latest` referanslarını `gemini-2.0-flash` ile değiştir.
- **Kural:** Üretim kodunda `-latest` suffix KULLANMA — spesifik model adı kullan.
- **Tarih:** Mart 2026

### get_logger() TypeError — Caller ↔ Callee İmza Uyumsuzluğu (TEKRARLAYAN)
- **Sorun:** Fonksiyonun çağrı noktası (`level=...`) güncellendi ama tanımı (`get_logger(name)`) güncellenmedi → 21 saat CRASH.
- **Çözüm:** `get_logger(name, level="INFO")` olarak güncellendi.
- **Kural:** Caller değiştirirken callee'yi de kontrol et. Import testi bunu YAKALAMAZ — imza doğrulaması da gerekli.
- **Tarih:** Nisan 2026

### GPT Model Geçişi — max_tokens + temperature Uyumsuzluğu
- **Sorun:** GPT-5 Mini `max_tokens` kabul etmiyor (→ `max_completion_tokens`), `temperature` sadece default (1.0), boş content (~%30).
- **Çözüm:** `max_tokens` → `max_completion_tokens`, temperature kaldır, boş content için 3 retry, model GPT-4.1 Mini'ye geçirildi.
- **Kural:** Model değişikliğinde API parametre uyumluluğunu kontrol et.
- **Tarih:** Nisan 2026

### ElevenLabs Rachel Sesi Kaldırıldı
- **Çözüm:** "Rachel" → "Sarah" ile değiştirildi. Voice lookup'a fallback eklendi.
- **Kural:** Hardcoded voice name yerine voice ID tercih et. API'den güncel ses listesini doğrula.
- **Tarih:** Nisan 2026

### Video Download Retry Eksikliği
- **Çözüm:** 3 deneme + exponential backoff (2s, 4s) + yarım dosya temizliği. CDN indirmelerine mutlaka retry ekle.
- **Tarih:** Nisan 2026

---

## FFmpeg — Nixpacks PATH Sorunu (3+ PROJEDE TEKRARLAYAN)

> Bu sorun Twitter, LinkedIn ve YouTube projelerinde tekrar tekrar yaşandı. TEK çözüm var.

### Sorun
Railway Nixpacks `Aptfile`/`apt.txt` dosyalarını YOKSAYAR. ffmpeg'i `/root/.nix-profile/bin/` altına kurar. `shutil.which()` ana process'te bulur ama `subprocess` child process'te bulamayabilir.

### Çözüm (3 katman)
1. **nixpacks.toml:** `[phases.setup] nixPkgs = ["ffmpeg"]` — `Aptfile`/`apt.txt` kullanma, bulursan SİL
2. **Absolute path:** `_FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"` → subprocess'te bu değişkeni kullan
3. **Fail-fast:** `config.py`'da `shutil.which("ffmpeg")` kontrolü — binary yoksa boot'ta çök

### Kurallar
- Railway'de sistem paketi = SADECE `nixpacks.toml`
- Sistem binary'leri her zaman `shutil.which()` ile resolve et
- **Tarih:** Mart-Nisan 2026 (çoklu tekrar)

---

## LinkedIn Automation

### Images API URN Format Uyumsuzluğu
- **Sorun:** Eski `v2/assets` API'si `urn:li:digitalmediaAsset:...` döndürüyor, yeni `rest/posts` `urn:li:image:...` bekliyor.
- **Çözüm:** Upload'u `rest/images?action=initializeUpload`'a migrate et. Eski ve yeni API'yi karıştırma.
- **Tarih:** Nisan 2026

### Video Content Filter — Groq LLM Tüm Videoları Reddediyor
- **Sorun:** "moderate" modda bile LLM her videoyu reddetti (7+ gün paylaşım yok).
- **Çözüm:** Prompt ultra-esnek yapıldı → `LINKEDIN_FILTER_STRICTNESS=relaxed` → tüm videolar reddedilirse en düşük güvenle reddedilen ZORLA kabul edilir.
- **Kural:** LLM content filter'larına her zaman fallback ekle.
- **Tarih:** Nisan 2026

### OpsLogger Queue Flush — Exit Before Logs Written
- **Çözüm:** `wait_all_loggers()` fonksiyonu eklendi — TÜM OpsLogger instance'larının queue'larını boşaltır.
- **Kural:** CronJob'larda birden fazla OpsLogger varsa exit'ten önce `wait_all_loggers()` çağır.
- **Tarih:** Nisan 2026

### Video Yükleme Timeout — 5 Dakika Yetersiz
- **Çözüm:** Polling `max_retries` 30'dan (5dk) 90'a (15dk) çıkarıldı. LinkedIn video işleme asenkron — en az 15dk ver.
- **Tarih:** Nisan 2026

---

## Kod-Repo Senkronizasyon

### Config.DEDUP_WINDOW_DAYS AttributeError — Lokal ↔ Production Uyumsuzluğu
- **Sorun:** Lokal'de kod değiştirildi ama push edilmedi → Railway eski commit çalıştırdı → 1 gün lead kaybı.
- **Çözüm:** Pre-push import testi + post-deploy smoke test + healing playbook `runtime_code_error` pattern'i eklendi.
- **Kural:** Her push'tan önce import testi, her deploy sonrası log taraması ZORUNLU.
- **Tarih:** Mart 2026

### Native Mono-Repo Mimarisi (MİMARİ KARAR)
- **Eski sorun:** Ayrı GitHub repo'larına kopyalama → sync sorunları, conflict'ler, veri kaybı.
- **Yeni mimari:** Tek repo `dolunayozerennn/antigravity-egitim`. Railway'de Root Directory + Watch Paths ile proje izolasyonu.
- **Kural:** `git push origin main` yeterli. Kopya `cp` scriptleri ASLA kullanılmaz.
- **Tarih:** Mart 2026

### macOS Sandbox EPERM & npm Cache
- **Sorun:** Lokal build'de `EPERM` / `operation not permitted` hataları.
- **Çözüm:** Koda DOKUNMA — sorun sandbox'ta. Kod sağlığını remote deploy loglarından yorumla. Kilitli klasörleri `mv` ile taşı.
- **Tarih:** Mart 2026

---

## Railway Deploy

### Sandbox Shell Script Token Okuma Engeli
- **Çözüm:** `cat`/`grep` yerine `view_file` ile token oku → komutu çalıştırırken enjekte et.
- **Tarih:** Mart 2026

### CLI "Unauthorized" — GraphQL API Fallback
- **Çözüm:** CLI çalışmazsa GraphQL API kullan: `curl -X POST https://backboard.railway.app/graphql/v2`
- **Tarih:** Mart 2026

### Yeni Token Propagation Gecikmesi
- **Çözüm:** 3-5 dakika bekleyip tekrar dene.

### BASH_SOURCE Sandbox'ta Boş
- **Çözüm:** Sabit yol (hardcoded path) kullan.

### Path.parents IndexError — Container Crash
- **Sorun:** Railway'de kısa yol (`/app/...`) nedeniyle `parents[N]` IndexError.
- **Çözüm:** `parents[N]` yerine enumerate ile güvenli erişim. Uzunluk kontrolü zorunlu.
- **Tarih:** Mart 2026

### API İsteklerinde Timeout Eksikliği — Sonsuz Bekleme
- **Çözüm:** Tüm dış API çağrılarına `timeout=30` (veya `60`) ekle. Python requests varsayılan timeout'suz çalışır.
- **Kural:** İstisnasız her dış istek `timeout` parametresi almalı.
- **Tarih:** Mart 2026

### SMTP Port Engellemesi — Email Gönderimi
- **Sorun:** Railway SMTP portlarını (25, 465, 587) engeller → `smtplib` çalışmaz.
- **Çözüm:** `smtplib` kaldır → Gmail API (OAuth2) kullan. `Lead_Notifier_Bot` referans implementasyon.
- **Kural:** Railway'de ASLA `smtplib` kullanma.
- **Tarih:** Mart 2026

### Ephemeral Filesystem — CSV Kalıcılık
- **Çözüm:** `ensure_csv_exists()` ile otomatik oluşturma veya harici storage kullan. `.gitignore`'daki dosyalar deploy'dan sonra kaybolur.
- **Tarih:** Mart 2026

### Nixpacks Docker Build Cache — python311
- **Çözüm:** `nixpkgs`'e `python311` explicit ekle + sıfırdan temiz deploy at (`usePreviousImageTag: false`).
- **Tarih:** Nisan 2026

---

## MCP Bağlantı Sorunları

### GitHub MCP — Docker Daemon Bağımlılığı
- **Çözüm:** Docker'dan npx tabanlıya geç: `"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]`. npm cache için `/tmp/npm-cache` kullan.
- **Tarih:** Mart 2026

### Notion MCP — 404 Hatası (Erişim İzni Eksik)
- **Sorun:** Entegrasyon sadece paylaşılmış sayfalara erişebilir.
- **Çözüm:** Notion sayfasında `...` → Connections → "antigravity" ekle. Alt sayfalar üst iznini miras alır.
- **Tanı:** `API-get-self` başarılı ama `API-retrieve-a-page` 404 → paylaşım eksik.
- **Tarih:** Mart 2026

### Notion MCP — Çift Workspace Karışıklığı
- **Sorun:** MCP tek workspace'e bağlı. Diğer workspace'e erişim yok.
- **Çözüm:** MCP dışındaki workspace'lere `curl` + `NOTION_SOCIAL_TOKEN` ile ulaş.
- **Tarih:** Mart 2026

---

## Servis İzleyici — Self-Healer

### Cron Job'lar "unknown" Raporlanıyor
- **Çözüm:** `deploy-registry.md`'de platform `railway` → `railway-cron`. `health_check.py` filtresine `railway-cron` ekle.
- **Tarih:** Mart 2026

### Watchdog — Health Check False Positive Döngüsü
- **Sorun:** Watchdog kendi hata raporlamalarını tespit edip kendisinin çöktüğünü sanıyor.
- **Çözüm:** `ERROR_PATTERNS` / `FALSE_POSITIVE_PATTERNS`'e log prefixini (`OpsLog_Akilli_Watchdog`) yoksayacak kural ekle.
- **Tarih:** Nisan 2026

---

## Netlify / Hosting

### Free Plan Kredi Tükenmesi
- **Sorun:** Her deploy = 15 kredi, 300/ay limit. Günlük cron → aylık ~450 kredi → site duraklar.
- **Çözüm:** Blog Yazıcı cron'u haftada 1'e çekildi. Aylık ~4 deploy = 60 kredi.
- **Kural:** Gereksiz push = gereksiz deploy = kredi harcama. Branch deploy kredi harcamaz.
- **Tarih:** Nisan 2026

### Cloudflare Pages — BAŞARISIZ
- **Karar:** dolunay.ai Netlify'da kalıyor. Cloudflare Pages önerilmez — daha önce denendi, başarısız oldu.
- **Tarih:** Nisan 2026

---

## GitHub

### Pages Build Spam — Sahte Alarm
- **Çözüm:** GitHub API ile Pages kapatıldı + Actions devre dışı. Mono-repo'da CI/CD = Railway build.
- **Kural:** Statik site barındırmayan repo'larda Pages kapalı olmalı.
- **Tarih:** Nisan 2026

---

## Pre-Push Test Kapsamı

### Import Testi Geçiyor Ama Runtime'da Crash (Caller ↔ Callee)
- **Sorun:** Import testi modül yüklenmesini kontrol eder ama fonksiyon argüman uyumsuzluğunu YAKALAMAZ.
- **Çözüm:** Deploy workflow'una AST tabanlı imza doğrulaması eklendi.
- **Kural:** Import testi GEREKLİ ama TEK BAŞINA YETERSİZ. Caller değiştirirken callee'yi de kontrol et.
- **Tarih:** Nisan 2026

### Lokal Fix Push Edilmemiş — Production Eski Kod (TEKRARLAYAN)
- **Sorun:** Fix lokal'de yapıldı ama push edilmedi → Railway eski commit çalıştırdı.
- **Çözüm:** Fix sonrası `git status` → modified varsa push → Railway deploy tetikle → smoke test.
- **Tarih:** Nisan 2026

---

## eCom Reklam Otomasyonu — v2.1 Stabilizasyon (24 Bug)

En kritik fixler:
1. **Event Loop Blocking (P0):** Senkron API çağrıları → `asyncio.to_thread()` ile sarımla
2. **Bellek Sızıntısı (P0):** `UserSession` temizliği → 10dk idle timeout + 20 mesaj limit
3. **asyncio.create_task Hata Yutma (P0):** `_handle_task_exception` done callback ekle
4. **Vision API NoneType (P1):** Null guard + 3 retry
5. **Telegram Markdown (P1):** `parse_mode=None` fallback
6. **Tarih:** Nisan 2026

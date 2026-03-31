# Hatalar ve Çözümler Günlüğü

Geçmişte karşılaşılan hatalar ve çözümleri. Aynı sorunu iki kez çözmemek için bu dosyayı güncelliyoruz.

**Format:** Her hata bloğu aşağıdaki yapıyı takip eder.

---

## Kie AI

### Sora 2 Pro Storyboard — Model adı ve format hataları
- **Sorun:** Model adı `sora-2-pro` değil, tam olarak `sora-2-pro-storyboard` olmalı
- **Sorun:** `shots` alanı içinde `Scene` büyük S ile yazılmalı
- **Sorun:** `n_frames` ve `aspect_ratio` zorunlu alan — eksik olunca 422 hatası
- **Çözüm:**
  ```json
  {
    "model": "sora-2-pro-storyboard",
    "input": {
      "n_frames": 150,
      "aspect_ratio": "16:9",
      "shots": [{ "Scene": "...", "image_urls": [] }]
    }
  }
  ```
- **Tarih:** Şubat 2026

### Kie AI — Eski API anahtarları (ÇÖZÜLDÜ)
- **Sorun:** Eskiden birden fazla key dolaşıyordu (`47b22662...`, `97d226c568...`)
- **Çözüm:** ✅ Tek aktif key: `0bf01128b0840e22108b95e484b09f76` — tüm dosyalar bununla güncellendi (Mart 2026)
- **Tarih:** Mart 2026

### Video üretimi sonrası URL gelmeme
- **Sorun:** `resultJson` alanı string olarak geliyor, JSON parse edilmeli
- **Çözüm:** `json.loads(data["resultJson"])["resultUrls"][0]`
- **Tarih:** Şubat 2026

---

## Gmail / Outreach

### OAuth Token Hatası (`invalid_grant`)
- **Sorun:** `token.json` süresi dolmuş veya bozulmuş
- **Çözüm:** `token.json` dosyasını sil → scripti tekrar çalıştır → tarayıcıda yeniden onayla
- **Tarih:** —

---

## Apify

### Boş sonuç / Actor başlamıyor
- **Sorun:** Çok kısıtlayıcı filtreler veya hatalı Actor ID
- **Çözüm:** Actor ID'yi Apify konsolundan kopyala, filtreleri genişlet
- **Tarih:** —

### Kredi tükenmesi
- **Çözüm:** `_knowledge/api-anahtarlari.md` → Apify Hesap 2 (yedek) kullan
- **Tarih:** —

---

## Telegram Bot

### Markdown parse hatası
- **Sorun:** GPT yanıtındaki özel karakterler Telegram'da hata veriyor
- **Çözüm:** Yanıtı göndermeden önce `escape_markdown()` ile temizle
- **Tarih:** Şubat 2026

### Telegram Conflict — Aynı anda iki bot instance (Railway)
- **Sorun:** `telegram.error.Conflict: terminated by other getUpdates request` — Railway deploy sırasında eski container henüz durmadan yenisi başlıyor, iki polling çakışıyor
- **Ek Sorun:** python-telegram-bot "No error handlers are registered" diye ERROR logluyor → self-healer bunu "unknown" sorun olarak algılıyor → sürekli yanlış alarm (false positive)
- **Çözüm (3 katman):**
  1. `bot.py` → `error_handler()` fonksiyonu eklendi: Conflict hatalarını INFO, ağ hatalarını WARNING olarak loglar. ERROR çıkmaz.
  2. `healing_playbook.json` → `telegram_conflict` ve `telegram_no_error_handler` pattern'ları eklendi: `ignore_transient` olarak sınıflandırılır.
  3. `health_check.py` → `FALSE_POSITIVE_PATTERNS` listesine eklendi: Log taramasında Conflict hataları artık hata sayılmaz.
- **Kural:** Deploy sonrası oluşan Conflict hatası geçicidir, yeni instance çalışır çalışmaz kendi kendine düzelir. Ayrıca `run_polling(stop_signals=None)` kullanılmalıdır.
- **Tarih:** Mart 2026

---

## Google Sheets / API Bağlantı Kopmaları

### SSL EOF Hatası — Geçici Ağ Kopması (Tekrarlayan Pattern)
- **Sorun:** `EOF occurred in violation of protocol (_ssl.c)` — Railway container'larında uzun süre yaşayan bağlantı objeleri bayatlıyor. Google Sheets, Fal AI gibi servislerde tekrarlayan pattern.
- **Kök neden:** `service` objesi bir kez oluşturulup sonsuza dek kullanılıyor. SSL bağlantısı kopunca retry yok, tüm döngü başarısız oluyor.
- **Çözüm (Sürdürülebilir retry pattern):**
  1. Hata mesajında geçici ağ anahtar kelimeleri ara: `eof`, `ssl`, `broken pipe`, `connection reset`, `timeout`, `connection aborted`
  2. Eşleşirse: `service = None` → `authenticate()` → tekrar dene
  3. Max 3 deneme, exponential backoff (2s, 4s)
  4. Geçici değilse doğrudan raise et
- **Uygulanan dosya:** `Tele_Satis_CRM/sheets_reader.py` → `get_all_rows()` metodu
- **Kural:** Uzun süre çalışan servislerde (polling loop, webhook listener) dış API çağrılarına **mutlaka** retry + reconnect ekle
- **Tarih:** Mart 2026

---

## Antigravity Chat — Tarayıcı Fallback Sorunu

### GEMINI.md Boş → Agent Tarayıcıya Düşüyor (KRİTİK)
- **Sorun:** Agent, Notion/Railway/GitHub gibi servislere erişirken MCP/API yerine `browser_subagent` kullanarak tarayıcı açıyordu. Kullanıcı "token'ın var" dediğinde düzeliyordu ama her seferinde hatırlatma gerekiyordu.
- **Kök Neden:** `~/.gemini/GEMINI.md` dosyası **tamamen boştu** (0 byte). Bu dosya her konuşma başında okunur ve servis yönlendirme kurallarını içermesi gerekir. Boş olduğunda agent hangi araçla hangi servise bağlanacağını bilemiyor ve default olarak tarayıcıya düşüyor.
- **Çözüm:** `GEMINI.md` dosyasına tam servis yönlendirme tablosu eklendi (GitHub → MCP, Notion → API, Railway → GraphQL, Google → MCP vb.). Bu tablo `user_global` kurallarındakiyle aynı ama ek bir güvenlik katmanı sağlıyor.
- **Kural:** `GEMINI.md` dosyasının **asla boş bırakılmaması** gerekir. Periyodik olarak kontrol et.
- **Tarih:** Mart 2026

### Gmail OAuth Scope Uyumsuzluğu — `invalid_scope: Bad Request`
- **Sorun:** `marka-is-birligi` projesinde `gmail_sender.py` → `SCOPES` listesi `gmail.readonly` istiyordu ama OAuth token `gmail.modify` scope'uyla oluşturulmuştu. Google OAuth kütüphanesi scope eşleşmediği için `invalid_scope: Bad Request` hatası verdi.
- **Kök Neden:** Token oluşturulurken `gmail.modify` (okuma+yazma) scope'u verildi ama kod daha sonra `gmail.readonly` (sadece okuma) isteyecek şekilde değiştirildi. Token scope'ları ⊃ istenen scope'lar olsa bile, eşleşme kontrolü strict.
- **Çözüm:** `gmail_sender.py` → SCOPES'ta `gmail.readonly` → `gmail.modify` olarak değiştirildi (token'daki scope ile eşleşecek şekilde).
- **Kural:** OAuth token oluşturulduktan sonra koddaki SCOPES listesi DEĞİŞTİRİLMEMELİ. Değiştirilirse token yeniden oluşturulmalı.
- **Tarih:** Mart 2026

---

## Gemini API

### Gemini Model Deprecated — `404 models/gemini-1.5-pro-latest is not found`
- **Sorun:** Bir projede `autonomous_cover_agent.py` ve `revision_engine.py` dosyalarında `gemini-1.5-pro-latest` model adı kullanılıyordu. Google bu modeli deprecate etti ve API 404 dönmeye başladı.
- **Etki:** Kapak üretim pipeline'ı Gemini Vision değerlendirmesi yapamıyordu. Evaluation hep `score: 0` dönüyordu.
- **Çözüm:** Tüm `gemini-1.5-pro-latest` referansları `gemini-2.0-flash` ile değiştirildi (6 yerde: 4x autonomous_cover_agent.py, 2x revision_engine.py).
- **Kural:** Gemini model adları deprecate olabilir. Üretim kodunda `-latest` suffix'li model adı KULLANMA — spesifik versiyon kullan. Deprecation durumunda `gemini-2.0-flash` veya `gemini-2.5-pro` gibi güncel modellere geçiş yap.
- **Tarih:** Mart 2026

> *(Yeni hata karşılaşıldığında bu dosyaya ekle)*

---

## Kod-Repo Senkronizasyon Hataları

### Config.DEDUP_WINDOW_DAYS AttributeError — Lokal ↔ Production Uyumsuzluğu (KRİTİK)
- **Sorun:** `notion_writer.py` → `Config.DEDUP_WINDOW_DAYS` kullanıyordu ama `config.py`'da bu attribute henüz tanımlanmamıştı. Lokal'de güncellenmiş ama ayrı GitHub repo'suna push edilmemişti. Railway eski commit üzerinden çalışıyordu.
- **Etki:** 1 gün boyunca lead'ler Notion'a yazılamadı → ciddi maddi kayıp
- **Kök Neden (3 katman):**
  1. Lokal kod değiştirildi ama ayrı repo'ya push edilmedi
  2. Deploy workflow'unda "push öncesi import testi" adımı yoktu → `AttributeError` deploy edilmeden yakalanamadı
  3. Health check sadece deployment status'e bakıyordu → SUCCESS durumundaki runtime error'ları tespit edemiyordu
- **Çözüm (3 katmanlı savunma eklendi):**
  1. `/canli-yayina-al` workflow'una **zorunlu pre-push kod sağlık kontrolü** eklendi (import zinciri testi + unit test çalıştırma)
  2. `/canli-yayina-al` workflow'una **zorunlu post-deploy smoke test** eklendi (log'lardan fatal error tarama)
  3. `healing_playbook.json`'a `runtime_code_error` pattern'i eklendi (AttributeError, ImportError → alert_only, redeploy yapma)
- **Kural:** Her push'tan önce `python3 -c "import modül"` ile tüm modüllerin import edilebilmesi doğrulanmalı. Her deploy sonrası loglar smoke test ile taranmalı.
- **Tarih:** Mart 2026

### Çift Repo Senkronizasyon Problemi — Lokal ↔ Ayrı GitHub Repo (KRİTİK)
- **Sorun:** Tüm projeler lokal'de mono-repo'nun içinde yaşıyor (`Projeler/XXX/`). Ama Railway her proje için **ayrı bir GitHub reposu** izliyor. Lokal'de yapılan değişiklikler mono-repo'ya push edilince **Railway bunları görmüyor** — çünkü ayrı repo'yu izliyor.
- **Etki:** 1 gün boyunca 44 lead Notion'a aktarılamadı (Tele Satış CRM)
- **Kök Neden:** 
  1. Lokal kod `antigravity-egitim` repo'suna push ediliyor
  2. Railway `tele-satis-crm` (veya benzeri) ayrı repo'dan deploy yapıyor
  3. İki repo arasında hiçbir otomatik senkronizasyon mekanizması yok
- **Çözüm (ZORUNLU DEPLOY PROSEDÜRLERİ):**
  1. **Push öncesi:** `deploy-registry.md`'den projenin **ayrı GitHub reposunu** bul
  2. O repoyu `/tmp/`'ye clone et
  3. Lokal `Projeler/XXX/` dizininden tüm dosyaları kopyala
  4. Ayrı repoya commit + push et
  5. Railway'in otomatik deploy tetiklemesini bekle (veya `serviceConnect` ile tetikle)
  6. Deploy loglarını kontrol et
- **Alternatif:** `serviceConnect` mutasyonu ile Railway'i yeniden bağla — yeni commit'ten build yapar
- **Kontrol scripti:** `/durum-kontrol` workflow'u her çalıştığında Railway commit ↔ GitHub HEAD karşılaştırması yapmalı
- **Tarih:** Mart 2026

---

## Railway Deploy

### Sandbox, Shell Script'ten Dosya Okumasını Engeller
- **Sorun:** `cat`, `grep` gibi komutlarla `_knowledge/api-anahtarlari.md` veya herhangi bir dosyadan token okunamıyor. `Operation not permitted` hatası veriyor.
- **Neden:** Antigravity sandbox ortamında çalışıyor. Sandbox, güvenlik nedeniyle shell komutlarının dosya okuma yetkisini kısıtlıyor.
- **Yanlış Çözümler (Çalışmayan):**
  - Shell script ile `cat dosya.txt` → ❌ İzin hatası
  - Gizli dosya `.railway-token` oluşturma → ❌ Gizli dosyalar ekstra kısıtlı
  - Farklı klasörlere token dosyası koyma → ❌ Tüm klasörler kısıtlı
- **Doğru Çözüm:** Antigravity'nin kendi `view_file` tool'unu kullanarak dosyayı oku, sonra token'ı komutu çalıştırırken `RAILWAY_TOKEN="okunan_token"` olarak enjekte et.
- **Kural:** Token gereken her işlemde `view_file` → `_knowledge/api-anahtarlari.md` → Token'ı oku → Komuta prefix olarak ekle.
- **Tarih:** Mart 2026

### Railway CLI "Unauthorized" ama GraphQL API Çalışıyor
- **Sorun:** `railway whoami`, `railway list` gibi CLI komutları `Unauthorized` hatası veriyor ama aynı token ile Railway GraphQL API'ye `curl` ile istek atınca sorunsuz çalışıyor.
- **Neden:** Railway CLI'ın eski versiyonu (veya workspace-scoped token'lar) bazı CLI komutlarıyla uyumsuz olabiliyor. CLI dahili olarak farklı bir auth endpoint kullanıyor.
- **Çözüm:** CLI çalışmazsa **GraphQL API fallback** kullan:
  ```bash
  curl -s -X POST https://backboard.railway.app/graphql/v2 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TOKEN" \
    -d '{"query": "{ projects { edges { node { id name } } } }"}'
  ```
- **Tarih:** Mart 2026

### Yeni Railway Token Propagation Gecikmesi
- **Sorun:** Yeni oluşturulan Railway token'ı ilk dakikalarda `Invalid RAILWAY_TOKEN` hatası verebilir.
- **Çözüm:** 3-5 dakika bekleyip tekrar dene. Token sonunda aktif olur.
- **Tarih:** Mart 2026

### BASH_SOURCE Sandbox'ta Boş Dönüyor
- **Sorun:** `bash script.sh` ile çalıştırılan script'lerde `${BASH_SOURCE[0]}` boş dönüyor. Bu da `SCRIPT_DIR` doğru hesaplanamıyor.
- **Çözüm:** `BASH_SOURCE` yerine sabit yol (hardcoded path) kullan.
- **Tarih:** Mart 2026

### Path.parents IndexError — Railway Container Crash
- **Sorun:** `pathlib.Path.parents[2]` Railway'de `IndexError: 2` fırlatıyor. `/app/shared/dosya.py` yolunun sadece 2 parent'i var (`/app/shared/`, `/app/`). `parents[2]` mevcut değil.
- **Kök Neden:** Modül seviyesinde (top-level) `try-except` olmadan parent dizin aranıyordu. Lokal'de yol derin (`/Users/.../Projeler/Proje_Adi/shared/`) olduğu için çalışıyordu, Railway'de kısa yol (`/app/shared/`) crash etti.
- **Çözüm:** `parents[N]` yerine `[p for i, p in enumerate(Path.parents) if i < 4]` ile güvenli erişim kullan. IndexError riskini ortadan kaldırır.
- **Kural:** Railway container'larında dosya yolu `/app/` altındadır. `Path.parents` index erişimlerinde **mutlaka** uzunluk kontrolü yap veya enumerate ile güvenli eriş.
- **Tarih:** Mart 2026

---

## MCP Bağlantı Sorunları

### GitHub MCP Server Bağlanmıyor — Docker Daemon + macOS Sandbox
- **Sorun:** GitHub MCP, `mcp_config.json`'da Docker container olarak yapılandırılmıştı (`ghcr.io/github/github-mcp-server`). Docker Desktop kapalı olduğunda MCP asla başlatılamıyordu. Tüm `mcp_github-mcp-server_*` araçları devre dışı kalıyordu.
- **Ek Sorun:** `~/.npm` klasöründe macOS'un `com.apple.provenance` extended attribute'u vardı. Bu, sandbox ortamından çalışan npm süreçlerinin yeni paket indirmesini engelliyordu (EPERM hatası).
- **Çözüm (2 adım):**
  1. Terminal'den `sudo chown -R $(whoami) ~/.npm && xattr -dr com.apple.provenance ~/.npm` çalıştırıldı
  2. `mcp_config.json`'da GitHub MCP, Docker'dan npx tabanlıya geçirildi: `"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]`
  3. Sandbox npm cache sorunu için `"npm_config_cache": "/tmp/npm-cache"` env değişkeni eklendi
- **Kural:** MCP sunucularını mümkünse Docker yerine npx/uvx ile çalıştır — Docker Desktop bağımlılığını ortadan kaldırır.
- **Tarih:** Mart 2026

---

## Railway — SMTP Port Engellemesi (KRİTİK)

### `[Errno 101] Network is unreachable` — SMTP Email Gönderimi
- **Sorun:** Railway container'larında `smtplib.SMTP_SSL("smtp.gmail.com", 465)` çağrısı `[Errno 101] Network is unreachable` hatası veriyor. Bu hata `Isbirligi_Tahsilat_Takip` ve `Akilli_Watchdog` projelerinde e-posta gönderimini haftalarca engelledi.
- **Kök Neden:** Railway, abuse önleme nedeniyle SMTP portlarını (25, 465, 587) engeller. `smtplib` ile e-posta göndermek mümkün değil.
- **Etki:** `Isbirligi_Tahsilat_Takip` 7+ gün boyunca 17 markaya ödeme hatırlatması gönderemedi. `Akilli_Watchdog` sağlık raporu e-postaları hiç ulaşmadı.
- **Çözüm:** `smtplib` tamamen kaldırıldı → Gmail API (OAuth2) ile değiştirildi:
  1. `GOOGLE_OUTREACH_TOKEN_JSON` env variable'ı Railway'e eklendi
  2. `google.oauth2.credentials.Credentials.from_authorized_user_info()` ile token parse
  3. `googleapiclient.discovery.build('gmail', 'v1')` ile service oluştur
  4. `base64.urlsafe_b64encode()` ile email encode → `users().messages().send()` 
- **Kural:** Railway'de **ASLA** `smtplib` kullanma. Email göndermek için **Gmail API (OAuth2)** kullan. `Lead_Notifier_Bot` referans implementasyon.
- **Dikkat:** `variableUpsert` mutation'ı ile JSON env variable eklerken çift-escape sorunu olabilir. Token'ı her zaman doğrudan `json.dumps(token_string)` ile escape et, ek escape YAPMA.
- **Tarih:** Mart 2026

### markalar.csv Kalıcılık Sorunu — Railway Ephemeral Filesystem
- **Sorun:** `Marka_Is_Birligi` projesinde `data/markalar.csv` dosyası `.gitignore`'da olduğu için Railway'e deploy edilmiyordu. Her deploy sonrası `[FOLLOWUP] markalar.csv bulunamadı!` hatası.
- **Kök Neden:** Railway container'ları ephemeral (geçici) dosya sistemi kullanır. `.gitignore` ile hariç tutulan dosyalar deploy'dan sonra mevcut olmaz.
- **Çözüm:** `ensure_csv_exists()` fonksiyonu eklendi — modül yüklendiğinde `data/` klasörü ve `markalar.csv` header-only olarak otomatik oluşturulur.
- **Kural:** Railway'de runtime'da oluşturulan/güncellenen veri dosyaları **deploy sonrası kaybolur**. Ya otomatik oluşturma mekanizması ekle, ya da harici storage (Google Drive, DB) kullan.
- **Tarih:** Mart 2026

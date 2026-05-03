# Antigravity — Universal Agent Talimatları

Bu dosya, Antigravity workspace'inde çalışan **her** AI agent (Antigravity/Gemini, Claude Code, Cursor, Cline) tarafından okunur. Tek kaynak gerçeği budur.

---

## 👤 Kullanıcı

- **Ad:** Dolunay Özeren
- **E-posta:** ozerendolunay@gmail.com
- **İkincil hesap:** d.ozeren@sweatco.in (Sweatcoin işi)
- **Çalışma dili:** Türkçe — kod hariç tüm iletişim Türkçe.
- **Tarz:** Otonom çalışma. Kullanıcıya "şu komutu terminale yapıştır", "dashboard'a git", "linke tıkla" deme. Tool'ları doğrudan kullan.
- **Mimar Modu (rol dağılımı):** Kullanıcı = ürün sahibi (hedef + ürün kararları). Sen = teknik mimar (kod, mimari, dependency, refactor — her şey *nasıl yapılacak*). Teknik karar için onay isteme; sadece ürün düzleminde sor (hedef belirsizliği, ürün-anlamlı trade-off, geri-dönüşü-zor + dış-görünür eylem, yüksek maliyet). Kullanıcı kodu/mimariyi anlamıyor — onu teknik diyaloga çekme. Detay: `~/.claude/CLAUDE.md`.

---

## 📁 Klasör Haritası

```
Antigravity/
├── AGENTS.md              ← Bu dosya (tüm agent'lar okur)
├── .claude/               ← Claude Code'a özel köprü dosyalar (lokal, gitignore'da)
│   ├── skills/            → ../_skills/<name>/  (symlink)
│   ├── agents/            → ../_agents/<name>/AGENT.md  (symlink)
│   └── commands/          → ../_agents/workflows/<name>.md  (symlink)
├── _knowledge/            ← Merkezi bilgi bankası
├── _skills/               ← Atomik beceriler (her biri SKILL.md ile)
├── _agents/               ← Orkestrasyon agent'ları + slash workflow'ları
│   └── workflows/         ← Slash komut tanımları (/canli-yayina-al gibi)
├── Projeler/              ← Aktif projeler
├── Paylasilan_Projeler/   ← Dışa paylaşıma hazırlanmış projeler
└── _arsiv/                ← Eski/pasif çalışmalar (genellikle dokunma)
```

`_skills/` ve `_agents/` patikleri Antigravity (Gemini) kullanımı içindir. Claude Code aynı içeriği `.claude/skills/`, `.claude/agents/`, `.claude/commands/` üzerinden symlink ile görür. **Tek kaynak vardır:** `_skills/`, `_agents/`. `.claude/` sadece köprüdür.

---

## 🧠 Knowledge — Bilgi Bankası

Her oturumda otomatik referans verilen kritik dosyalar:

| Dosya | İçerik | Ne Zaman |
|---|---|---|
| `_knowledge/calisma-kurallari.md` | Kullanıcının kalıcı tercihleri, tekrarlayan talepleri | **Her oturumun başında oku** |
| `_knowledge/api-anahtarlari.md` | Tüm servislerin API anahtar listesi (lokal, gitignore) | API/servis çağrısı yapmadan önce |
| `_knowledge/deploy-registry.md` | Railway'e deploy edilmiş projelerin ID kaydı | Deploy/redeploy işleminden önce |
| `_knowledge/hatalar-ve-cozumler.md` | Geçmişte çözülmüş hatalar | Yeni hata aynı kalıba uyuyor mu kontrolü |
| `_knowledge/bekleyen-gorevler.md` | TODO listesi | Kullanıcı "ne yapacaktık" derse |
| `_knowledge/maliyet-takibi.md` | API kotası ve maliyet logu | Yüksek-maliyetli çağrılar öncesi |
| `_knowledge/mcp-ve-tool-optimizasyon-rehberi.md` | MCP ve tool kullanım kuralları | Tool seçerken |

İhtiyaç olunca bakılır:
- `_knowledge/banka-bilgileri.md` — fatura kesimi
- `_knowledge/estetik-tasarim-notlari.md` — UI/görsel iş
- `_knowledge/son-audit-raporu.md` — proje audit referansı
- `_knowledge/tamamlanan-gorevler-arsiv.md` — geçmiş işler
- `_knowledge/platform-checklists/` — platform-spesifik kontrol listeleri
- `_knowledge/templates/` — şablonlar

---

## 🔐 Credentials

**Konum:** `_knowledge/credentials/master.env` (gitignore'da, asla commit edilmez, içeriği hiçbir agent-okur dosyaya yazılmaz)

**Kullanım:**
- Master.env'i bir projeye bağlamak gerekiyorsa `_skills/sifre-yonetici/SKILL.md` skill'ini tetikle
- Railway için: `RAILWAY_TOKEN` master.env'den alınıp `RAILWAY_TOKEN=... railway ...` formatında kullanılır
- Google OAuth (Gmail/Drive/Sheets) için: `_knowledge/credentials/oauth/google_auth.py` modülü import edilir, asla yeni token oluşturma akışı başlatılmaz. Detay: `_skills/eposta-gonderim/SKILL.md`

**ASLA:**
- Master.env içeriğini herhangi bir markdown/dokümana yazma
- Yeni Google OAuth token akışı (browser/redirect URL) başlatma
- `.env` dosyasını commit'e dahil etme

---

## 🛠 Skills — Atomik Beceriler

Her skill `_skills/<name>/SKILL.md` içinde tanımlı, YAML frontmatter ile (`name`, `description`). Description alanı tetiklenme cümlesidir — agent kullanıcının talebine bakıp ilgili skill'i otomatik açar.

**Tam liste:** `ls _skills/` veya `_skills/README.md`. Sık kullanılanlar:

| Skill | Tetikleyici |
|---|---|
| `canli-yayina-al` | "deploy et", "production'a al", "7/24 çalışsın" |
| `eposta-gonderim` | "mail at", "outreach gönder" |
| `lead-generation` | "lead bul", "scraping yap" |
| `fatura-olusturucu` | "fatura kes" |
| `kie-ai-video-production` | video/görsel/ses üretimi |
| `proje-gorsellestirici` | "mimari şema", D3.js |
| `servis-izleyici` | sağlık kontrolü |
| `sifre-yonetici` | env/token bağlama |
| `otomatik-yedekleme` | backup |

Tüm projelerde **standart kural** olarak okunması gerekenler (rule skill'leri):
- `notion-api-rules`, `railway-deploy-rules`, `supabase-postgres-best-practices`, `apify-scraping-rules`, `telegram-bot-rules`, `llm-structured-output-rules`

---

## 🤖 Sub-Agents

`_agents/<name>/AGENT.md` ile tanımlı orkestrasyon agent'ları:

- **icerik-uretim** — Çağrı Bozay / Dubai gayrimenkul içerik pipeline'ı (araştırma → script → video)
- **musteri-kazanim** — Lead generation + outreach kombinasyonu
- **yayinla-paylas** — Deploy + paylaşım + fatura

---

## ⚡ Slash Workflow'ları

`_agents/workflows/<name>.md` — Claude Code'da `.claude/commands/` üzerinden `/<name>` olarak çağrılır:

| Komut | İşlev |
|---|---|
| `/canli-yayina-al` | Production deploy (GitHub + Railway) |
| `/durum-kontrol` | Tüm servislerin sağlık durumu |
| `/fatura-kes` | Invoice üret |
| `/yedekle` | Manuel yedekleme |
| `/sifre-bagla` | Projeye env bağla |
| `/proje-audit` | Proje sağlık denetimi |
| `/proje-paylas` | Export + paylaşıma hazırla |
| `/proje-gorsellestir` | D3.js mimari şema |
| `/icerik-uretimi` | İçerik pipeline'ını başlat |
| `/hata-duzeltme` | Yapılandırılmış hata triage |
| `/stabilize` | Flaky/unstable pattern düzeltme |
| `/mimari-audit` | Cross-proje mimari kontrol |
| `/degisiklik-kontrol` | Diff özet/etki analizi |
| `/bot-test` | Telegram botların flow testi |
| `/drone-cekim` | (özel iş akışı) |
| `/self-review` | Kendi çıktına ikinci-pass |
| `/sub-agent-prompt`, `/sub-agent-sonuc` | Sub-agent koordinasyonu |

---

## 🚀 Otonom Çalışma Kuralları (KRİTİK)

1. **Terminal komutları** — `Bash`/`run_command` ile sen çalıştır, kullanıcıya yapıştırma. Risk az ise auto-run kullan.
2. **GitHub** — `gh` CLI veya GitHub MCP. Asla "manuel commit at" deme.
3. **Railway** — `master.env`'deki `RAILWAY_TOKEN` ile `railway` CLI. Dashboard söyleme.
4. **Dosya değişiklikleri** — `Edit`/`Write` doğrudan. "Şu satırı şöyle değiştir" diyerek kullanıcıya iş bırakma.
5. **OAuth/token** — Mevcut tokenlar otomatik refresh'lenir. Yeni token akışı başlatma.

Kısacası: **klavyeyi sen kullan, kullanıcı sadece onay versin.**

---

## 📌 Aktif Bağlam Notu

- Bekleyen Railway deploy kaydı: `_knowledge/bekleyen-gorevler.md` veya memory'deki `project_ecom_pending_deploy.md`'ye bak.
- Proje listesi için `Projeler/` ls'le; `_arsiv/` pasif.

---

*Bu dosyaya bir şey eklemek istersen: kapsam küçükse direkt düzenle. Knowledge'a ait bir bilgi ise `_knowledge/` altındaki ilgili dosyaya yaz, buradan referans ver.*

# 💰 İşbirliği Tahsilat Takip

Sosyal medya işbirlikleri (YouTube & Reels) için **günlük toplu tahsilat özeti**.
Her sabah Notion'daki "Yayınlandı" durumundaki videoları tarar, ödeme alınmamış olanlardan
14+ gün geçenleri tek bir HTML e-postada özetler.

---

## 🎯 Ne Yapar?

1. **Notion'dan veri çeker** — YouTube İşbirliği ve Reels İşbirliği veritabanlarından "Yayınlandı" durumundaki videoları alır.
2. **Tutar bilgisini join'ler** — `Gelir > Tahsilat Takip` veritabanını **sadece okur** ve `Dolunay Reels` relation'ı üzerinden video → tutar eşlemesi yapar.
3. **Gecikme hesaplar** — Yayın tarihinden bugüne kaç gün geçtiğini hesaplar.
4. **Tek toplu e-posta atar** — Bekleyen kayıtlar üç banda ayrılır:
   - 🟡 **14-29 gün** → Sarı bandı
   - 🔴 **30-59 gün** → Kırmızı bandı
   - ⚫ **60+ gün** → Siyah bandı
5. **Bekleyen yoksa mail atılmaz.** Notion'a hiçbir şey yazılmaz.

---

## 🏗️ Mimari

```
Notion (YouTube DB + Reels DB)        Notion (Gelir > Tahsilat Takip)
            │                                       │ (READ-ONLY)
            ▼                                       ▼
                       notion_client.py
                              │
                              ▼
                         database.py — gecikme + bant filtresi
                              │
                              ▼
                            main.py — tek HTML özet hazırlar
                              │
                              ▼
                         email_client.py — Gmail API
```

State takibi **yok** — günde 1 mail atıldığı için duplicate riski olmadan stateless çalışır.

---

## 🔒 Tahsilat Takip DB — Kritik Veri (sadece okuma)

`notion_client.fetch_payment_amounts()` **yalnızca** `databases/{id}/query` çağrısı yapar.
Bu DB üzerinde hiçbir `pages PATCH`, `comments POST` veya yazma çağrısı yoktur.

---

## 📁 Dosya Yapısı

| Dosya | Açıklama |
|-------|----------|
| `main.py` | Toplu HTML özet + Gmail gönderim |
| `config.py` | Ortam değişkenleri ve DB ID'leri |
| `notion_client.py` | Video DB sorgusu + Tahsilat Takip read-only join |
| `database.py` | Gecikme + bant filtresi (state-less) |
| `email_client.py` | Gmail API (OAuth2) ile gönderim |
| `railway.json` | Railway native cron config |
| `requirements.txt` | Python bağımlılıkları |

---

## ⚙️ Ortam Değişkenleri

| Değişken | Kaynak | Açıklama |
|----------|--------|----------|
| `NOTION_SOCIAL_TOKEN` | `master.env` / Railway env | Notion Social workspace anahtarı |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Railway env | Gmail API OAuth2 token |

---

## 📡 Notion Veritabanları

| DB | ID | Erişim |
|----|----|----|
| YouTube İşbirliği | `5bb95514-0a32-821f-98cc-81605e4a971f` | read |
| Reels İşbirliği | `27b95514-0a32-8385-89eb-813222d532a2` | read |
| Tahsilat Takip (Gelir) | `2cb955140a3282708ada810e72dbd0d2` | **read-only** |

---

## 🚀 Çalıştırma

```bash
# Lokal
python main.py

# Railway: native cron (her gün 07:00 UTC)
```

---

## 🚂 Deploy

- **Platform:** Railway (Native Cron)
- **GitHub Repo:** `dolunayozerennn/isbirligi-tahsilat-takip`
- **Start:** `python main.py` · **Restart:** `NEVER` · **Cron:** `0 7 * * *`

---

## 📝 Versiyon Geçmişi

| Tarih | Değişiklik |
|-------|-----------|
| 2026-05-03 | Toplu özet maile geçiş, eşikler 14/30/60'a güncellendi, Tahsilat Takip read-only join eklendi, Notion'a yorum yazımı tamamen kaldırıldı |
| 2026-03-24 | Production stabilizasyonu (timeout, schema fix) |
| 2026-03-16 | Notion comment-based state'e geçiş |
| 2026-03-15 | SQLite → Notion state migration |
| 2026-03-13 | Kademeli bildirim sistemi |
| 2026-03-12 | İlk sürüm |

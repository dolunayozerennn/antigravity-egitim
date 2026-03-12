# 🚀 Antigravity — AI Agent Talimatları

Bu dosya, Antigravity projesiyle çalışan AI agent'ın her konuşmada bilmesi gereken temel kuralları içerir.

---

## 🔐 Google OAuth — Merkezi Token Sistemi

**Google API erişimi (Gmail, Drive, Sheets) için asla yeni token oluşturma, terminal URL yapıştırma veya tarayıcı açma!**

Tokenlar zaten merkezi depoda mevcut ve otomatik yenileniyor:

```
_knowledge/credentials/oauth/
├── google_auth.py              ← Bu modülü import et
├── gmail-outreach-token.json   ← ozerendolunay@gmail.com
└── gmail-swc-token.json        ← d.ozeren@sweatco.in
```

### Kullanım
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.expanduser("~/Desktop/Antigravity"), "_knowledge/credentials/oauth"))
from google_auth import get_gmail_service, get_sheets_service, get_drive_service

# Outreach / kişisel hesap → "outreach"
gmail = get_gmail_service("outreach")
sheets = get_sheets_service("outreach")
drive = get_drive_service("outreach")

# Sweatcoin hesabı → "swc"
gmail = get_gmail_service("swc")
sheets = get_sheets_service("swc")
```

### Kurallar
1. **Yeni token oluşturma** — mevcut tokenlar `refresh_token` ile sonsuza kadar yenilenir
2. **Token dosyasını kopyalama veya taşıma** — merkezi depodaki dosyalar kullanılır
3. **Kullanıcıdan terminal etkileşimi isteme** — token yenileme otomatik
4. Sadece token tamamen bozulduysa: `cd _knowledge/credentials/oauth && python3 auth_helper.py status`

---

## 🔑 API Anahtarları — Merkezi .env Deposu

Tüm API anahtarları tek dosyada: `_knowledge/credentials/master.env`

Projelere bağlamak için `_skills/sifre-yonetici/` skill'ini kullan (detaylar `SKILL.md`'de).

---

## 📁 Proje Yapısı

```
Antigravity/
├── _agents/          ← Orkestrasyon agent'ları + workflow'lar
├── _skills/          ← Atomik beceriler (lead bulma, mail atma, video üretimi vb.)
├── _knowledge/       ← Merkezi bilgi bankası + credentials deposu
├── Projeler/         ← Aktif projeler
└── Paylasilan_Projeler/ ← Dışarıyla paylaşılan projeler
```

---

## 📋 Sık Kullanılan Workflow'lar

| Komut | İşlev |
|-------|-------|
| `/mail-gonder` | Lead listesine mail gönder |
| `/lead-toplama` | Hedef profil ve e-posta listesi oluştur |
| `/marka-outreach` | Marka iş birliği outreach pipeline'ı |
| `/fatura-kes` | Invoice üret |
| `/durum-kontrol` | Railway servislerinin sağlık durumu |
| `/yedekle` | Manuel yedekleme |
| `/sifre-bagla` | Projeye token/API anahtarı bağla |

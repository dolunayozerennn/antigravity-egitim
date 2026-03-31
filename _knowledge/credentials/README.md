# 🔐 Merkezi Credential Deposu

Bu klasör Antigravity ekosistemindeki **tüm API token ve bağlantılarını** merkezi olarak yönetir.

## Dosyalar

| Dosya | İçerik | Güvenlik |
|-------|--------|----------|
| `master.env` | Tüm API anahtarları (.env formatı) | 🔒 .gitignore |
| `google-service-account.json` | Google Cloud Service Account | 🔒 .gitignore |
| `oauth/google_auth.py` | Merkezi Google OAuth modülü | ✅ Kullanılabilir |
| `oauth/auth_helper.py` | İlk seferlik OAuth yetkilendirme | ✅ Kullanılabilir |
| `oauth/gmail-outreach-token.json` | ozerendolunay@gmail.com token'ı | 🔒 .gitignore |
| `oauth/gmail-swc-token.json` | d.ozeren@sweatco.in token'ı | 🔒 .gitignore |

## Google OAuth — Merkezi Token Yönetimi

### Yapı
```
oauth/
├── google_auth.py              ← TÜM projeler bu modülü kullanır
├── auth_helper.py              ← İlk seferlik yetkilendirme (bir daha gerekmez)
├── gmail-outreach-token.json   ← ozerendolunay@gmail.com (Gmail+Drive+Sheets)
├── gmail-swc-token.json        ← d.ozeren@sweatco.in (Gmail+Drive+Sheets)
├── gmail-outreach-credentials.json
└── gmail-swc-credentials.json
```

### Kullanım (Projelerden)
```python
import sys
sys.path.insert(0, '_knowledge/credentials/oauth')
from google_auth import get_gmail_service, get_sheets_service

# Outreach hesabı
gmail = get_gmail_service("outreach")
sheets = get_sheets_service("outreach")

# Sweatcoin hesabı
gmail = get_gmail_service("swc")
```

### Token Scope'ları (Her İki Hesap İçin)
- `gmail.modify` — Gmail okuma, yazma, gönderme
- `gmail.send` — Gmail gönderme
- `drive.file` — Google Drive dosya erişimi
- `spreadsheets` — Google Sheets okuma/yazma

### Token Yenileme
Token'lar `refresh_token` içerir → **sonsuza kadar otomatik yenilenir**.
Google Cloud Console'da uygulamayı silmediğin sürece tarayıcı açılmaz.

## Nasıl Çalışır?

1. **Yeni proje başlatırken:** `sifre-yonetici` skill'ini çağır
2. Skill otomatik olarak projenin ihtiyaç duyduğu token'ları belirler
3. Google OAuth için `google_auth.py` modülünü import eder
4. Diğer API'ler için projeye symlink veya `.env` oluşturulur

## Kurallar

- ⚠️ Bu klasörü **asla** GitHub'a push etme
- 🔄 Token değiştiğinde **sadece `master.env`** dosyasını güncelle
- 🔑 Google OAuth sorun çıkarsa: `cd oauth && python3 auth_helper.py status`
- 📋 Yeni servis eklendiğinde `master.env` dosyasını güncelle

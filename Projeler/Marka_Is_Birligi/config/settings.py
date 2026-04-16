# ═══════════════════════════════════════════════════════════
# ⚠️ LEGACY DOSYA — KULLANILMIYOR
# ═══════════════════════════════════════════════════════════
# Bu dosya projenin bağımsız olduğu dönemden kalmadır.
# Artık Antigravity ekosistemi altındayız.
#
# API Anahtarları    → _knowledge/api-anahtarlari.md
# Kampanya Ayarları  → config/kampanya.yaml
# Mail Gönderimi     → _skills/eposta-gonderim/
# Lead Bulma         → _skills/lead-generation/
#
# Bu dosyayı değiştirmeyin, sadece referans olarak tutulur.
# ═══════════════════════════════════════════════════════════

# API Anahtarları ve Ayarları (LEGACY)

import os

# Apify Ayarları (Instagram Hashtag/Profile Scraper için)
APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")

# Hunter.io Ayarları (E-posta bulmak için)
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

# Brave Search API (Opsiyonel: Google alternatif arama için)
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# Arama Kriterleri
SEARCH_KEYWORDS = [
    "moda markaları",
    "kozmetik markaları",
    "teknoloji aksesuarları",
    "sürdürülebilir giyim"
]

# E-posta Gönderim Ayarları
GMAIL_USER = "sizin_email@gmail.com"
EMAIL_SUBJECT = "Marka İş Birliği Hakkında"

# Diğer Ayarlar
OUTPUT_FILE = "data/markalar.csv"
MAIL_TEMPLATE_PATH = "mail_templates/collaboration_tr.html"

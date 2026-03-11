"""
config.py — Buğra Influencer Outreach Projesi
Tüm API anahtarları ve arama kriterleri burada tanımlanır.
"""

# ─────────────────────────────────────────────
# 🔑 API ANAHTARLARI
# ─────────────────────────────────────────────

# Apify: Instagram & TikTok scraping
# https://console.apify.com/account/integrations
APIFY_TOKEN = ""  # ← Buraya Apify API token'ını yaz

# Hunter.io: E-posta bulma (domain'den)
# https://hunter.io/api-keys
HUNTER_API_KEY = ""  # ← Buraya Hunter.io API key'ini yaz

# Apollo.io: B2B kişi bulma (Hunter yetmezse)
# https://developer.apollo.io/
APOLLO_API_KEY = ""  # ← Buraya Apollo.io API key'ini yaz

# Gmail OAuth2 credentials dosyası
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# ─────────────────────────────────────────────
# 🎯 INFLUENCER ARAMA KRİTERLERİ
# ─────────────────────────────────────────────
# Buğra buraya ne tür influencer aradığını yazar.
# Örnek: etkinlik, konser, festival, eğlence, lifestyle...

INSTAGRAM_KEYWORDS = [
    # Örnek — Buğra dolduracak:
    # "etkinlik istanbul",
    # "konser istanbul",
    # "festival türkiye",
    # "lifestyle türkiye",
    # "influencer iş birliği",
]

TIKTOK_KEYWORDS = [
    # Örnek — Buğra dolduracak:
    # "istanbul etkinlik",
    # "türkiye festival",
    # "eğlence içerik",
]

INSTAGRAM_HASHTAGS = [
    # Örnek — Buğra dolduracak:
    # "#istanbuletkinlik",
    # "#konseristanbul",
    # "#festivalturkiye",
]

# ─────────────────────────────────────────────
# ⭐ HEDEF INFLUENCER PROFİLİ
# ─────────────────────────────────────────────
# Ne tür bir influencer arıyorsun? Bu bilgi referans içindir.

HEDEF_PROFIL = {
    "minimum_takipci": 10000,        # Minimum takipçi sayısı
    "maksimum_takipci": 5000000,     # Maksimum (mega influencer hariç tutmak için)
    "dil": ["TR"],                   # Türkçe içerik üretenler
    "niş": [],                       # Örnek: ["lifestyle", "muzik", "eglence"] — Buğra dolduracak
    "lokasyon": "Türkiye",           # Hedef lokasyon
}

# ─────────────────────────────────────────────
# 📤 OUTREACH AYARLARI
# ─────────────────────────────────────────────

GONDEREN_EMAIL = ""  # ← Buğra'nın Gmail adresi (örn. bugra@gmail.com)

# Günlük maksimum e-posta (spam önleme)
GUNLUK_LIMIT = 50

# ─────────────────────────────────────────────
# 📁 DOSYA YOLLARI
# ─────────────────────────────────────────────

INPUT_RAW       = "data/influencers_raw.json"
INPUT_EMAILS    = "data/influencers_with_emails.json"
OUTPUT_MESSAGES = "data/outreach_messages.json"
TAKIP_CSV       = "Takip_Listesi.csv"
BEGENI_CSV      = "Beğenilen_Influencerlar.csv"

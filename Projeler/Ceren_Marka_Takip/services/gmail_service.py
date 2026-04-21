"""
Ceren_Marka_Takip — Gmail API Servis Wrapper
===============================================
Merkezi google_auth modülünü kullanarak Gmail API erişimi sağlar.
Hem lokal hem Railway ortamında çalışır.
"""

import os
import sys
import json
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Merkezi OAuth dizini (lokal)
# services/gmail_service.py → services/ → Ceren_Marka_Takip/ → Projeler/ → Antigravity/
OAUTH_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "_knowledge", "credentials", "oauth"
)

# Desteklenen hesaplar
ACCOUNTS = {
    "ceren": {
        "email": "ceren@dolunay.ai",
        "token_file": "gmail-ceren-token.json",
        "token_env": "GOOGLE_CEREN_TOKEN_JSON",
    },
    "dolunay_ai": {
        "email": "dolunay@dolunay.ai",
        "token_file": "gmail-dolunay-ai-token.json",
        "token_env": "GOOGLE_DOLUNAY_AI_TOKEN_JSON",
    },
    "outreach": {
        "email": "ozerendolunay@gmail.com",
        "token_file": "gmail-outreach-token.json",
        "token_env": "GOOGLE_OUTREACH_TOKEN_JSON",
    },
}

ALL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
]


def _get_credentials(account: str) -> Credentials:
    """
    Token al — lokal dosya veya Railway env variable.
    
    Args:
        account: "ceren", "dolunay_ai", veya "outreach"
    
    Returns:
        Geçerli Google OAuth Credentials
    """
    if account not in ACCOUNTS:
        raise ValueError(f"Bilinmeyen hesap: '{account}'. Geçerli: {list(ACCOUNTS.keys())}")

    config = ACCOUNTS[account]
    token_path = os.path.join(OAUTH_DIR, config["token_file"])
    env_var = config["token_env"]
    loaded_from = None

    # 1) Lokal dosya
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, ALL_SCOPES)
        loaded_from = "file"
    # 2) Railway env variable
    elif os.environ.get(env_var):
        token_json = json.loads(os.environ[env_var])
        creds = Credentials.from_authorized_user_info(token_json, ALL_SCOPES)
        loaded_from = "env"
    else:
        raise FileNotFoundError(
            f"Token bulunamadı: {config['email']} için ne dosya ({token_path}) "
            f"ne de env ({env_var}) mevcut."
        )

    # Süresi dolmuşsa yenile
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if loaded_from == "file":
                _save_token(creds, token_path)
            logger.info(f"Token yenilendi: {config['email']}")
        else:
            raise RuntimeError(f"Token geçersiz ve yenilenemiyor: {config['email']}")

    return creds


def _save_token(creds: Credentials, token_path: str):
    """Yenilenen token'ı dosyaya kaydet."""
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else ALL_SCOPES,
        "universe_domain": "googleapis.com",
        "account": "",
        "expiry": creds.expiry.isoformat() + "Z" if creds.expiry else None,
    }
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)


def get_gmail_service(account: str):
    """Gmail API service objesi döndür."""
    creds = _get_credentials(account)
    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    logger.debug(f"Gmail service hazır: {ACCOUNTS[account]['email']}")
    return service

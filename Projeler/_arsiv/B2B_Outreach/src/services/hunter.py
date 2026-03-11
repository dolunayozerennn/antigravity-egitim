import os
import requests
from typing import Dict, Any

class HunterClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUNTER_API_KEY")
        self.base_url = "https://api.hunter.io/v2"

    def verify_email(self, email: str) -> str:
        url = f"{self.base_url}/email-verifier"
        params = {"email": email, "api_key": self.api_key}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            # Hunter.io returns 'status': 'deliverable', 'risky', 'undeliverable', etc.
            status = data.get("data", {}).get("status", "unknown")
            return status
        except requests.exceptions.RequestException as e:
            print(f"Hunter API hatası (Verify Email): {e}")
            return "unknown"

    def find_email(self, domain: str, first_name: str, last_name: str) -> Dict[str, Any]:
        url = f"{self.base_url}/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except requests.exceptions.RequestException as e:
            print(f"Hunter API hatası (Find Email): {e}")
            return {}

import os
import requests
from typing import List, Dict, Any

class ApolloClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }

    def search_people(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/mixed_people/search"
        payload = {"api_key": self.api_key, **query_params}
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("people", [])
        except requests.exceptions.RequestException as e:
            print(f"Apollo API hatası (People Search): {e}")
            return []

    def enrich_person(self, email: str = None, linkedin_url: str = None) -> Dict[str, Any]:
        url = f"{self.base_url}/people/match"
        payload = {"api_key": self.api_key}
        if email:
            payload["email"] = email
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("person", {})
        except requests.exceptions.RequestException as e:
            print(f"Apollo API hatası (Enrichment): {e}")
            return {}

    def search_organizations(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/mixed_companies/search"
        payload = {"api_key": self.api_key, **query_params}
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("organizations", [])
        except requests.exceptions.RequestException as e:
            print(f"Apollo API hatası (Organizations Search): {e}")
            return []

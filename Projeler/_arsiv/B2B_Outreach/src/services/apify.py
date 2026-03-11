import os
from apify_client import ApifyClient
from typing import List, Dict, Any

class ApifyClientWrapper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("APIFY_API_KEY")
        self.client = ApifyClient(self.api_key)

    def search_linkedin_leads(self, keywords: List[str], locations: List[str], titles: List[str], num_results: int = 10) -> List[Dict[str, str]]:
        """
        Google arama üzerinden LinkedIn profillerini bularak lead verisi toplar.
        """
        # Arama sorgusunu yapılandırma
        titles_query = " OR ".join(titles)
        locations_query = " OR ".join(locations)
        keywords_query = " OR ".join(keywords)
        
        query = f'site:linkedin.com/in ({titles_query}) ({keywords_query}) ({locations_query})'
        
        try:
            run = self.client.actor("apify/google-search-scraper").call(
                run_input={
                    "queries": query,
                    "resultsPerPage": num_results + 5,
                    "maxPagesPerQuery": 1
                }
            )
            
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            leads = []
            for row in items:
                results = row.get("organicResults", [])
                for idx, r in enumerate(results):
                    if idx >= num_results:
                        break
                        
                    title_parts = r.get("title", "").split(" - ")
                    ad_soyad = title_parts[0] if len(title_parts) > 0 else "Bilinmiyor"
                    pozisyon_sirket = title_parts[1] if len(title_parts) > 1 else "Bilinmiyor"
                    
                    leads.append({
                        "ad_soyad": ad_soyad,
                        "pozisyon_sirket": pozisyon_sirket,
                        "linkedin_url": r.get("url", ""),
                        "aciklama": r.get("description", "")
                    })
            return leads
        except Exception as e:
            print(f"Apify API hatası (LinkedIn Search): {e}")
            return []

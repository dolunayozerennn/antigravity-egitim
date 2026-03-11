import time
from typing import List, Dict, Any
from src.models.lead import Lead
from src.models.campaign import Campaign
from src.services.apollo import ApolloClient
from src.services.hunter import HunterClient
from src.services.llm_content import LLMEmailGenerator
from src.services.gmail import GmailClient

class CampaignOrchestrator:
    def __init__(self):
        self.apollo = ApolloClient()
        self.hunter = HunterClient()
        self.llm = LLMEmailGenerator()
        # Gmail requires credentials.json to be set up.
        # Initialize lazily when sending.
        self.gmail = None

    def find_and_verify_leads(self, campaign: Campaign, limit: int = 10) -> List[Lead]:
        print(f"[{campaign.ad}] Kampanyası için Apollo'da lead aranıyor...")
        
        # Simple mapping to Apollo query parameters
        query = {
            "q_organization_domains": "", # Or industry specific searches
            "person_titles": [campaign.icp_tanimi.get("hedef_pozisyon", "")],
            "per_page": limit
        }
        
        raw_people = self.apollo.search_people(query)
        leads = []
        
        print(f"Apollo'dan {len(raw_people)} kişi bulundu. Hunter ile doğrulanıyor...")
        
        for person in raw_people:
            email = person.get("email")
            if not email:
                continue
                
            status = self.hunter.verify_email(email)
            print(f"- {email}: {status}")
            
            if status in ["deliverable", "risky"]:
                lead = Lead(
                    lead_id=person.get("id"),
                    ad=person.get("first_name", ""),
                    soyad=person.get("last_name", ""),
                    email=email,
                    email_dogrulama_durumu=status,
                    sirket=person.get("organization", {}).get("name", ""),
                    pozisyon=person.get("title", ""),
                    sektor=person.get("organization", {}).get("industry", campaign.hedef_sektor),
                    linkedin=person.get("linkedin_url", ""),
                    kampanya_id=campaign.kampanya_id
                )
                leads.append(lead)
                
        return leads

    def generate_contents_for_leads(self, campaign: Campaign, leads: List[Lead], template: str) -> Dict[str, Dict[str, str]]:
        print(f"[{campaign.ad}] LLM ile kişiselleştirilmiş içerikler üretiliyor...")
        lead_contents = {}
        for lead in leads:
            content = self.llm.generate_email(lead, campaign, template)
            if content.get("subject") and content.get("body"):
                lead_contents[lead.lead_id] = content
            # Add sleep to avoid rate limiting
            time.sleep(1)
            
        return lead_contents

    def send_initial_emails(self, campaign: Campaign, leads: List[Lead], contents: Dict[str, Dict[str, str]]):
        print(f"[{campaign.ad}] Gmail API kullanılarak iletim başlatılıyor...")
        if not self.gmail:
            try:
                self.gmail = GmailClient()
            except Exception as e:
                print(f"Gmail başlatılamadı (credentials.json eksik olabilir): {e}")
                return

        for lead in leads:
            content = contents.get(lead.lead_id)
            if not content:
                continue
                
            print(f"- {lead.email} adresine mail gönderiliyor...")
            result = self.gmail.send_email(
                to=lead.email,
                subject=content.get("subject"),
                body=content.get("body")
            )
            
            if result.get("status") == "success":
                print(f"  Başarılı! (Message ID: {result.get('message_id')})")
                lead.sequence_durumu.mevcut_adim = 1
                lead.sequence_durumu.son_gonderim_tarihi = time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                print(f"  Hata: {result.get('error_message')}")
            
            # Use gonderim_araligi
            time.sleep(campaign.sequence_kurallari.gonderim_araligi * 60)

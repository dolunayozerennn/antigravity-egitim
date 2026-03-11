import sys
import os

# Ensure src is in standard path for execution if run directly from inside src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.campaign import Campaign, SequenceConfig
from src.orchestrator import CampaignOrchestrator

def main():
    print("🚀 Antigravity B2B Outreach Sistemi Başlatılıyor...")
    
    # Example Campaign Initialization
    ornek_kampanya = Campaign(
        kampanya_id="CMP-001",
        ad="SaaS Event Collaboration",
        aciklama="Tech etkinlikleri için B2B iş ortaklıkları arayışı.",
        hedef_sektor="SaaS",
        icp_tanimi={"hedef_pozisyon": "Marketing Director", "sirket_buyuklugu": "50-200"},
        deger_onerisi="Etkinliğimizde doğru kitleyle buluşarak marka bilinirliğinizi artırabilirsiniz.",
        dil="TR",
        sequence_kurallari=SequenceConfig(gonderim_araligi=1) # 1 dk for testing
    )
    
    print(f"\n[{ornek_kampanya.ad}] Kampanyası Ayarlandı.")
    print("Hedef Sektör:", ornek_kampanya.hedef_sektor)
    print("Değer Önerisi:", ornek_kampanya.deger_onerisi)

    # Initialize Orchestrator
    orchestrator = CampaignOrchestrator()
    
    # 1. Lead Generation (Layer 1)
    print("\nAdım 1: Apollo ve Hunter.io üzerinden Lead Generation")
    
    # MOCK LEAD FOR TESTING (Because Apollo keys likely not available)
    from src.models.lead import Lead, EnrichmentData, SequenceStatus
    mock_lead = Lead(
        lead_id="L-001",
        ad="Ahmet",
        soyad="Yılmaz",
        email="ahmet.yilmaz@ornek-saas.com",
        email_dogrulama_durumu="deliverable",
        sirket="Örnek SaaS Ltd.",
        pozisyon="Marketing Director",
        sektor="SaaS",
        enrichment=EnrichmentData(
            teknoloji_stacki=["React", "AWS"],
            buyume_sinyalleri=["Son 3 ayda 10 yeni stajyer"]
        ),
        kampanya_id=ornek_kampanya.kampanya_id,
        sequence_durumu=SequenceStatus()
    )
    leads = [mock_lead]
    
    # 2. LLM Content (Layer 2)
    print("\nAdım 2: OpenAI ile Kişiselleştirilmiş İçerik Üretimi")
    sample_template = """
Merhaba {ad},
Şirketiniz {sirket}'in büyüme adımlarını yakından takip ediyorum. Özellikle {kanca}.
Biz {deger_onerisi}.
Sektörünüzdeki şu problemi {sektor_pain_point} aşmak için harika bir fırsat.
Görüşelim mi?
{cta}
    """
    
    # We won't call the actual LLM API without keys unless to print flow.
    # contents = orchestrator.generate_contents_for_leads(ornek_kampanya, leads, sample_template)
    contents = {
        mock_lead.lead_id: {
            "subject": f"İşbirliği Fırsatı - {mock_lead.ad}",
            "body": f"Merhaba {mock_lead.ad},\n\nÖrnek SaaS Ltd.'in büyüme adımlarını yakından takip ediyorum.\n\n{ornek_kampanya.deger_onerisi}\n\nGörüşelim mi?"
        }
    }
    
    # 3. Outreach (Layer 3)
    print("\nAdım 3: Gmail API üzerinden Gönderim ve Sequence Başlatma")
    print(f"[{mock_lead.email}] -> Body:\n{contents[mock_lead.lead_id]['body']}")
    # orchestrator.send_initial_emails(ornek_kampanya, leads, contents)
    
    print("\n✅ Sistem kurulumu ve entegrasyon temeli hazır.")

if __name__ == "__main__":
    main()

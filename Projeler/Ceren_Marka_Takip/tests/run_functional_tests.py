import sys
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Proje kökünü sys.path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from main import main
from utils import state_manager

class TestCerenMarkaTakipE2E(unittest.TestCase):
    
    def setUp(self):
        # State tarihçesini test için sıfırla/başka dosyaya al
        self.test_state_file = os.path.join(BASE_DIR, "data", "test_reminder_history.json")
        self.original_state_file = state_manager.STATE_FILE
        state_manager.STATE_FILE = self.test_state_file

        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)

        # Fail-fast kontrolünü geçmek için mock env
        os.environ["GROQ_API_KEY"] = "mock_groq_key"

    def tearDown(self):
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)
        
        # State dosya yolunu geri al
        state_manager.STATE_FILE = self.original_state_file

    @patch("core.notifier.send_reminder_to_ceren")
    @patch("core.notifier.send_error_alert")
    @patch("core.notifier.send_weekly_report")
    @patch("core.thread_analyzer.analyze_thread")
    @patch("core.gmail_scanner.scan_all_inboxes")
    def test_end_to_end_scenarios(
        self, 
        mock_scan_all_inboxes, 
        mock_analyze_thread,
        mock_send_weekly_report,
        mock_send_error_alert,
        mock_send_reminder_to_ceren
    ):
        """
        Senaryo 1: Marka yazdı, >48 iş saati geçti -> HATIRLAT
        Senaryo 2: Ceren yazdı, marka cevap vermedi (>48s) -> HATIRLATMA
        Senaryo 3: Spam Mail, >48 iş saati geçti -> HATIRLATMA
        Senaryo 4: Marka yazdı, <12 saat geçti -> HATIRLATMA (stale değil)
        """
        
        now = datetime.utcnow()
        past_stale = now - timedelta(days=5) # Kesinlikle stale (>48 iş saati olacak kadar eski)
        past_fresh = now - timedelta(hours=5) # Fresh
        
        # Scanner mock çıktısı
        mock_scan_all_inboxes.return_value = [
            {
                "thread_id": "thread_1",
                "subject": "Case 1: Nike İşbirliği Teklifi (Stale, Reminder)",
                "last_message_date": past_stale,
                "last_sender_email": "marketing@nike.com",
                "message_count": 2,
                "participants": ["ceren@dolunay.ai", "marketing@nike.com"],
                "message_snippets": ["Merhaba Ceren, teklif nedir?"],
                "gmail_link": "http://gmail.com/1",
                "found_in_accounts": ["ceren"]
            },
            {
                "thread_id": "thread_2",
                "subject": "Case 2: Puma İşbirliği (Ceren cevap bekliyor)",
                "last_message_date": past_stale,
                "last_sender_email": "ceren@dolunay.ai",
                "message_count": 3,
                "participants": ["ceren@dolunay.ai", "pr@puma.com"],
                "message_snippets": ["Fiyat listemizi iletiyorum."],
                "gmail_link": "http://gmail.com/2",
                "found_in_accounts": ["ceren"]
            },
            {
                "thread_id": "thread_3",
                "subject": "Case 3: Fatura Onay (Marka değil)",
                "last_message_date": past_stale,
                "last_sender_email": "muhasebe@sirket.com",
                "message_count": 1,
                "participants": ["ceren@dolunay.ai", "muhasebe@sirket.com"],
                "message_snippets": ["Aylık fatura ektedir."],
                "gmail_link": "http://gmail.com/3",
                "found_in_accounts": ["ceren"]
            },
            {
                "thread_id": "thread_4",
                "subject": "Case 4: Adidas İşbirliği (Stale DEĞİL)",
                "last_message_date": past_fresh,
                "last_sender_email": "collab@adidas.com",
                "message_count": 1,
                "participants": ["ceren@dolunay.ai", "collab@adidas.com"],
                "message_snippets": ["Merhaba Ceren ilgilenir misiniz?"],
                "gmail_link": "http://gmail.com/4",
                "found_in_accounts": ["ceren"]
            }
        ]

        # LLM mock response
        def mock_llm_response(text, prompt):
            if "Nike" in text:
                return {
                    "is_brand_collaboration": True,
                    "brand_name": "Nike",
                    "last_sender": "brand",
                    "action_needed_by_ceren": True,
                    "reason": "Marka teklif donusu bekliyor",
                    "thread_status": "waiting_for_ceren",
                    "urgency": "medium"
                }
            elif "Puma" in text:
                return {
                    "is_brand_collaboration": True,
                    "brand_name": "Puma",
                    "last_sender": "ceren",
                    "action_needed_by_ceren": False,
                    "reason": "Ceren fiyat iletmis cvp bekliyor",
                    "thread_status": "waiting_for_brand",
                    "urgency": "low"
                }
            elif "Fatura" in text:
                return {
                    "is_brand_collaboration": False,
                    "brand_name": None,
                    "last_sender": "other",
                    "action_needed_by_ceren": False,
                    "reason": "Muhasebe faturasi",
                    "thread_status": "closed",
                    "urgency": "low"
                }
            return None

        mock_analyze_thread.side_effect = mock_llm_response

        # Mimarın çalıştırılması
        main(dry_run=False)

        # Doğrulamalar (Asserts)
        # Sadece Thread 1 (Nike) için bildirim gitmesi gerek. (Puma, Ceren'i bekliyor; Fatura marka değil; Adidas taze)
        self.assertEqual(mock_send_reminder_to_ceren.call_count, 1, "Beklenenden farklı sayıda hatırlatma tetiklendi.")
        
        notified_threads = mock_send_reminder_to_ceren.call_args[0][0]
        self.assertEqual(len(notified_threads), 1)
        self.assertEqual(notified_threads[0]["thread_id"], "thread_1")
        self.assertEqual(notified_threads[0]["brand_name"], "Nike")

        print("\n✔ Senaryolar başarıyla test edildi: Yalnızca stale olan ve aksiyon gereken marka mailleri tespit edildi.")

         # 2. Tur Çalıştırma: Duplicate test (Aynı thread 2. kez geldiğinde, cooldown'da olduğu için gönderilmez)
        mock_send_reminder_to_ceren.reset_mock()
        main(dry_run=False)
        self.assertEqual(mock_send_reminder_to_ceren.call_count, 0, "Duplicate engeli aşıldı, aynı mail hemen 2 defa gitti!")
        print("✔ Cooldown/Duplicate mekanizması başarıyla test edildi: Aynı takip hatırlatması peş peşe gönderilmedi.\n")

if __name__ == "__main__":
    unittest.main()

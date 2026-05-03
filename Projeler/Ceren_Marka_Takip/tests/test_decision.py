"""Karar kuralı testleri — core/decision.py."""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core import decision  # noqa: E402


class TestLlmToStatus(unittest.TestCase):
    def _llm(self, **kwargs):
        base = {
            "category": "brand_collab_offer",
            "confidence": 0.9,
            "is_personalized": True,
            "last_sender": "brand",
            "thread_status": "active",
            "reason": "test",
        }
        base.update(kwargs)
        return base

    def test_real_collab_becomes_open(self):
        status, _ = decision.llm_to_status(self._llm())
        self.assertEqual(status, "open")

    def test_promotional_marketing_becomes_false_positive(self):
        status, reason = decision.llm_to_status(self._llm(category="promotional_marketing"))
        self.assertEqual(status, "false_positive")
        self.assertIn("promotional_marketing", reason)

    def test_transactional_becomes_false_positive(self):
        status, _ = decision.llm_to_status(self._llm(category="transactional"))
        self.assertEqual(status, "false_positive")

    def test_low_confidence_becomes_false_positive(self):
        status, reason = decision.llm_to_status(self._llm(confidence=0.5))
        self.assertEqual(status, "false_positive")
        self.assertIn("düşük güven", reason)

    def test_non_personalized_becomes_false_positive(self):
        status, reason = decision.llm_to_status(self._llm(is_personalized=False))
        self.assertEqual(status, "false_positive")
        self.assertIn("toplu mail", reason)

    def test_ceren_replied_transitions_to_responded(self):
        status, _ = decision.llm_to_status(
            self._llm(last_sender="ceren", thread_status="responded_by_ceren")
        )
        self.assertEqual(status, "responded_by_ceren")

    def test_llm_says_closed_becomes_closed_lost(self):
        status, _ = decision.llm_to_status(self._llm(thread_status="closed"))
        self.assertEqual(status, "closed_lost")

    def test_terminal_status_is_respected(self):
        # Kullanıcı manuel olarak false_positive yapmışsa, LLM "open" demek istese bile dokunma
        status, reason = decision.llm_to_status(
            self._llm(), current_status="false_positive"
        )
        self.assertEqual(status, "false_positive")

    def test_terminal_closed_won_is_respected(self):
        status, _ = decision.llm_to_status(self._llm(), current_status="closed_won")
        self.assertEqual(status, "closed_won")


class TestShouldRunLlm(unittest.TestCase):
    def test_new_thread_runs_llm(self):
        self.assertTrue(decision.should_run_llm(None, "2026-05-01T10:00:00"))

    def test_terminal_status_skips(self):
        rec = {"status": "false_positive", "last_message_at": "2026-05-01T10:00:00"}
        self.assertFalse(decision.should_run_llm(rec, "2026-05-02T10:00:00"))

        rec = {"status": "closed_won", "last_message_at": "2026-05-01T10:00:00"}
        self.assertFalse(decision.should_run_llm(rec, "2026-05-02T10:00:00"))

    def test_open_unchanged_skips(self):
        rec = {"status": "open", "last_message_at": "2026-05-01T10:00:00"}
        self.assertFalse(decision.should_run_llm(rec, "2026-05-01T10:00:00"))

    def test_open_with_new_message_runs(self):
        rec = {"status": "open", "last_message_at": "2026-05-01T10:00:00"}
        self.assertTrue(decision.should_run_llm(rec, "2026-05-02T15:30:00"))

    def test_responded_with_new_message_runs(self):
        # Ceren cevap yazmıştı, ama marka tekrar yazdı → yeniden değerlendir
        rec = {"status": "responded_by_ceren", "last_message_at": "2026-05-01T10:00:00"}
        self.assertTrue(decision.should_run_llm(rec, "2026-05-02T15:30:00"))


if __name__ == "__main__":
    unittest.main()

"""
Ceren_Marka_Takip — Karar Kuralları
=====================================
LLM çıktısını alır, "bu thread için hangi Status?" ve
"digest'e girmeli mi?" sorularını cevaplar.

Tek yerde toplanmasının amacı: Notion DB'deki manuel düzenlemelerin
(false_positive, closed_*) sistem tarafından override edilmemesi.
"""

from typing import Dict, Any, Optional, Tuple

# LLM kategorisi → "açık iş" mi? (digest'e girmeye aday)
COLLAB_CATEGORIES = {"brand_collab_offer", "brand_collab_followup"}

# LLM güveni eşiği
MIN_CONFIDENCE = 0.75

# Manuel olarak terminal duruma çekilmiş thread'ler — sistem dokunmaz
TERMINAL_STATUSES = {"closed_won", "closed_lost", "false_positive"}


def llm_to_status(
    llm_result: Dict[str, Any],
    current_status: Optional[str] = None,
) -> Tuple[str, str]:
    """
    LLM analiz sonucundan yeni Status değerini ve gerekçesini üret.

    Returns:
        (new_status, reason)
        new_status: "open" | "responded_by_ceren" | "false_positive" | <current>
        reason: Notion'a yazılacak kısa açıklama
    """
    # Kullanıcı manuel olarak kapatmışsa dokunma
    if current_status in TERMINAL_STATUSES:
        return current_status, llm_result.get("reason", "manuel kapatıldı")

    category = (llm_result.get("category") or "").strip()
    confidence = float(llm_result.get("confidence") or 0.0)
    is_personalized = bool(llm_result.get("is_personalized"))
    last_sender = llm_result.get("last_sender")
    thread_status_llm = llm_result.get("thread_status")
    reason = llm_result.get("reason") or ""

    # Eşikleri geçemiyorsa → bu sistem için ilgisiz, false_positive olarak işaretle
    if category not in COLLAB_CATEGORIES:
        return "false_positive", f"[{category}] {reason}"
    if not is_personalized:
        return "false_positive", f"toplu mail (is_personalized=false): {reason}"
    if confidence < MIN_CONFIDENCE:
        return "false_positive", f"düşük güven ({confidence:.2f}): {reason}"

    # Marka collab + yüksek güven + kişisel → şimdi sıra durumda
    # Ceren cevap yazmışsa, top onun değil → responded_by_ceren
    if last_sender == "ceren" or thread_status_llm == "responded_by_ceren":
        return "responded_by_ceren", reason

    # LLM "closed" demişse kapat
    if thread_status_llm == "closed":
        return "closed_lost", reason or "LLM thread'i kapanmış olarak işaretledi"

    # Aksi halde açık iş — Ceren'in cevap vermesi gereken bir collab
    return "open", reason


def should_run_llm(
    notion_record: Optional[Dict[str, Any]],
    fresh_last_message_at: Optional[str],
) -> bool:
    """
    LLM'i bu thread için çağırmaya gerek var mı?

    Çağırırız:
    - Yeni thread (Notion'da yok)
    - Notion'da var ama Status=open ve son mesaj tarihi değişmiş (yeni mesaj geldi)

    Çağırmayız:
    - Notion'da terminal status (closed_*, false_positive)
    - Notion'da responded_by_ceren ve son mesaj değişmemiş
    - Notion'da open ama son mesaj değişmemiş (durum aynı, tekrar analiz gereksiz)
    """
    if notion_record is None:
        return True

    status = notion_record.get("status")
    if status in TERMINAL_STATUSES:
        return False

    # Son mesaj tarihi değişti mi?
    cached = (notion_record.get("last_message_at") or "")[:19]
    fresh = (fresh_last_message_at or "")[:19] if fresh_last_message_at else ""
    if cached and fresh and cached == fresh:
        return False

    return True

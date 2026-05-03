"""
Ceren_Marka_Takip — Gmail Thread Tarama
==========================================
Ceren'in inbox'ından thread'leri çeker.
"""

import logging
import base64
import email.utils
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from services.gmail_service import get_gmail_service

logger = logging.getLogger(__name__)

# Taranacak hesaplar
SCAN_ACCOUNTS = ["ceren"]

# Her hesaptan maksimum çekilecek thread sayısı (API/LLM maliyetini sınırla)
MAX_THREADS_PER_ACCOUNT = 300

# E-posta adresleri (thread'de kimin yazdığını belirlemek için)
KNOWN_EMAILS = {
    "ceren@dolunay.ai": "ceren",
}

# ── Pre-LLM Filtreleri (LLM API çağrısı yapmadan elenecekler) ──

# Subject'te bunlardan biri geçiyorsa → kesinlikle marka işbirliği DEĞİL
SUBJECT_BLOCKLIST = [
    # Sistem bildirimleri
    "lead bildirimi", "yeni lead", "lead akışı durdu",
    "notification", "new notification", "bildirim",
    "antigravity alarm", "antigravity:", "sistem hatası",
    "made updates in", "updates in",
    # Güvenlik & hesap
    "password reset", "şifre sıfırlama", "verify your", "doğrulama",
    "security alert", "güvenlik uyarısı",
    # Finans & sipariş
    "invoice", "fatura", "receipt", "makbuz",
    "shipping confirmation", "kargo takip",
    "order confirmation", "sipariş onay",
    # Abonelik & digest
    "unsubscribe", "newsletter", "haber bülteni", "e-bülten",
    "your subscription", "aboneliğiniz",
    "weekly digest", "daily digest", "haftalık özet",
    "bültenimize hoş geldin", "aboneliğinizi onayla",
    # Otomatik yanıtlar
    "out of office", "otomatik yanıt",
    "calendar invitation", "takvim daveti",
    # Notion bildirimleri
    "commented in", "for you in",
    # Ödeme uyarıları (kendi sistemimiz)
    "geciken ödeme", "ödeme uyarısı", "kritik: ödeme",
    # Udemy / platform istatistikleri
    "istatistiklerinize göz", "your stats", "your earnings",
    "yeni istatistik", "instructor revenue",
    # Affiliate raporları
    "affiliate activity", "affiliate report",
    # Tarama/evrak
    "camscanner",
    # Mozi/kupon/tanıtım bülteni
    "mozi minute", "play your hand",
    # Kampanya/indirim — toplu marketing göstergeleri
    "kampanya", "indirim", "flaş satış", "mega indirim",
    "%50 indirim", "fırsat", "son saatler", "stoklarla sınırlı",
]

# Bu sender domain'lerden gelen e-postalar → otomatik atla
# Genişletilmiş: toplu mail prefix'leri eklendi (marketing@, bulletin@, vs.)
# Not: "info", "team", "hello", "support", "contact" kasıtlı olarak DAHIL EDILMEDİ —
# küçük/orta marka outreach'leri bu prefix'lerden gelebiliyor; onları List-Unsubscribe
# header sinyaliyle ayırt ediyoruz.
SENDER_BLOCKLIST_DOMAINS = [
    "noreply", "no-reply", "notifications", "mailer-daemon",
    "postmaster", "donotreply", "auto-reply", "automated",
    "marketing", "bulletin", "campaigns", "newsletter", "news",
    "promo", "promotions", "deals",
]

# Bu tam sender adreslerini atla
SENDER_BLOCKLIST_EMAILS = [
    "calendar-notification@google.com",
    "notifications@github.com",
    "noreply@medium.com",
    "noreply@youtube.com",
    "noreply@linkedin.com",
    "notify@twitter.com",
    "noreply@udemy.com",
    "do-not-reply@udemy.com",
    "notification@notion.so",
    "noreply@notion.so",
]


def _should_skip_thread(
    subject: str,
    last_sender_email: str,
    list_unsubscribe: str = "",
    precedence: str = "",
) -> bool:
    """
    Pre-LLM filtre: Kesinlikle marka işbirliği olamayacak thread'leri atla.
    LLM çağrısından önce çalışır — token tasarrufu + false positive azaltma.
    """
    subject_lower = subject.lower()
    sender_lower = last_sender_email.lower()

    # Subject blocklist kontrolü
    for blocked in SUBJECT_BLOCKLIST:
        if blocked in subject_lower:
            return True

    # Sender email blocklist
    if sender_lower in SENDER_BLOCKLIST_EMAILS:
        return True

    # Sender domain blocklist (noreply@, marketing@, bulletin@, vs.)
    sender_local = sender_lower.split("@")[0] if "@" in sender_lower else ""
    for blocked_prefix in SENDER_BLOCKLIST_DOMAINS:
        if blocked_prefix in sender_local:
            return True

    # Bulk-mail göstergeleri — gerçek collab outreach'lerinde olmaz
    # List-Unsubscribe header'ı bulk mailing list standardıdır (RFC 2369)
    if list_unsubscribe:
        return True
    # Precedence: bulk / list / junk → toplu mail
    if precedence and precedence.lower().strip() in ("bulk", "list", "junk"):
        return True

    return False


def scan_all_inboxes(days: int = 15) -> List[Dict[str, Any]]:
    """
    Tüm inbox'ları tara ve thread listesi döndür.
    
    Args:
        days: Geriye dönük kaç gün taranacak (varsayılan: 15)
    
    Returns:
        Deduplicate edilmiş thread listesi
    """
    all_threads = {}  # thread_id → thread data

    for account in SCAN_ACCOUNTS:
        try:
            threads = _scan_inbox(account, days)
            for thread in threads:
                tid = thread["thread_id"]
                if tid not in all_threads:
                    all_threads[tid] = thread
                else:
                    # Mevcut thread'e ek bilgi ekle
                    existing = all_threads[tid]
                    existing["found_in_accounts"].append(account)
            
            logger.info(f"✅ {account}: {len(threads)} thread bulundu")
        except Exception as e:
            logger.error(f"❌ {account} inbox taranamadı: {e}", exc_info=True)

    result = list(all_threads.values())
    logger.info(f"Toplam unique thread: {len(result)} ({sum(len(_scan_inbox_cached.get(a, [])) for a in SCAN_ACCOUNTS if a in _scan_inbox_cached)} ham)")
    return result

# Basit cache — aynı run'da tekrar tarama yapma
_scan_inbox_cached = {}


def _scan_inbox(account: str, days: int) -> List[Dict[str, Any]]:
    """Tek bir inbox'ı tara."""
    service = get_gmail_service(account)
    
    # Son N gündeki mesajları çek
    # Gmail kategorilerini negate et: Promotions/Social/Updates/Forums sekmelerinde olanlar zaten collab değil.
    after_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = (
        f"after:{after_date} "
        f"-category:promotions -category:social -category:updates -category:forums"
    )

    threads = []
    skipped = 0
    page_token = None

    while True:
        results = service.users().threads().list(
            userId='me',
            q=query,
            pageToken=page_token,
            maxResults=100,
        ).execute()

        thread_list = results.get('threads', [])
        if not thread_list:
            break

        for thread_meta in thread_list:
            thread_data = _get_thread_detail(service, thread_meta['id'])
            if thread_data:
                # Pre-LLM filtre: Bildirim/spam thread'lerini LLM'e göndermeden atla
                if _should_skip_thread(
                    thread_data["subject"],
                    thread_data["last_sender_email"],
                    list_unsubscribe=thread_data.get("list_unsubscribe", ""),
                    precedence=thread_data.get("precedence", ""),
                ):
                    logger.debug(f"PRE-FILTER ATLA: '{thread_data['subject'][:50]}'")
                    skipped += 1
                    continue
                thread_data["found_in_accounts"] = [account]
                threads.append(thread_data)

        page_token = results.get('nextPageToken')
        if not page_token or len(threads) >= MAX_THREADS_PER_ACCOUNT:
            break

    logger.info(f"Pre-filter: {skipped} thread bildirim/spam olarak atlandı")
    _scan_inbox_cached[account] = threads
    return threads


def _get_thread_detail(service, thread_id: str) -> Optional[Dict[str, Any]]:
    """Thread detayını çek — son mesaj bilgisi ve katılımcılar."""
    try:
        thread = service.users().threads().get(
            userId='me',
            id=thread_id,
            format='metadata',
            metadataHeaders=[
                'From', 'To', 'Cc', 'Subject', 'Date',
                'List-Unsubscribe', 'Precedence',
            ],
        ).execute()

        messages = thread.get('messages', [])
        if not messages:
            return None

        # Subject
        subject = _get_header(messages[0], 'Subject') or "(Konu yok)"

        # Son mesaj bilgisi
        last_msg = messages[-1]
        last_from = _get_header(last_msg, 'From') or ""
        last_date_str = _get_header(last_msg, 'Date') or ""
        last_date = _parse_email_date(last_date_str)

        # Son mesajı atan kim?
        last_sender_email = _extract_email(last_from)
        last_sender_role = KNOWN_EMAILS.get(last_sender_email, "brand")

        # Thread'deki tüm katılımcılar
        participants = set()
        for msg in messages:
            for header in ['From', 'To', 'Cc']:
                value = _get_header(msg, header) or ""
                for addr in value.split(','):
                    addr_clean = _extract_email(addr.strip())
                    if addr_clean:
                        participants.add(addr_clean)

        # Son 3-5 mesajın snippet'ini hazırla (LLM analizi için)
        recent_messages = messages[-5:]  # Son 5 mesaj
        message_snippets = []
        for msg in recent_messages:
            from_addr = _get_header(msg, 'From') or "?"
            snippet = msg.get('snippet', '')
            date = _get_header(msg, 'Date') or ""
            message_snippets.append(f"From: {from_addr}\nDate: {date}\n{snippet}")

        # Bulk-mail göstergeleri (son mesajdan)
        list_unsubscribe = _get_header(last_msg, 'List-Unsubscribe') or ""
        precedence = _get_header(last_msg, 'Precedence') or ""

        return {
            "thread_id": thread_id,
            "subject": subject,
            "last_message_date": last_date,
            "last_sender_email": last_sender_email,
            "last_sender_role": last_sender_role,
            "message_count": len(messages),
            "participants": list(participants),
            "message_snippets": message_snippets,
            "gmail_link": f"https://mail.google.com/mail/u/0/#inbox/{thread_id}",
            "list_unsubscribe": list_unsubscribe,
            "precedence": precedence,
            "found_in_accounts": [],
        }

    except Exception as e:
        logger.warning(f"Thread {thread_id} detayı alınamadı: {e}")
        return None


def _get_header(message: dict, header_name: str) -> Optional[str]:
    """Mesaj header'ından değer çıkar."""
    headers = message.get('payload', {}).get('headers', [])
    for h in headers:
        if h['name'].lower() == header_name.lower():
            return h['value']
    return None


def _extract_email(from_str: str) -> str:
    """'Ceren <ceren@dolunay.ai>' → 'ceren@dolunay.ai'"""
    if '<' in from_str and '>' in from_str:
        return from_str.split('<')[1].split('>')[0].strip().lower()
    return from_str.strip().lower()


def _parse_email_date(date_str: str) -> Optional[datetime]:
    """E-posta tarih stringini datetime'a çevir."""
    if not date_str:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        # UTC'ye çevir
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    except Exception:
        try:
            # Fallback: internal date milisniye
            return datetime.utcfromtimestamp(int(date_str) / 1000)
        except Exception:
            return None

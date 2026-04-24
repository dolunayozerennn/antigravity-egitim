"""
Lead Generator — Aşama 1 MVP
Apify Google Maps Scraper → Lead Scoring → Notion'a yaz.

Kullanım:
  python -m src.lead_generator --location "Kadıköy, Istanbul" --category "restaurant"
"""
from __future__ import annotations
import argparse
import re
import sys

from apify_client import ApifyClient

from src import config
from src.notion_helper import create_lead_db, write_lead

logger = config.logger


# ============================================================================
# ANA GÖLGE MODU — Supabase Logger (opsiyonel, yoksa disabled)
# ============================================================================

def _init_shadow_logger():
    """Supabase cred'leri varsa logger döndür, yoksa None (disabled mod)."""
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        logger.info("Supabase cred'leri eksik — Gölge Modu devre dışı.")
        return None
    try:
        from _skills.providers.supabase_logger import SupabaseLoggerNode
        return SupabaseLoggerNode(
            supabase_url=config.SUPABASE_URL,
            supabase_key=config.SUPABASE_KEY,
        )
    except ImportError:
        logger.warning("_skills.providers.supabase_logger import edilemedi — Gölge Modu devre dışı.")
        return None

_shadow = _init_shadow_logger()


# ============================================================================
# 1) APIFY SCRAPE
# ============================================================================

def scrape_places(
    location: str,
    category: str,
    max_results: int = config.MAX_PLACES_PER_SEARCH,
) -> list[dict]:
    """
    Apify Google Maps Scraper ile işletme verisi çeker.
    Fail-over: KEY_1 başarısız → KEY_2 ile dener.
    """
    run_input = {
        "searchStringsArray": [category],
        "locationQuery": location,
        "maxCrawledPlacesPerSearch": max_results,
        "language": "tr",
        "countryCode": "tr",
        "searchMatching": "all",
        "website": "allPlaces",
        "skipClosedPlaces": True,
        "scrapePlaceDetailPage": True,
        "scrapeContacts": True,
        "scrapeSocialMediaProfiles": {
            "instagrams": True,
            "facebooks": False,
            "youtubes": False,
        },
        "maxImages": 0,
        "maxReviews": 10,
        "reviewsSort": "newest",
        "scrapeReviewsPersonalData": False,
        "placeMinimumStars": "threeAndHalf",
    }

    keys = [config.APIFY_API_KEY_1]
    if config.APIFY_API_KEY_2:
        keys.append(config.APIFY_API_KEY_2)

    for i, key in enumerate(keys, 1):
        try:
            logger.info("Apify çalıştırılıyor (KEY_%d)… konum=%s, kategori=%s", i, location, category)
            client = ApifyClient(key)
            run = client.actor(config.APIFY_ACTOR_ID).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            logger.info("Apify tamamlandı — %d işletme döndü.", len(items))
            return items
        except Exception as e:
            error_msg = str(e)
            if "usage hard limit" in error_msg.lower() or "quota" in error_msg.lower():
                logger.warning("Apify KEY_%d quota aşıldı, fail-over deneniyor…", i)
                continue
            logger.error("Apify hatası (KEY_%d): %s", i, error_msg, exc_info=True)
            raise

    logger.error("Tüm Apify key'leri quota aştı! Bugünkü operasyon durduruluyor.")
    return []


# ============================================================================
# 2) VERİ PARSE + NORMALIZE
# ============================================================================

def _parse_price_scale(price_str: str | None) -> tuple[str, int]:
    """
    Apify'ın price alanını fiyat skalası + puan'a çevir.
    '₺2,000+' → '$$$', 30 puan
    'Cheap'   → '$', 10 puan
    """
    if not price_str:
        return "Bilinmiyor", 15  # orta varsayım

    # Güvenli tip dönüşümü — Apify bazen int/float gönderebilir
    if not isinstance(price_str, str):
        price_str = str(price_str)

    price_lower = price_str.lower().strip()

    # TL bazlı aralıklar
    numbers = re.findall(r"[\d,.]+", price_str.replace(",", ""))
    if numbers:
        try:
            val = float(numbers[0])
            if val >= 1500:
                return "$$$", 30
            elif val >= 500:
                return "$$", 20
            else:
                return "$", 10
        except ValueError:
            pass

    # Google'ın $ sembol sistemi
    dollar_count = price_lower.count("$") + price_lower.count("₺")
    if dollar_count >= 3:
        return "$$$", 30
    elif dollar_count == 2:
        return "$$", 20
    elif dollar_count == 1:
        return "$", 10

    # Metin bazlı
    if "expensive" in price_lower or "pahalı" in price_lower:
        return "$$$", 30
    if "moderate" in price_lower or "orta" in price_lower:
        return "$$", 20
    if "cheap" in price_lower or "ucuz" in price_lower:
        return "$", 10

    return "$$", 20  # default orta


def _extract_email(item: dict) -> str | None:
    """Apify datasından e-mail çek: email alanı → emails listesi → None."""
    email = item.get("email")
    if email:
        return email

    emails = item.get("emails")
    if emails and isinstance(emails, list) and len(emails) > 0:
        return emails[0]

    return None


def _extract_instagram(item: dict) -> str | None:
    """Instagram URL'i çek."""
    instagrams = item.get("instagrams")
    if instagrams and isinstance(instagrams, list) and len(instagrams) > 0:
        return instagrams[0]
    return None


def parse_place(item: dict) -> dict:
    """Apify raw item → normalize edilmiş lead dict."""
    price_scale, price_score = _parse_price_scale(item.get("price"))

    google_maps_url = None
    place_id = item.get("placeId", "")
    if place_id:
        google_maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

    # Güvenli sayısal dönüşüm — Apify bazen string/null gönderebilir
    try:
        stars = float(item.get("totalScore", 0) or 0)
    except (TypeError, ValueError):
        stars = 0
    try:
        reviews_count = int(item.get("reviewsCount", 0) or 0)
    except (TypeError, ValueError):
        reviews_count = 0

    return {
        "name": item.get("title", "N/A"),
        "category": item.get("categoryName", "Genel") or "Genel",
        "address": item.get("address", ""),
        "city": item.get("city", "Bilinmiyor"),
        "phone": item.get("phone"),
        "website": item.get("website"),
        "email": _extract_email(item),
        "instagram": _extract_instagram(item),
        "stars": stars,
        "reviews_count": reviews_count,
        "price_scale": price_scale,
        "price_score": price_score,
        "place_id": place_id,
        "google_maps_url": google_maps_url,
    }


# ============================================================================
# 3) LEAD SCORING
# ============================================================================

def score_lead(lead: dict) -> float:
    """
    Plan v2'deki formül (LLM skoru hariç — sonraki aşamada eklenir):

    Skor =
      min(yorum_sayısı / 100, 1) × 25      # max 25 puan — müşteri yoğunluğu
      + max(0, (yıldız - 3)) × 15           # 3 yıldız = 0, 5 yıldız = 30
      + fiyat_skalası_puanı                  # $ = 10, $$ = 20, $$$ = 30
      (+ llm_gelir_potansiyeli × 1.5)       # → sonraki aşama

    Toplam: 0-85 aralığı (LLM olmadan max 85)
    """
    reviews = lead.get("reviews_count", 0)
    stars = lead.get("stars", 0)
    price_pts = lead.get("price_score", 20)

    review_score = min(reviews / 100, 1.0) * 25
    star_score = max(0, (stars - 3)) * 15
    price_score = price_pts

    total = review_score + star_score + price_score
    return round(min(total, 100), 1)


# ============================================================================
# 4) ANA AKIŞ
# ============================================================================

def ensure_notion_db() -> str:
    """Lead Onay DB var mı kontrol et, yoksa oluştur."""
    db_id = config.NOTION_LEAD_DB_ID
    if db_id:
        logger.info("Mevcut Notion DB kullanılıyor: %s", db_id)
        return db_id

    logger.info("Notion Lead Onay DB bulunamadı, oluşturuluyor…")
    db_id = create_lead_db(config.NOTION_COCKPIT_PAGE_ID)
    logger.info("⚠️  DB oluşturuldu: %s", db_id)
    logger.info("⚠️  Bu ID'yi config.py'deki NOTION_LEAD_DB_ID'ye veya master.env'ye ekle!")
    return db_id


def run(location: str, category: str, max_results: int | None = None):
    """Uçtan uca: Scrape → Parse → Score → Notion'a yaz."""
    max_res = max_results or config.MAX_PLACES_PER_SEARCH

    # 1) Scrape
    try:
        raw_items = scrape_places(location, category, max_res)
    except Exception as e:
        # Gölge Modu: Hata anında raw context kaydet
        if _shadow:
            _shadow.safe_log(
                project_name="Web_Site_Satis_Otomasyonu",
                status="ERROR",
                message=f"Apify scrape çöktü: {str(e)}",
                details={"stage": "apify_scrape", "error_type": type(e).__name__},
                raw_payload={"location": location, "category": category, "max_results": max_res},
            )
        raise

    if not raw_items:
        logger.warning("Apify 0 sonuç döndürdü. Çıkılıyor.")
        if _shadow:
            _shadow.safe_log(
                project_name="Web_Site_Satis_Otomasyonu",
                status="WARNING",
                message="Apify 0 sonuç döndürdü",
                details={"location": location, "category": category},
            )
        return

    # Gölge Modu: Raw payload snapshot (ilk 3 item)
    if _shadow:
        _shadow.safe_log(
            project_name="Web_Site_Satis_Otomasyonu",
            status="SHADOW_SNAPSHOT",
            message=f"Apify raw payload — {len(raw_items)} items",
            details={"location": location, "category": category, "count": len(raw_items)},
            raw_payload={"items_sample": raw_items[:3]},
        )

    # 2) Parse + Score
    leads = []
    for item in raw_items:
        lead = parse_place(item)
        lead["score"] = score_lead(lead)
        leads.append(lead)

    # 3) Eşik filtresi (< 50 elenir)
    qualified = [l for l in leads if l["score"] >= config.SCORE_THRESHOLD_MIN]
    eliminated = len(leads) - len(qualified)

    logger.info(
        "Skorlama tamamlandı — Toplam: %d | Yerleşen: %d | Elenen (<%d): %d",
        len(leads), len(qualified), config.SCORE_THRESHOLD_MIN, eliminated,
    )

    # Debug: tüm skorları yazdır
    for l in leads:
        flag = "✅" if l["score"] >= config.SCORE_THRESHOLD_MIN else "❌"
        logger.info(
            "  %s %s — Skor: %.1f (⭐%.1f | 💬%d | 💰%s)",
            flag, l["name"], l["score"], l["stars"], l["reviews_count"], l["price_scale"],
        )

    if not qualified:
        logger.warning("Hiçbir lead eşiği geçemedi. Notion'a yazılacak bir şey yok.")
        return

    # 4) Notion'a yaz
    db_id = ensure_notion_db()
    written = 0
    skipped = 0
    for lead in qualified:
        result = write_lead(db_id, lead)
        if result:
            written += 1
        else:
            skipped += 1

    logger.info(
        "Notion yazımı tamamlandı — Yazılan: %d | Atlanan (duplicate): %d",
        written, skipped,
    )

    # Gölge Modu: Pipeline sonuç logu
    if _shadow:
        _shadow.safe_log(
            project_name="Web_Site_Satis_Otomasyonu",
            status="OK" if written > 0 else "WARNING",
            message=f"Pipeline tamamlandı — Yazılan: {written}, Atlanan: {skipped}, Elenen: {eliminated}",
            details={
                "location": location,
                "category": category,
                "total_scraped": len(raw_items),
                "qualified": len(qualified),
                "written": written,
                "skipped": skipped,
                "eliminated": eliminated,
            },
        )


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Web Site Satış Otomasyonu — Lead Generator (Aşama 1)"
    )
    parser.add_argument(
        "--location", "-l",
        default="Kadıköy, Istanbul",
        help="Google Maps arama konumu (default: Kadıköy, Istanbul)",
    )
    parser.add_argument(
        "--category", "-c",
        default="restaurant",
        help="Aranacak sektör/kategori (default: restaurant)",
    )
    parser.add_argument(
        "--max", "-m",
        type=int,
        default=None,
        help=f"Maksimum sonuç sayısı (default: {config.MAX_PLACES_PER_SEARCH})",
    )
    args = parser.parse_args()
    run(args.location, args.category, args.max)


if __name__ == "__main__":
    main()

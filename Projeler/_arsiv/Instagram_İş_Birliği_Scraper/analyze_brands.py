#!/usr/bin/env python3
"""
Caption metinlerinden marka isimlerini tespit eder ve yapay zeka odaklı
markaları filtreler.

Çıktı: data/ai_brands.json
"""

import json
import re
import sys
from collections import defaultdict

INPUT_PATH = "data/raw_reels.json"
OUTPUT_PATH = "data/ai_brands.json"

# İş birliği belirteçleri (caption'da bunlardan biri varsa sponsorlu içerik)
COLLAB_MARKERS_TR = [
    "işbirliği", "iş birliği", "reklam", "sponsorlu",
    "sponsor", "ortaklık", "tanıtım",
]
COLLAB_MARKERS_EN = [
    "ad ", " ad\n", "#ad ", "sponsored", "partnership",
    "collab", "collaboration", "paid partnership",
]


def load_reels(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_mentions_from_caption(caption: str) -> list[str]:
    """Caption metninden @mention'ları çıkarır."""
    return re.findall(r"@([\w.]+)", caption)


def normalize_mention(mention: str) -> str:
    """Mention'ı temizler (trailing dots vs.)."""
    return mention.strip().rstrip(".").lower()


def has_collab_marker(caption: str) -> bool:
    """Caption'da iş birliği belirteci var mı?"""
    cap_lower = caption.lower()
    for marker in COLLAB_MARKERS_TR + COLLAB_MARKERS_EN:
        if marker in cap_lower:
            return True
    # /işbirliği formatı (başında slash)
    if "/işbirliği" in cap_lower or "/iş birliği" in cap_lower:
        return True
    return False


def extract_mentions_from_field(mentions_field) -> list[str]:
    """Apify mentions alanından (str list veya dict list) kullanıcı adlarını çıkarır."""
    results = []
    if not mentions_field:
        return results
    for m in mentions_field:
        if isinstance(m, str):
            results.append(normalize_mention(m))
        elif isinstance(m, dict):
            username = m.get("username", "")
            if username:
                results.append(normalize_mention(username))
    return results


def analyze_reels(reels: list[dict]) -> dict:
    """
    Her reel'i analiz ederek iş birliği yapılan markaları tespit eder.

    Dönen yapı:
    {
      "marka_adi": {
        "mention_count": int,
        "sources": [ { "profil", "caption_snippet", "url", "is_collab" } ],
        "instagram_handle": str,
      }
    }
    """
    brands = defaultdict(lambda: {"mention_count": 0, "sources": [], "instagram_handle": ""})

    # Kendi profil kullanıcı adlarımız (rakipler) — bunları filtreleyelim
    competitor_handles = set()
    for reel in reels:
        owner = (reel.get("ownerUsername") or "").lower()
        if owner:
            competitor_handles.add(owner)

    for reel in reels:
        caption = reel.get("caption") or ""
        owner_username = (reel.get("ownerUsername") or "").lower()
        url = reel.get("url") or ""
        is_collab = has_collab_marker(caption)

        # Mention'ları topla (hem field'dan hem caption'dan)
        mentions_from_field = extract_mentions_from_field(reel.get("mentions"))
        mentions_from_caption = [normalize_mention(m) for m in extract_mentions_from_caption(caption)]

        # Tagged users da olabilir
        tagged_users = extract_mentions_from_field(reel.get("taggedUsers"))

        all_mentions = set(mentions_from_field + mentions_from_caption + tagged_users)

        # Rakip profillerini ve sahibini filtrele
        all_mentions -= competitor_handles
        # Genel hesapları filtrele
        generic_handles = {"", "yapayzeka", "ai", "yapay_zeka"}
        all_mentions -= generic_handles

        for mention in all_mentions:
            brand = brands[mention]
            brand["mention_count"] += 1
            brand["instagram_handle"] = mention
            brand["sources"].append({
                "profil": owner_username,
                "caption_snippet": caption[:200],
                "url": url,
                "is_collab": is_collab,
            })

    return dict(brands)


# ── Bilinen AI markaları ve anahtar kelimeleri ──
KNOWN_AI_BRANDS = {
    # Genel AI platformlar
    "chatgpt", "openai", "claude", "anthropic", "gemini", "googlegemini",
    "googleturkiye", "google", "midjourney", "dalle", "dall_e",
    "stability", "stablediffusion", "copilot", "microsoftcopilot",
    "perplexity", "perplexity_ai",
    # Video AI
    "runway", "runwayml", "paborunway", "heygen", "heygenofficial",
    "synthesia", "synthesiahq", "sora", "luma_ai", "lumalabs",
    "kling", "klingai", "klingcreator", "veo", "pika", "paborunway",
    "topview_ai", "topviewai", "creatify.ai", "creatifyai",
    # Grafik / Tasarım AI
    "canva", "canvatr", "adobe", "adobefirefly", "figma",
    "pixelcut", "pixelcutapp", "napkin_ai", "napkinai",
    # Müzik AI
    "suno", "sunomusic", "udio", "udiomusic",
    # Yazı AI
    "jasper_ai", "copy.ai", "copy_ai", "writesonic",
    "aithor", "aithorai", "grammarly",
    # Kodlama AI
    "repl.it", "replit", "cursor_ai", "cursorapp",
    "v0", "v0dev", "bolt", "boltai", "bolt.new",
    "abacus.ai", "abacusai", "verdent__ai", "verdentai",
    # Diğer AI araçları
    "lexi_ai", "lexiai", "artflow", "artflowai",
    "nimai", "nim_ai", "nim.ai",
    "pollo", "polloai", "itspollo.ai", "itspollo",
    "elevenlabs", "descript", "gamma", "gammaapp",
    "beautiful.ai", "tome", "tome_app",
    "ideogram", "ideogramai", "fluxai", "flux",
    "recraft", "recraftai", "magnific", "magnific_ai",
    "krea", "krea_ai", "kreaai",
    "invideo", "invideoai", "invideo_ai",
    "captions", "captionsapp",
    "pictory", "pictoryai",
    "echtaworld", "echta",
    "raw.dijital",
}

# AI ile ilgili anahtar kelimeler (marka adında veya caption'da geçiyorsa AI markası olabilir)
AI_KEYWORDS = [
    "ai", "yapay zeka", "artificial intelligence", "machine learning",
    "deep learning", "gpt", "llm", "generative", "neural",
    "automation", "chatbot", "copilot",
]


def is_likely_ai_brand(handle: str, sources: list[dict]) -> bool:
    """Bir markanın yapay zeka odaklı olup olmadığını tahmin eder."""
    handle_lower = handle.lower()

    # Bilinen AI markaları
    if handle_lower in KNOWN_AI_BRANDS:
        return True

    # Handle'da AI keyword var mı?
    for kw in ["ai", "_ai", ".ai", "yapay", "zeka"]:
        if kw in handle_lower:
            return True

    # Caption'larda AI ile ilgili bağlam var mı?
    for src in sources:
        caption = src.get("caption_snippet", "").lower()
        ai_score = sum(1 for kw in AI_KEYWORDS if kw in caption)
        if ai_score >= 2 and src.get("is_collab"):
            return True

    return False


def main():
    reels = load_reels(INPUT_PATH)
    print(f"[INFO] {len(reels)} reel yüklendi.")

    all_brands = analyze_reels(reels)
    print(f"[INFO] {len(all_brands)} benzersiz mention tespit edildi.")

    # AI filtresi
    ai_brands = {}
    non_ai_brands = {}

    for handle, data in all_brands.items():
        if is_likely_ai_brand(handle, data["sources"]):
            ai_brands[handle] = data
        else:
            non_ai_brands[handle] = data

    # İş birliği olanları önceliklendir
    collab_brands = {}
    other_ai_brands = {}
    for handle, data in ai_brands.items():
        has_any_collab = any(s["is_collab"] for s in data["sources"])
        if has_any_collab:
            collab_brands[handle] = data
            collab_brands[handle]["has_collab_marker"] = True
        else:
            other_ai_brands[handle] = data
            other_ai_brands[handle]["has_collab_marker"] = False

    # Sonuçları kaydet
    output = {
        "summary": {
            "total_reels_analyzed": len(reels),
            "total_mentions": len(all_brands),
            "ai_brands_with_collab": len(collab_brands),
            "ai_brands_without_collab": len(other_ai_brands),
            "non_ai_mentions": len(non_ai_brands),
        },
        "ai_brands_collab": collab_brands,
        "ai_brands_other": other_ai_brands,
        "non_ai_mentions": {h: d["mention_count"] for h, d in non_ai_brands.items()},
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Sonuçlar kaydedildi → {OUTPUT_PATH}")

    # Özet
    print(f"\n{'='*60}")
    print(f"📊 MARKA ANALİZİ ÖZETİ")
    print(f"{'='*60}")
    print(f"  Analiz edilen reel    : {len(reels)}")
    print(f"  Toplam mention        : {len(all_brands)}")
    print(f"  AI markası (iş birliği): {len(collab_brands)}")
    print(f"  AI markası (diğer)    : {len(other_ai_brands)}")
    print(f"  AI dışı mention       : {len(non_ai_brands)}")
    print()

    if collab_brands:
        print("🎯 İŞ BİRLİĞİ YAPILAN AI MARKALARI:")
        for handle, data in sorted(collab_brands.items(), key=lambda x: -x[1]["mention_count"]):
            profiles = set(s["profil"] for s in data["sources"])
            print(f"  @{handle} ({data['mention_count']} mention, profiller: {', '.join(profiles)})")
        print()

    if other_ai_brands:
        print("🤖 DİĞER AI MARKALARI (iş birliği belirteci yok):")
        for handle, data in sorted(other_ai_brands.items(), key=lambda x: -x[1]["mention_count"]):
            print(f"  @{handle} ({data['mention_count']} mention)")
        print()

    print(f"{'='*60}")


if __name__ == "__main__":
    main()

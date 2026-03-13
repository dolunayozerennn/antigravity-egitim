#!/usr/bin/env python3
"""
Personalizer modülü — OpenAI GPT-4.1 ile marka bazlı email kişiselleştirme.

İlk outreach ve follow-up mailler için markaya özel, doğal Türkçe/İngilizce
email metinleri üretir.
"""

import json
import os
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Dolunay profil bilgileri (template'lerde kullanılır) ────────────────────
DOLUNAY_PROFILE = {
    "name": "Dolunay Özeren",
    "instagram": "https://www.instagram.com/dolunay_ozeren/",
    "tiktok": "https://www.tiktok.com/@dolunayozeren",
    "youtube": "https://www.youtube.com/@dolunayozeren/",
    "total_views": "100M+",
    "country": "Turkey",
    "recent_collabs": "Pixelcut, Nim AI, Aithor, TopView, Creatify, Lexi AI, ArtFlow, Temu, Printify, Syntx",
    "top_results": [
        {"brand": "Pixelcut", "views": "19.7M", "url": "https://www.instagram.com/reel/DAdt0tUN-j9/"},
        {"brand": "Nim AI", "views": "4M", "url": "https://www.instagram.com/reel/DKtuJ3cK-Yr/"},
        {"brand": "Aithor", "views": "2M", "url": "https://www.instagram.com/reel/DKHLswaK4Tj/"},
    ],
}


def _get_openai_key():
    """OpenAI API key'ini al."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    # Lokal fallback
    import re
    knowledge_path = os.path.join(BASE_DIR, "..", "..", "_knowledge", "api-anahtarlari.md")
    if os.path.exists(knowledge_path):
        with open(knowledge_path, "r") as f:
            content = f.read()
        for line in content.split("\n"):
            if "sk-proj-" in line:
                match = re.search(r"`(sk-proj-[^`]+)`", line)
                if match:
                    return match.group(1)
    return None


def _call_openai(prompt, system_prompt=None, model="gpt-4.1-nano"):
    """OpenAI API çağrısı yapar."""
    api_key = _get_openai_key()
    if not api_key:
        print("[PERSONALIZER] ⚠️ OpenAI API key bulunamadı, template kullanılacak.")
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[PERSONALIZER] OpenAI hatası: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# İLK OUTREACH
# ═══════════════════════════════════════════════════════════════════════════

OUTREACH_SYSTEM_PROMPT = """You are writing a cold outreach email from Dolunay Özeren, a content creator 
with 100M+ organic views in Turkey, to an AI/tech brand for a potential collaboration.

Rules:
- Write in English (most AI brands are global)
- Keep it SHORT — max 150 words for the body
- Be specific about the brand's product/niche
- Include 2-3 concrete results with links
- End with a LOW-PRESSURE CTA (just reply if interested)
- Tone: Professional but warm, NOT desperate
- Subject line: Creative, curiosity-driving (max 60 chars)
- Do NOT use "Dear" or overly formal language
- Do NOT use emojis in subject line

Output format (JSON):
{"subject": "...", "body_text": "...", "body_html": "..."}
"""

def generate_outreach_email(brand_info):
    """
    Markaya özel outreach emaili üretir.
    
    Args:
        brand_info: dict with marka_adi, instagram_handle, website, sirket_aciklamasi
    
    Returns:
        dict: {subject, body_text, body_html} or fallback template
    """
    brand_name = brand_info.get("marka_adi", "Brand")
    handle = brand_info.get("instagram_handle", "")
    website = brand_info.get("website", "")
    description = brand_info.get("sirket_aciklamasi", "AI tool")
    collab_context = brand_info.get("caption_samples", [])

    prompt = f"""Write an outreach email to {brand_name} (@{handle}).

Brand info:
- Website: {website}
- Description: {description}
- They work with Turkish influencers (found via competitor analysis)
- Sample captions mentioning them: {json.dumps(collab_context[:2], ensure_ascii=False)}

Dolunay's profile:
- 100M+ organic views across Instagram/TikTok/YouTube in Turkey
- Top results: Pixelcut (19.7M views), Nim AI (4M views), Aithor (2M views)
- Instagram: @dolunay_ozeren | TikTok: @dolunayozeren | YouTube: @dolunayozeren
- Links: {json.dumps([r for r in DOLUNAY_PROFILE['top_results']], ensure_ascii=False)}

Write a personalized email that references what {brand_name} does specifically."""

    result = _call_openai(prompt, OUTREACH_SYSTEM_PROMPT)
    
    if result:
        try:
            # JSON parse
            parsed = json.loads(result)
            return parsed
        except json.JSONDecodeError:
            # JSON parse başarısız — raw text olarak kullan
            pass

    # Fallback template
    return _fallback_outreach(brand_name, handle)


def _fallback_outreach(brand_name, handle):
    """OpenAI çalışmazsa kullanılacak şablon."""
    subject = f"100M views, but not yet with {brand_name}"
    
    results = "\n".join([
        f"- {r['brand']}: {r['views']} views — {r['url']}"
        for r in DOLUNAY_PROFILE["top_results"]
    ])
    
    body_text = f"""Hi {brand_name} team,

I'm Dolunay, a content creator focused on AI, tech, and digital tools. My content has reached over 100 million organic views in Turkey.

My profiles:
- Instagram: {DOLUNAY_PROFILE['instagram']}
- TikTok: {DOLUNAY_PROFILE['tiktok']}
- YouTube: {DOLUNAY_PROFILE['youtube']}

Recent results:
{results}

I've been following @{handle} and I have a viral campaign idea that could make {brand_name} stand out in the Turkish market.

If you're interested, just reply and I'll share the concept.

Best,
Dolunay"""

    body_html = f"""<p>Hi {brand_name} team,</p>

<p>I'm <strong>Dolunay</strong>, a content creator focused on AI, tech, and digital tools. My content has reached over <strong>100 million organic views</strong> in Turkey.</p>

<p>My profiles:<br>
• <a href="{DOLUNAY_PROFILE['instagram']}">Instagram</a> | 
<a href="{DOLUNAY_PROFILE['tiktok']}">TikTok</a> | 
<a href="{DOLUNAY_PROFILE['youtube']}">YouTube</a></p>

<p>Recent results:</p>
<ul>
{"".join(f'<li><strong>{r["brand"]}</strong>: {r["views"]} views — <a href="{r["url"]}">View</a></li>' for r in DOLUNAY_PROFILE["top_results"])}
</ul>

<p>I've been following @{handle} and I have a viral campaign idea that could make <strong>{brand_name}</strong> stand out in the Turkish market.</p>

<p>If you're interested, just reply and I'll share the concept.</p>

<p>Best,<br>Dolunay</p>"""

    return {"subject": subject, "body_text": body_text, "body_html": body_html}


# ═══════════════════════════════════════════════════════════════════════════
# FOLLOW-UP (Seçenek A — Web + Sosyal Medya Analizi)
# ═══════════════════════════════════════════════════════════════════════════

FOLLOWUP_SYSTEM_PROMPT = """You are writing a follow-up email for Dolunay Özeren's brand collaboration outreach.
This email must be a REPLY to a previous email that got no response.

Rules:
- Keep it VERY SHORT — max 80 words
- Reference something SPECIFIC about the brand (from the context provided)
- Add NEW VALUE — something not in the first email (new result, new idea, new angle)
- Tone: Casual, not pushy. Like bumping a message to a friend.
- Do NOT repeat the full pitch from the first email
- Do NOT apologize for following up
- End with a simple question or soft CTA
- Write in English

Output format (JSON):
{"body_text": "...", "body_html": "..."}
"""


def generate_followup_email(brand_info, brand_context=None):
    """
    Follow-up emaili üretir. Markaya özel kişiselleştirme yapar.
    
    Args:
        brand_info: dict with marka_adi, instagram_handle, website etc.
        brand_context: dict with recent_posts, website_info (from research)
    
    Returns:
        dict: {body_text, body_html}
    """
    brand_name = brand_info.get("marka_adi", "Brand")
    handle = brand_info.get("instagram_handle", "")
    website = brand_info.get("website", "")

    context_str = ""
    if brand_context:
        if brand_context.get("recent_posts"):
            context_str += f"\nRecent Instagram posts: {json.dumps(brand_context['recent_posts'][:3], ensure_ascii=False)}"
        if brand_context.get("website_summary"):
            context_str += f"\nWebsite summary: {brand_context['website_summary']}"

    prompt = f"""Write a follow-up email to {brand_name} (@{handle}).

Previous email was a collaboration pitch sent 1 week ago with no reply.

Brand context:{context_str if context_str else " No additional context available."}
Brand website: {website}

Dolunay recently achieved: Syntx campaign successfully completed (first brand from this outreach pipeline!).
Dolunay's latest views: Pixelcut reel now at 19.7M views.

Write a short, specific follow-up that gives them a reason to reply NOW."""

    result = _call_openai(prompt, FOLLOWUP_SYSTEM_PROMPT)

    if result:
        try:
            parsed = json.loads(result)
            return parsed
        except json.JSONDecodeError:
            pass

    # Fallback follow-up
    return _fallback_followup(brand_name)


def _fallback_followup(brand_name):
    """Fallback follow-up template."""
    body_text = f"""Hi again,

Quick follow-up on my previous email — I just wrapped up a successful campaign with Syntx that generated great engagement from the Turkish AI community.

I'd love to create something similar for {brand_name}. Would you be open to a quick chat this week?

Best,
Dolunay"""

    body_html = f"""<p>Hi again,</p>

<p>Quick follow-up on my previous email — I just wrapped up a successful campaign with <strong>Syntx</strong> that generated great engagement from the Turkish AI community.</p>

<p>I'd love to create something similar for <strong>{brand_name}</strong>. Would you be open to a quick chat this week?</p>

<p>Best,<br>Dolunay</p>"""

    return {"body_text": body_text, "body_html": body_html}


def research_brand_for_followup(brand_info, apify_token=None):
    """
    Follow-up kişiselleştirmesi için markanın son aktivitelerini araştırır.
    (Seçenek A — Web + Instagram analizi)
    
    Args:
        brand_info: dict with instagram_handle, website
        apify_token: Apify API token
    
    Returns:
        dict: {recent_posts, website_summary}
    """
    handle = brand_info.get("instagram_handle", "")
    website = brand_info.get("website", "")
    context = {"recent_posts": [], "website_summary": ""}

    if not apify_token:
        apify_token = os.environ.get("APIFY_TOKEN")

    # 1. Son Instagram paylaşımlarını çek
    if handle and apify_token:
        try:
            print(f"  📱 @{handle} son paylaşımları çekiliyor...")
            resp = requests.post(
                "https://api.apify.com/v2/acts/apify~instagram-scraper/runs",
                headers={"Authorization": f"Bearer {apify_token}", "Content-Type": "application/json"},
                json={
                    "directUrls": [f"https://www.instagram.com/{handle}/"],
                    "resultsType": "posts",
                    "resultsLimit": 5,
                },
                timeout=30,
            )
            if resp.status_code == 201:
                import time
                run_id = resp.json()["data"]["id"]
                # Polling (max 2 dakika)
                for _ in range(12):
                    time.sleep(10)
                    status_resp = requests.get(
                        f"https://api.apify.com/v2/actor-runs/{run_id}",
                        headers={"Authorization": f"Bearer {apify_token}"},
                    )
                    status = status_resp.json()["data"]["status"]
                    if status == "SUCCEEDED":
                        dataset_id = status_resp.json()["data"]["defaultDatasetId"]
                        items = requests.get(
                            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                            headers={"Authorization": f"Bearer {apify_token}"},
                        ).json()
                        context["recent_posts"] = [
                            {"caption": (item.get("caption") or "")[:150], "likes": item.get("likesCount", 0)}
                            for item in items[:5]
                        ]
                        print(f"  ✅ {len(context['recent_posts'])} paylaşım bulundu.")
                        break
                    elif status in ("FAILED", "ABORTED"):
                        break
        except Exception as e:
            print(f"  ⚠️ Instagram araştırma hatası: {e}")

    # 2. Web sitesinden kısa özet çıkar (OpenAI ile)
    if website:
        summary_prompt = f"Visit {website} mentally and describe in 1 sentence what this company does. Be specific about their product."
        summary = _call_openai(summary_prompt)
        if summary:
            context["website_summary"] = summary

    return context


if __name__ == "__main__":
    # Test outreach
    test_brand = {
        "marka_adi": "Test AI",
        "instagram_handle": "test_ai",
        "website": "https://test.ai",
        "sirket_aciklamasi": "AI testing tool",
    }
    result = generate_outreach_email(test_brand)
    print(json.dumps(result, indent=2, ensure_ascii=False))

import json

from src import personalizer


def test_safe_parse_json_direct():
    raw = '{"subject": "X", "body_text": "Y", "body_html": "<p>Y</p>"}'
    parsed = personalizer._safe_parse_json(raw)
    assert parsed["subject"] == "X"


def test_safe_parse_json_codeblock():
    raw = "```json\n{\"a\": 1}\n```"
    parsed = personalizer._safe_parse_json(raw)
    assert parsed == {"a": 1}


def test_safe_parse_json_garbage_returns_none():
    assert personalizer._safe_parse_json("not json at all") is None


def test_append_signature_appends():
    out = personalizer._append_signature({"body_text": "hi", "body_html": "<p>hi</p>"})
    assert "Dolunay" in out["body_text"]
    assert "Dolunay" in out["body_html"]


def test_fallback_outreach_contains_brand():
    out = personalizer._fallback_outreach("FooBrand", "foobrand")
    assert "FooBrand" in out["subject"]
    assert "FooBrand" in out["body_text"]
    assert "<p>" in out["body_html"]


def test_dolunay_profile_loaded():
    assert personalizer.DOLUNAY_PROFILE.get("name")
    assert personalizer.DOLUNAY_PROFILE.get("top_results")


def test_generate_outreach_uses_fallback_when_no_api(monkeypatch):
    """API key yokken fallback template döner — gerçek çağrı yapılmaz."""
    monkeypatch.setattr(personalizer, "_get_openai_key", lambda: None)
    out = personalizer.generate_outreach_email({
        "marka_adi": "TestCo",
        "instagram_handle": "testco",
        "website": "https://testco.ai",
        "sirket_aciklamasi": "AI tool",
    })
    assert "TestCo" in out["subject"]
    assert "subject" in out and "body_text" in out and "body_html" in out

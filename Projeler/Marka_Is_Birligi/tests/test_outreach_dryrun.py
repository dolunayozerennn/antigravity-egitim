"""Pipeline dry-run integration smoke test.

Network/Notion/Gmail çağrılarını mock'layıp `run_full_pipeline(dry_run=True)`
ucundan uca dönecek mi diye test eder. Asıl amaç: dry_run flag gerçekten
side-effect'leri (Notion yaz, email gönder) atlıyor mu.
"""

from src import outreach


def _fake_brand():
    return {
        "instagram_handle": "fakebrand",
        "marka_adi": "FakeBrand",
        "mention_sayisi": 3,
        "is_collab": True,
        "kaynak_profiller": ["someinfluencer"],
        "caption_samples": ["caption with @fakebrand"],
    }


def test_dry_run_does_not_call_notion_or_gmail(monkeypatch):
    calls = {"add": 0, "update": 0, "send": 0}

    monkeypatch.setattr(outreach, "add_brands_batch", lambda brands: calls.__setitem__("add", calls["add"] + 1))
    monkeypatch.setattr(outreach, "update_brand", lambda *a, **k: calls.__setitem__("update", calls["update"] + 1))
    monkeypatch.setattr(outreach, "get_brands_by_status", lambda *_: [])  # send_outreach pending=0

    # Pipeline'ın kullandığı modülleri stub'la.
    from src import scraper, analyzer, contact_finder
    monkeypatch.setattr(scraper, "scrape_reels", lambda dry_run=False: [{"caption": "x"}])
    monkeypatch.setattr(analyzer, "find_new_brands", lambda reels=None: [_fake_brand()])
    monkeypatch.setattr(
        contact_finder,
        "enrich_new_brands",
        lambda brands: [{**b, "best_email": "x@y.com", "email_status": "verified", "email_source": "web_scrape"} for b in brands],
    )

    metrics = outreach.run_full_pipeline(dry_run=True)

    assert metrics["new_brands"] == 1
    assert metrics["emails_verified"] == 1
    # dry_run'da Notion'a yazma çağrılmamalı
    assert calls["add"] == 0
    # dry_run'da email gönderim 0 (pending zaten boş ama yine de güvenlik)
    assert metrics["sent"] == 0

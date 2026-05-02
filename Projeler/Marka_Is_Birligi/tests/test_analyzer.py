from src import analyzer


def test_extract_mentions_from_caption():
    cap = "Harika içerik @brand_ai @another.tool ve @brand_ai tekrar"
    out = analyzer.extract_mentions_from_caption(cap)
    assert "brand_ai" in out
    assert "another.tool" in out


def test_has_collab_marker_tr():
    assert analyzer.has_collab_marker("Bu paylaşım işbirliği içerir")
    assert analyzer.has_collab_marker("#sponsored content")
    assert not analyzer.has_collab_marker("normal post")


def test_is_likely_ai_brand_known():
    assert analyzer.is_likely_ai_brand("pixelcut", sources=[])


def test_is_likely_ai_brand_handle_heuristic():
    assert analyzer.is_likely_ai_brand("foobar_ai", sources=[])
    assert analyzer.is_likely_ai_brand("agent.ai", sources=[])


def test_is_likely_ai_brand_negative():
    assert not analyzer.is_likely_ai_brand("randomperson", sources=[{"caption_snippet": "lorem ipsum", "is_collab": False}])


def test_brand_filters_loaded():
    # config/brand_filters.json yüklendi, listeler boş değil.
    assert len(analyzer.KNOWN_AI_BRANDS) > 50
    assert "pixelcut" in analyzer.KNOWN_AI_BRANDS
    assert len(analyzer.FALSE_POSITIVES) > 0
    assert len(analyzer.SKIP_BIG_COMPANIES) > 0

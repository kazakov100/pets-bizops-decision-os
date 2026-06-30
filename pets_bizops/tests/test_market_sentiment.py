from pets_bizops.data import market_sentiment as sentiment


def test_trustpilot_snapshot_has_expected_keys():
    assert 0 < sentiment.TRUSTPILOT_SNAPSHOT["rating"] <= sentiment.TRUSTPILOT_SNAPSHOT["scale"]
    assert sentiment.TRUSTPILOT_SNAPSHOT["review_count"] > 0


def test_naic_complaint_index_has_expected_keys():
    assert sentiment.NAIC_COMPLAINT_INDEX["value"] > sentiment.NAIC_COMPLAINT_INDEX["industry_baseline"]


def test_naic_complaint_index_has_prior_year_for_trend():
    naic = sentiment.NAIC_COMPLAINT_INDEX
    assert naic["prior_year"] < naic["year"]
    assert naic["prior_year_value"] > 0
    assert naic["prior_year_caveat"]


def test_complaint_themes_have_both_sentiments():
    sentiments = {t["sentiment"] for t in sentiment.COMPLAINT_THEMES}
    assert "negative" in sentiments
    assert "positive" in sentiments


def test_complaint_themes_have_emoji():
    for theme in sentiment.COMPLAINT_THEMES:
        assert theme.get("emoji")


def test_sources_and_limitation_are_present():
    assert len(sentiment.SOURCES) >= 2
    assert "internal" in sentiment.PUBLIC_SENTIMENT_LIMITATION.lower()

import pytest

from pets_bizops.ai import client, tools


def test_parse_json_response_handles_plain_json():
    out = client.parse_json_response('{"a": 1}')
    assert out == {"a": 1}


def test_parse_json_response_handles_markdown_fence():
    out = client.parse_json_response('```json\n{"a": 1}\n```')
    assert out == {"a": 1}


def test_parse_json_response_handles_prose_before_fenced_json():
    text = 'Here is the diagnosis:\n\n```json\n{"a": 1, "b": [1, 2]}\n```'
    out = client.parse_json_response(text)
    assert out == {"a": 1, "b": [1, 2]}


def test_parse_json_response_handles_prose_with_unfenced_json():
    text = 'Sure, here you go: {"a": 1} -- let me know if you need more.'
    out = client.parse_json_response(text)
    assert out == {"a": 1}


def test_parse_json_response_raises_on_garbage():
    with pytest.raises(ValueError):
        client.parse_json_response("not json at all")


def test_rank_hypotheses_orders_by_composite_score_not_input_order():
    hypotheses = [
        {"statement": "weak", "evidence_strength": "low", "impact_estimate": "low", "confidence": "low"},
        {"statement": "strong", "evidence_strength": "high", "impact_estimate": "high", "confidence": "high"},
    ]
    ranked = client.rank_hypotheses(hypotheses)
    assert ranked[0]["statement"] == "strong"
    assert ranked[0]["composite_score"] > ranked[1]["composite_score"]


def test_rank_hypotheses_breaks_ties_deterministically():
    hypotheses = [
        {"statement": "b", "evidence_strength": "medium", "impact_estimate": "medium", "confidence": "medium"},
        {"statement": "a", "evidence_strength": "medium", "impact_estimate": "medium", "confidence": "medium"},
    ]
    ranked = client.rank_hypotheses(hypotheses)
    assert [h["statement"] for h in ranked] == ["a", "b"]


def test_build_tool_executor_has_all_schema_names():
    executor = tools.build_tool_executor()
    schema_names = {s["name"] for s in tools.TOOL_SCHEMAS}
    assert set(executor.keys()) == schema_names


def test_get_company_kpis_tool():
    executor = tools.build_tool_executor()
    result = executor["get_company_kpis"]({})
    assert "in_force_premium_m" in result


def test_get_pet_segment_kpis_tool():
    executor = tools.build_tool_executor()
    result = executor["get_pet_segment_kpis"]({})
    assert result["quarter"] == "Q1'26"
    assert result["yoy_ifp_growth_pct"] > 0


def test_get_pet_loss_ratio_trend_tool():
    executor = tools.build_tool_executor()
    result = executor["get_pet_loss_ratio_trend"]({})
    assert len(result["quarters"]) == 9


def test_get_segment_breakdown_tool_defaults_to_latest():
    executor = tools.build_tool_executor()
    result = executor["get_segment_breakdown"]({})
    assert result["quarter"] == "Q1'26"
    assert "breakdown" in result


def test_get_segment_breakdown_tool_accepts_explicit_quarter():
    executor = tools.build_tool_executor()
    result = executor["get_segment_breakdown"]({"quarter": "Q4'25"})
    assert result["quarter"] == "Q4'25"


def test_get_all_segments_trend_tool():
    executor = tools.build_tool_executor()
    result = executor["get_all_segments_trend"]({})
    assert len(result["rows"]) == 45


def test_get_growth_trend_tool():
    executor = tools.build_tool_executor()
    result = executor["get_growth_trend"]({})
    assert len(result["quarters"]) == 9


def test_retrieve_knowledge_tool_returns_cited_results():
    executor = tools.build_tool_executor()
    result = executor["retrieve_knowledge"]({"query": "growth and margin tradeoffs", "corpus": "consulting_best_practices", "k": 2})
    assert len(result["results"]) == 2
    for r in result["results"]:
        assert r["source"]
        assert r["corpus"] == "consulting_best_practices"


def test_retrieve_knowledge_tool_rejects_unknown_corpus():
    executor = tools.build_tool_executor()
    result = executor["retrieve_knowledge"]({"query": "x", "corpus": "not_a_real_corpus"})
    assert "error" in result


def test_get_golden_metric_history_tool():
    executor = tools.build_tool_executor()
    result = executor["get_golden_metric_history"]({"metric_id": "pet_gross_loss_ratio"})
    assert "quarters" in result
    assert len(result["quarters"]) >= 5


def test_get_golden_metric_history_tool_unknown_metric():
    executor = tools.build_tool_executor()
    result = executor["get_golden_metric_history"]({"metric_id": "not_a_metric"})
    assert "error" in result


def test_get_market_sentiment_tool():
    executor = tools.build_tool_executor()
    result = executor["get_market_sentiment"]({})
    assert "trustpilot" in result
    assert "naic_complaint_index" in result
    assert "complaint_themes" in result


def test_estimate_dollar_value_tool():
    executor = tools.build_tool_executor()
    result = executor["estimate_dollar_value"]({"base_metric": "pet_ifp_m", "low_points": 1, "base_points": 2, "high_points": 4})
    assert result["low_usd_m"] < result["high_usd_m"]
    assert "formula" in result


def test_estimate_dollar_value_tool_unknown_metric():
    executor = tools.build_tool_executor()
    result = executor["estimate_dollar_value"]({"base_metric": "nope", "low_points": 1, "base_points": 2, "high_points": 4})
    assert "error" in result


def test_get_mission_and_strategy_context_tool():
    executor = tools.build_tool_executor()
    result = executor["get_mission_and_strategy_context"]({})
    assert "Giveback" in result["context"]

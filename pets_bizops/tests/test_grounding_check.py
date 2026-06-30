from pets_bizops.ai import grounding_check


def _transcript():
    return [
        {"tool": "get_market_sentiment", "input": {}, "result": {"trustpilot": {"rating": 4.1}, "complaint_themes": [{"theme": "Premium increases after the first 12 months"}]}},
        {"tool": "retrieve_knowledge", "input": {"corpus": "consulting_best_practices"}, "result": {"results": [{"source": "McKinsey & Company, Grow fast or die slow", "text": "...", "score": 0.5}]}},
    ]


def test_tool_name_citation_verified():
    out = {"risks": [{"risk": "x", "evidence_source": "get_market_sentiment"}]}
    report = grounding_check.check_grounding(out, _transcript())
    assert report.all_grounded
    assert report.verdicts[0].verdict == "verified_tool"


def test_rag_source_citation_verified():
    out = {"framework_choice": {"rag_source": "McKinsey & Company, Grow fast or die slow"}}
    report = grounding_check.check_grounding(out, _transcript())
    assert report.verdicts[0].verdict == "verified_rag"


def test_value_inside_tool_result_verified():
    # A complaint theme cited verbatim is traceable to the real tool result.
    out = {"pain_points": [{"pain_point": "p", "evidence_source": "Premium increases after the first 12 months"}]}
    report = grounding_check.check_grounding(out, _transcript())
    assert report.verdicts[0].verdict == "verified_tool"


def test_fabricated_citation_flagged_unverified():
    out = {"risks": [{"risk": "x", "evidence_source": "internal NPS survey 2025"}]}
    report = grounding_check.check_grounding(out, _transcript())
    assert not report.all_grounded
    assert report.unverified[0].value == "internal NPS survey 2025"


def test_generic_allow_listed_not_flagged():
    out = {"risks": [{"risk": "x", "evidence_source": "market context"}]}
    report = grounding_check.check_grounding(out, _transcript())
    assert report.verdicts[0].verdict == "allowed_generic"
    assert report.all_grounded


def test_nested_citations_collected():
    out = {
        "framework_choice": {"rag_source": "McKinsey & Company, Grow fast or die slow"},
        "key_implications": [
            {"implication": "a", "type": "risk", "evidence_source": "get_market_sentiment"},
            {"implication": "b", "type": "opportunity", "evidence_source": "fabricated thing"},
        ],
    }
    report = grounding_check.check_grounding(out, _transcript())
    assert report.total == 3
    assert len(report.unverified) == 1

"""Tool-calling functions exposed to Claude via the Claude API's native
tool-use mechanism, over real publicly disclosed Lemonade data plus the
retrieval layer in pets_bizops/rag/.

This is tool calling, not a standalone MCP server. Every function returns
JSON-serializable evidence built only from analysis/evidence.py,
analysis/kpis.py, and the rag/ retrieval index -- the LLM never receives
raw source text it didn't explicitly retrieve, and never invents its own
numbers.
"""

from __future__ import annotations

from typing import Callable

from pets_bizops.analysis import kpis, impact
from pets_bizops.data import real_lemonade_data as data
from pets_bizops.data import market_sentiment
from pets_bizops.rag import load_index
from pets_bizops.rag.corpus_loader import CORPUS_IDS

TOOL_SCHEMAS = [
    {
        "name": "get_company_kpis",
        "description": (
            "Get Lemonade's most recently disclosed company-wide KPIs: in-force premium, "
            "customer count, premium per customer, YoY IFP growth rate, gross/net loss "
            "ratio (most recent full year), and most recent disclosed net loss figure."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_pet_segment_kpis",
        "description": (
            "Get Lemonade Pet segment KPIs as of the latest disclosed quarter: in-force "
            "premium, premium per customer, quarterly gross loss ratio, YoY growth rates "
            "for IFP/PPC/loss-ratio-points, cost per claim, launch date, and the new "
            "cross-sell IFP figure."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_pet_loss_ratio_trend",
        "description": (
            "Get the FULL quarterly gross loss ratio time series for Pet (9 quarters, "
            "Q1'24 through Q1'26) -- use this to assess whether Pet's underwriting is "
            "improving, worsening, or flat over time, not just at one snapshot."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_segment_breakdown",
        "description": (
            "Get the cross-segment in-force premium breakdown (Homeowners, Pet, Car, "
            "Europe, Other) at a given quarter, to see relative segment sizes and Pet's "
            "share of the company. Defaults to the latest quarter if not specified."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "quarter": {"type": "string", "description": "e.g. \"Q4'25\" or \"Q1'26\". Defaults to the latest quarter."}
            },
        },
    },
    {
        "name": "get_all_segments_trend",
        "description": (
            "Get the full quarterly time series (in-force premium, gross loss ratio, "
            "premium per customer) for ALL segments (Homeowners, Pet, Car, Europe, Other) "
            "across all 9 disclosed quarters -- use this to compare Pet's trajectory "
            "against other growth segments like Car or Europe."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_growth_trend",
        "description": (
            "Get the full company-wide quarterly time series (in-force premium, "
            "customers, premium per customer, net loss, YoY growth rate) across all "
            "quarters with public data."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "retrieve_knowledge",
        "description": (
            "Retrieve real, cited reference material from one of three knowledge corpora "
            "to ground your reasoning -- this is NOT Lemonade data, it's external "
            "methodology/strategy knowledge. consulting_best_practices: real excerpts from "
            "McKinsey/BCG growth and underwriting frameworks. sentiment_methodology: real "
            "excerpts on survey/NPS/review-bias/thematic-coding methodology. "
            "lemonade_approach: real excerpts on Lemonade's own stated strategic playbook "
            "(flat fee, Giveback, AI-first claims, cross-sell, reinsurance). ALWAYS cite "
            "the returned 'source' field when you use a retrieved chunk in your reasoning."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What you're trying to ground -- a short natural-language question or topic."},
                "corpus": {
                    "type": "string",
                    "description": f"One of: {', '.join(CORPUS_IDS)}",
                },
                "k": {"type": "integer", "description": "Number of chunks to retrieve. Defaults to 3."},
            },
            "required": ["query", "corpus"],
        },
    },
    {
        "name": "get_company_financials",
        "description": (
            "Get Lemonade's company-wide quarterly FINANCIALS and operating metrics "
            "across all 9 disclosed quarters (Q1'24-Q1'26): revenue, gross earned "
            "premium, gross profit + gross profit margin, Adjusted EBITDA (the path to "
            "the company's guided first EBITDA-positive quarter in Q4'26), Annual Dollar "
            "Retention (ADR -- a churn/retention lever), and the company-wide quarterly "
            "gross and net loss ratios. Use this to analyze profitability, operating "
            "leverage, retention, and margin -- not just underwriting loss ratio."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_golden_metric_history",
        "description": (
            "Get the full real quarterly history for one named golden metric: "
            "pet_ifp_growth, pet_gross_loss_ratio, pet_premium_per_customer, "
            "company_ifp_growth, company_adjusted_ebitda, "
            "company_annual_dollar_retention, or company_gross_profit_margin. Use this "
            "to see the actual trend behind a metric the user is trying to improve."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric_id": {
                    "type": "string",
                    "description": "One of: pet_ifp_growth, pet_gross_loss_ratio, pet_premium_per_customer, company_ifp_growth, company_adjusted_ebitda, company_annual_dollar_retention, company_gross_profit_margin",
                }
            },
            "required": ["metric_id"],
        },
    },
    {
        "name": "get_market_sentiment",
        "description": (
            "Get real, publicly available customer-sentiment signal for Lemonade: "
            "Trustpilot rating/review count, the NAIC consumer complaint index "
            "(vs. industry baseline), and recurring complaint/praise themes from "
            "review aggregation. This is NOT Lemonade's internal NPS/CSAT data -- "
            "it's the closest public proxy available, clearly labeled as such."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "estimate_dollar_value",
        "description": (
            "Get a deterministically computed $ value range (low/base/high, in $M "
            "annual) for a risk/opportunity. You supply ONLY: (1) base_metric -- "
            "which real current figure to apply the assumption to (pet_ifp_m or "
            "company_ifp_m), and (2) an assumed percentage-point range "
            "(low/base/high) you believe is achievable, which you MUST ground in "
            "retrieved RAG evidence (e.g. a McKinsey doc on realistic loss-ratio "
            "improvement). Code resolves base_metric to its real value and does the "
            "multiplication -- NEVER state a dollar figure yourself, only these "
            "inputs. The returned number is value = base_metric * (points / 100)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "base_metric": {"type": "string", "description": "One of: pet_ifp_m, company_ifp_m"},
                "low_points": {"type": "number", "description": "Conservative assumed percentage-point improvement."},
                "base_points": {"type": "number", "description": "Base-case assumed percentage-point improvement."},
                "high_points": {"type": "number", "description": "Optimistic assumed percentage-point improvement."},
            },
            "required": ["base_metric", "low_points", "base_points", "high_points"],
        },
    },
    {
        "name": "get_mission_and_strategy_context",
        "description": (
            "Get Lemonade's publicly stated business model, mission, and growth strategy "
            "(flat-fee model, Giveback program, AI-first claims/onboarding, cross-sell "
            "strategy) for grounding recommendations in how the company actually frames "
            "its own goals."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]


def build_tool_executor() -> dict[str, Callable[[dict], dict]]:
    def get_company_kpis(_args: dict) -> dict:
        return kpis.company_latest_snapshot()

    def get_pet_segment_kpis(_args: dict) -> dict:
        return kpis.pet_latest_snapshot()

    def get_pet_loss_ratio_trend(_args: dict) -> dict:
        return {"quarters": kpis.pet_loss_ratio_series().to_dict(orient="records")}

    def get_segment_breakdown(args: dict) -> dict:
        quarter = args.get("quarter") or "Q1'26"
        return kpis.segment_breakdown(quarter)

    def get_all_segments_trend(_args: dict) -> dict:
        return {"rows": kpis.all_segments_quarterly_series().to_dict(orient="records")}

    def get_growth_trend(_args: dict) -> dict:
        return {"quarters": kpis.company_quarterly_series().to_dict(orient="records")}

    def get_company_financials(_args: dict) -> dict:
        return {
            "latest": kpis.company_financials_latest(),
            "quarters": kpis.company_financials_series().to_dict(orient="records"),
        }

    def retrieve_knowledge(args: dict) -> dict:
        query = args.get("query", "")
        corpus = args.get("corpus")
        k = int(args.get("k", 3))
        if corpus not in CORPUS_IDS:
            return {"error": f"Unknown corpus: {corpus!r}. Known: {CORPUS_IDS}"}
        retriever = load_index.get_retriever()
        return {"results": retriever.retrieve(query, corpus=corpus, k=k)}

    def get_golden_metric_history(args: dict) -> dict:
        metric_id = args.get("metric_id", "")
        try:
            series = kpis.golden_metric_series(metric_id)
        except ValueError as e:
            return {"error": str(e)}
        return {"metric_id": metric_id, "quarters": series.to_dict(orient="records")}

    def get_market_sentiment(_args: dict) -> dict:
        return {
            "trustpilot": market_sentiment.TRUSTPILOT_SNAPSHOT,
            "naic_complaint_index": market_sentiment.NAIC_COMPLAINT_INDEX,
            "complaint_themes": market_sentiment.COMPLAINT_THEMES,
            "limitation": market_sentiment.PUBLIC_SENTIMENT_LIMITATION,
        }

    def estimate_dollar_value(args: dict) -> dict:
        try:
            return impact.estimate_dollar_value(
                base_metric=args.get("base_metric", ""),
                low_points=args.get("low_points", 0),
                base_points=args.get("base_points", 0),
                high_points=args.get("high_points", 0),
            ).as_dict()
        except (ValueError, TypeError) as e:
            return {"error": str(e)}

    def get_mission_and_strategy_context(_args: dict) -> dict:
        return {"context": data.MISSION_AND_STRATEGY}

    return {
        "get_company_kpis": get_company_kpis,
        "get_pet_segment_kpis": get_pet_segment_kpis,
        "get_pet_loss_ratio_trend": get_pet_loss_ratio_trend,
        "get_segment_breakdown": get_segment_breakdown,
        "get_all_segments_trend": get_all_segments_trend,
        "get_growth_trend": get_growth_trend,
        "get_company_financials": get_company_financials,
        "retrieve_knowledge": retrieve_knowledge,
        "get_golden_metric_history": get_golden_metric_history,
        "get_market_sentiment": get_market_sentiment,
        "estimate_dollar_value": estimate_dollar_value,
        "get_mission_and_strategy_context": get_mission_and_strategy_context,
    }

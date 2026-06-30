"""Tier-1 deterministic grounding check.

After an AI page returns its parsed JSON, this walks every citation-bearing
field (`evidence_source`, `rag_source`, `document_used`) and verifies each
claimed citation against the REAL tool-call transcript the model actually
had access to:

- a claimed tool name must match a tool actually called, OR the cited value
  must appear verbatim inside a real tool result (i.e. it's traceable to
  real evidence the model saw);
- a claimed RAG source must match a `source` actually returned by a real
  `retrieve_knowledge` result;
- a small allow-list covers the generic, non-citation fallback values the
  prompts explicitly permit (e.g. "market context").

Anything else is flagged `unverified` -- a real, code-checked signal that
the model cited something that isn't in its evidence. This is not theater:
it runs on the actual transcript every time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

CITATION_KEYS = {"evidence_source", "rag_source", "document_used"}

# Generic, non-citation fallback values the prompts explicitly allow.
GENERIC_ALLOW = {
    "market context",
    "market_context",
    "general market context",
    "strategic pillar",
    "n/a",
    "",
}


@dataclass
class ClaimVerdict:
    field: str
    value: str
    verdict: str  # verified_tool | verified_rag | allowed_generic | unverified


@dataclass
class GroundingReport:
    verdicts: list[ClaimVerdict] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.verdicts)

    @property
    def unverified(self) -> list[ClaimVerdict]:
        return [v for v in self.verdicts if v.verdict == "unverified"]

    @property
    def verified_count(self) -> int:
        return sum(1 for v in self.verdicts if v.verdict != "unverified")

    @property
    def all_grounded(self) -> bool:
        return len(self.unverified) == 0


def _collect_citations(obj, out: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in CITATION_KEYS and isinstance(v, str):
                out.append((k, v))
            else:
                _collect_citations(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_citations(item, out)
    return out


def _classify(value: str, tool_names: set[str], rag_sources: set[str], serialized_results: list[str]) -> str:
    low = value.strip().lower()
    if low in GENERIC_ALLOW:
        return "allowed_generic"

    for src in rag_sources:
        s = src.lower()
        if low and (low in s or s in low):
            return "verified_rag"

    for t in tool_names:
        tl = t.lower()
        if tl and (tl in low or low in tl):
            return "verified_tool"

    # Cited value appears verbatim inside a real tool result -> traceable to
    # evidence the model actually saw (e.g. a complaint theme, a segment name).
    if low and any(low in s for s in serialized_results):
        return "verified_tool"

    return "unverified"


def check_grounding(ai_output: dict, transcript: list[dict]) -> GroundingReport:
    tool_names = {e.get("tool", "") for e in transcript}
    rag_sources: set[str] = set()
    serialized_results: list[str] = []
    for e in transcript:
        result = e.get("result", {})
        serialized_results.append(json.dumps(result, default=str).lower())
        if e.get("tool") == "retrieve_knowledge":
            for chunk in (result or {}).get("results", []):
                if chunk.get("source"):
                    rag_sources.add(chunk["source"])

    report = GroundingReport()
    for fld, value in _collect_citations(ai_output):
        report.verdicts.append(ClaimVerdict(fld, value, _classify(value, tool_names, rag_sources, serialized_results)))
    return report

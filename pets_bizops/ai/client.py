"""Claude API tool-calling client.

This wraps Anthropic's native tool-use mechanism in a small loop: send a
message, execute any requested tool calls against the bound dataset, feed
results back, repeat until Claude returns a final text response. The caller
is expected to ask for a JSON-only final response (enforced via the system
prompts in ai/prompts.py) and parse it.
"""

from __future__ import annotations

import json
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
# A faster, cheaper model for lightweight "helper" calls (framework advisor,
# problem framing) where speed matters more than analytical depth. Core
# analytical calls stay on MODEL.
FAST_MODEL = "claude-haiku-4-5-20251001"
MAX_TOOL_TURNS = 6

# Surfaced in the UI so the model choice (and its tradeoff) is visible per step.
MODEL_INFO = {
    MODEL: {
        "label": "Claude Sonnet 4.6",
        "role": "deeper reasoning — for the core analysis where depth matters.",
    },
    FAST_MODEL: {
        "label": "Claude Haiku 4.5",
        "role": "fast & low-cost — for structured helper steps.",
    },
}


class MissingApiKeyError(RuntimeError):
    pass


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise MissingApiKeyError(
            "ANTHROPIC_API_KEY is not set. Create a .env file with "
            "ANTHROPIC_API_KEY=sk-ant-... in the project root."
        )
    return anthropic.Anthropic(api_key=api_key)


def run_tool_loop(
    system_prompt: str,
    user_message: str,
    tool_schemas: list[dict],
    tool_executor: dict,
    max_turns: int = MAX_TOOL_TURNS,
    model: str | None = None,
) -> tuple[str, list[dict]]:
    """Run the tool-calling loop until Claude returns a final text-only turn.

    Returns (final_text, transcript) where transcript is a list of
    {"tool": name, "input": ..., "result": ...} entries, useful for showing
    "what evidence did the AI actually look at" in the UI.
    """
    client = _get_client()
    messages = [{"role": "user", "content": user_message}]
    transcript: list[dict] = []

    for _ in range(max_turns):
        create_kwargs = dict(model=model or MODEL, max_tokens=4096, system=system_prompt, messages=messages)
        if tool_schemas:
            create_kwargs["tools"] = tool_schemas
        response = client.messages.create(**create_kwargs)

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if not tool_use_blocks:
            final_text = "".join(b.text for b in text_blocks)
            return final_text, transcript

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            fn = tool_executor.get(block.name)
            if fn is None:
                result = {"error": f"Unknown tool: {block.name}"}
            else:
                result = fn(block.input)
            transcript.append({"tool": block.name, "input": block.input, "result": result})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Exceeded {max_turns} tool-call turns without a final response.")


def parse_json_response(text: str) -> dict:
    """Parse a JSON object from the model's final text.

    The system prompts ask for JSON-only with no surrounding prose, but
    models don't always comply (e.g. "Here is the diagnosis:\n```json\n{...}\n```").
    Tries, in order: the whole text as-is, a fenced ```json block found
    anywhere in the text, then the substring between the first '{' and the
    matching last '}'.
    """
    cleaned = text.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(cleaned[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from model response: {text[:500]}")


_RUBRIC_SCORE = {"low": 1, "medium": 2, "high": 3}
_RUBRIC_WEIGHTS = {"evidence_strength": 0.4, "impact_estimate": 0.4, "confidence": 0.2}


def rank_hypotheses(hypotheses: list[dict]) -> list[dict]:
    """Compute a composite rank from the model's own per-hypothesis rubric
    scores -- the model proposes evidence_strength/impact_estimate/confidence,
    but the ranking itself is computed here, not asserted by the model.
    """

    def composite_score(h: dict) -> float:
        return sum(
            _RUBRIC_SCORE.get(h.get(field, "low"), 1) * weight
            for field, weight in _RUBRIC_WEIGHTS.items()
        )

    scored = [dict(h, composite_score=round(composite_score(h), 2)) for h in hypotheses]
    return sorted(scored, key=lambda h: (-h["composite_score"], h["statement"]))

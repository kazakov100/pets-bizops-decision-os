"""Shared UI for the two-tier validation agent, reused by all 3 AI pages.

Tier 1: deterministic grounding check (always runs, no API call) -- verifies
every citation in the AI output against the real transcript.
Tier 2: optional deep AI audit (one extra Claude call) -- claim-by-claim
hallucination review of the output against the transcript.
"""

from __future__ import annotations

import time

import anthropic
import streamlit as st

from pets_bizops.ai import client, prompts, grounding_check
from pets_bizops.ui import style


def render_validation(ai_output: dict, transcript: list[dict], state_key: str) -> None:
    # Tier 1 -- deterministic, real, always runs. The brief spinner pause makes
    # the check visible to a human; the check itself completes in milliseconds.
    with st.spinner("🔍 Validating claims against retrieved evidence..."):
        report = grounding_check.check_grounding(ai_output, transcript)
        time.sleep(0.6)
    style.grounding_badge(report, label="code-verified")

    # Tier 2 -- optional deeper AI audit (runs on the fast model so it doesn't hang).
    st.caption("Optional second pass: a separate model re-checks every claim against the transcript.")
    if st.button("🔬 Run Deep Hallucination Audit (AI-reviewed)", key=f"audit_btn_{state_key}"):
        try:
            user_message = (
                "AI OUTPUT (the JSON to audit):\n"
                + str(ai_output)
                + "\n\nFULL TOOL-CALL TRANSCRIPT it had access to:\n"
                + str(transcript)
                + "\n\nAudit it claim by claim as instructed."
            )
            with st.spinner("Asking a second model to audit every claim against the transcript..."):
                text, _ = client.run_tool_loop(
                    system_prompt=prompts.HALLUCINATION_AUDIT_SYSTEM_PROMPT,
                    user_message=user_message,
                    tool_schemas=[],
                    tool_executor={},
                    model=client.FAST_MODEL,
                )
            try:
                st.session_state[f"audit_{state_key}"] = client.parse_json_response(text)
            except ValueError:
                # Never silently drop the result -- show the raw audit text instead.
                st.session_state[f"audit_{state_key}"] = {"overall": text.strip(), "verdicts": []}
        except client.MissingApiKeyError as e:
            st.error(str(e))
        except anthropic.APIError as e:
            st.error(f"Claude API error: {e}")

    audit = st.session_state.get(f"audit_{state_key}")
    if audit:
        st.markdown(f"🔬 **AI-reviewed:** {style.escape_dollar(audit.get('overall', ''))}")
        if audit.get("verdicts"):
            with st.expander("Deep audit detail (AI-reviewed)"):
                for v in audit.get("verdicts", []):
                    icon = {"grounded": "✅", "hallucinated": "⚠", "unverifiable": "❓"}.get(v.get("verdict"), "•")
                    st.markdown(f"{icon} **{v.get('verdict', '')}** — {style.escape_dollar(v.get('claim', ''))}")
                    if v.get("matched_evidence"):
                        st.caption(style.escape_dollar(v["matched_evidence"]))

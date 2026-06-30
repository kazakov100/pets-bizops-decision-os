"""Generate REAL default analysis runs and save them as fixtures so the app
can show a precomputed analysis by default (a reviewer doesn't have to run it,
but can re-run live). Re-run this script to refresh the defaults:

    python -m scripts.build_default_runs

Every output here is a genuine pipeline run (real tool calls + transcript),
not hand-written -- so the defaults carry the same grounding as a live run.
"""

from __future__ import annotations

import json
import os

from pets_bizops.ai import full_chain

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "pets_bizops", "data", "default_runs")


def main() -> None:
    chain = full_chain.run_full_chain(full_chain.DEFAULT_FRAMEWORK)
    for name, payload in chain.items():
        path = os.path.join(OUT_DIR, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"saved {name} -> {path}")


if __name__ == "__main__":
    main()

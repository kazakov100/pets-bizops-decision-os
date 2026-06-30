"""Loader for named, reviewable AI "skills" -- markdown instruction modules
with a frontmatter name/description, injected into a system prompt for one
specific analysis stage.

This app calls the Claude API directly (no Claude Code/Agent SDK skill
loading available), so a "skill" here is just a transparent, named text
asset: a deliberate choice to make the AI's grounding instructions visible
and labeled in the UI ("Skill used: ...") rather than buried in one
monolithic prompt file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")


@dataclass
class Skill:
    name: str
    description: str
    body: str


def load_skill(skill_id: str) -> Skill:
    path = os.path.join(_SKILLS_DIR, f"{skill_id}.md")
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    parts = raw.split("---")
    if len(raw.strip()) == 0 or len(parts) < 3:
        raise ValueError(f"Skill file {path} is missing frontmatter (expected '---' delimited header).")

    frontmatter, body = parts[1], "---".join(parts[2:])
    fields: dict[str, str] = {}
    for line in frontmatter.strip().splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()

    return Skill(name=fields.get("name", skill_id), description=fields.get("description", ""), body=body.strip())

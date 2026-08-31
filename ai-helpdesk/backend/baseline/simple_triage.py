"""
Baseline IT triage — represents a simple pre-agent approach.

Design (intentionally limited):
- Single-pass keyword matching (no dedicated validation agent)
- Always creates a ticket (no spam/self-service suppression)
- No duplicate detection
- Flat P3 severity unless the word "critical" appears in text
- Round-robin assignment (ignores expertise and workload)
"""

from __future__ import annotations

import re
from typing import Any

_ROUND_ROBIN = ["Amit Patel", "Priya Mehta", "Raj Shah"]
_rr_index = 0

KEYWORDS = [
    ("vpn", "Network"),
    ("wifi", "Network"),
    ("laptop", "Hardware"),
    ("screen", "Hardware"),
    ("email", "Email"),
    ("outlook", "Email"),
    ("password", "Password / Account"),
    ("printer", "Printer"),
    ("security", "Security"),
    ("production", "Application"),
    ("software", "Software"),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _detect_category(text: str) -> str:
    for keyword, category in KEYWORDS:
        if keyword in text:
            return category
    return "Other"


def _next_assignee() -> str:
    global _rr_index
    assignee = _ROUND_ROBIN[_rr_index % len(_ROUND_ROBIN)]
    _rr_index += 1
    return assignee


def reset_round_robin() -> None:
    global _rr_index
    _rr_index = 0


def triage(issue: dict, existing_tickets: list | None = None) -> dict[str, Any]:
    """
    Simple baseline triage. Returns a normalized result dict comparable to the agent workflow.
    """
    text = _normalize(f"{issue.get('title', '')} {issue.get('description', '')}")

    category = _detect_category(text)
    severity = "P1" if "critical" in text or "production" in text else "P3"
    assignee = _next_assignee()

    return {
        "create_ticket": True,
        "suppression_outcome": None,
        "duplicate": {"is_duplicate": False},
        "categorization": {"category": category, "subcategory": "General"},
        "severity": {"severity": severity, "priority": "MEDIUM" if severity == "P3" else "CRITICAL"},
        "assignee": assignee,
        "suggestions": ["Please restart your device and try again."],
        "validation": {"is_genuine": True, "requires_it_intervention": True},
        "approach": "baseline_keyword_round_robin",
    }


if __name__ == "__main__":
    sample = {
        "title": "VPN is not connecting",
        "description": "I cannot connect to the company VPN since this morning.",
    }
    import json
    print(json.dumps(triage(sample), indent=2))

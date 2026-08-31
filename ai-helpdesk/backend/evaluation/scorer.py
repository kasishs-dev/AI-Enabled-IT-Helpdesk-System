"""Score triage results against expected outcomes."""

from __future__ import annotations

from typing import Any


def _action_from_result(result: dict) -> str:
    if result.get("suppression_outcome") == "DUPLICATE" or (
        result.get("duplicate", {}).get("is_duplicate") and not result.get("create_ticket")
    ):
        return "DUPLICATE"
    if not result.get("create_ticket"):
        return "SUPPRESS"
    return "CREATE"


def score_case(result: dict, expected: dict) -> dict[str, Any]:
    """Score a single case. Returns per-dimension scores and overall pass."""
    action = _action_from_result(result)
    exp_action = expected["action"]

    action_ok = action == exp_action
    category_ok = True
    severity_ok = True
    assignee_ok = True

    if exp_action == "CREATE":
        cat = (result.get("categorization") or {}).get("category")
        sev = (result.get("severity") or {}).get("severity")
        assignee = result.get("assignee")

        if expected.get("category"):
            category_ok = cat == expected["category"]
        if expected.get("severity"):
            severity_ok = sev == expected["severity"]
        if expected.get("assignee"):
            allowed = expected["assignee"]
            if isinstance(allowed, str):
                allowed = [allowed]
            assignee_ok = assignee in allowed if assignee else False
    elif exp_action in ("SUPPRESS", "DUPLICATE"):
        category_ok = severity_ok = assignee_ok = not result.get("create_ticket")

    dims = {
        "action": action_ok,
        "category": category_ok,
        "severity": severity_ok,
        "assignee": assignee_ok,
    }

    if exp_action in ("SUPPRESS", "DUPLICATE"):
        overall = action_ok
        triage_score = 100.0 if action_ok else 0.0
    else:
        weights = {"action": 0.35, "category": 0.25, "severity": 0.25, "assignee": 0.15}
        triage_score = sum(weights[k] * (100 if dims[k] else 0) for k in weights)
        overall = triage_score >= 75.0

    false_positive = exp_action in ("SUPPRESS", "DUPLICATE") and result.get("create_ticket")
    false_negative = exp_action == "CREATE" and not result.get("create_ticket")

    return {
        "action": action,
        "expected_action": exp_action,
        "action_ok": action_ok,
        "category_ok": category_ok,
        "severity_ok": severity_ok,
        "assignee_ok": assignee_ok,
        "triage_score": round(triage_score, 1),
        "pass": overall,
        "false_positive_ticket": false_positive,
        "false_negative_ticket": false_negative,
    }


def aggregate(results: list[dict]) -> dict[str, Any]:
    n = len(results)
    if n == 0:
        return {}

    return {
        "cases": n,
        "pass_rate": round(sum(1 for r in results if r["pass"]) / n * 100, 1),
        "mean_triage_score": round(sum(r["triage_score"] for r in results) / n, 1),
        "action_accuracy": round(sum(1 for r in results if r["action_ok"]) / n * 100, 1),
        "category_accuracy": round(
            sum(1 for r in results if r["category_ok"] or r["expected_action"] != "CREATE") / n * 100, 1
        ),
        "severity_accuracy": round(
            sum(1 for r in results if r["severity_ok"] or r["expected_action"] != "CREATE") / n * 100, 1
        ),
        "assignee_accuracy": round(
            sum(1 for r in results if r["assignee_ok"] or r["expected_action"] != "CREATE") / n * 100, 1
        ),
        "false_positive_tickets": sum(1 for r in results if r["false_positive_ticket"]),
        "false_negative_tickets": sum(1 for r in results if r["false_negative_ticket"]),
    }

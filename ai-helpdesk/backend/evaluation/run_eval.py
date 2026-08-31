"""
Run baseline vs agentic workflow evaluation on shared test cases.

Usage (from backend/):
    python -m evaluation.run_eval
    python -m evaluation.run_eval --json
    python -m evaluation.run_eval --baseline-only
    python -m evaluation.run_eval --agent-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Ensure backend root is on path when run as script
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from baseline.simple_triage import reset_round_robin, triage as baseline_triage
from app.ai.service import AIHelpdeskService
from evaluation.mock_team import select_assignee
from evaluation.scorer import aggregate, score_case

CASES_PATH = Path(__file__).parent / "test_cases.json"
RESULTS_PATH = Path(__file__).parent / "results.json"


def _normalize_agent_result(raw: dict) -> dict:
    out = {
        "create_ticket": raw.get("create_ticket", False),
        "suppression_outcome": raw.get("suppression_outcome"),
        "duplicate": raw.get("duplicate", {}),
        "categorization": raw.get("categorization"),
        "severity": raw.get("severity"),
        "validation": raw.get("validation", {}),
        "suggestions": raw.get("suggestions", []),
        "approach": "agentic_orchestration",
    }
    if out["create_ticket"] and out.get("categorization") and out.get("severity"):
        cat = out["categorization"]
        sev = out["severity"]
        name, score, reason = select_assignee(
            cat.get("category", ""),
            cat.get("subcategory", ""),
            sev.get("severity", "P3"),
        )
        out["assignee"] = name
        out["assignment_score"] = score
        out["assignment_reason"] = reason
    else:
        out["assignee"] = None
    return out


async def run_agent_case(issue: dict, existing: list, thresholds: dict) -> dict:
    payload = {**issue, "existing_tickets": existing}
    service = AIHelpdeskService()
    raw = await service.process_issue(payload, thresholds)
    return _normalize_agent_result(raw)


def run_baseline_case(issue: dict, existing: list) -> dict:
    reset_round_robin()
    return baseline_triage(issue, existing)


async def evaluate(mode: str = "both") -> dict:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    thresholds = data["thresholds"]
    cases = data["cases"]

    baseline_rows = []
    agent_rows = []

    for case in cases:
        issue = {"title": case["title"], "description": case["description"]}
        existing = case.get("existing_tickets", [])
        expected = case["expected"]

        row = {"id": case["id"], "notes": case.get("notes", "")}

        if mode in ("both", "baseline"):
            t0 = time.perf_counter()
            b_result = run_baseline_case(issue, existing)
            b_ms = round((time.perf_counter() - t0) * 1000, 1)
            b_score = score_case(b_result, expected)
            baseline_rows.append({**row, "result": b_result, "score": b_score, "latency_ms": b_ms})

        if mode in ("both", "agent"):
            t0 = time.perf_counter()
            a_result = await run_agent_case(issue, existing, thresholds)
            a_ms = round((time.perf_counter() - t0) * 1000, 1)
            a_score = score_case(a_result, expected)
            agent_rows.append({**row, "result": a_result, "score": a_score, "latency_ms": a_ms})

    report = {
        "test_cases_file": str(CASES_PATH.name),
        "case_count": len(cases),
        "thresholds": thresholds,
    }

    if baseline_rows:
        report["baseline"] = {
            "approach": "Single-pass keyword triage + always create ticket + round-robin assign",
            "aggregate": aggregate([r["score"] for r in baseline_rows]),
            "cases": [
                {
                    "id": r["id"],
                    "pass": r["score"]["pass"],
                    "triage_score": r["score"]["triage_score"],
                    "action": r["score"]["action"],
                    "expected": r["score"]["expected_action"],
                    "latency_ms": r["latency_ms"],
                    "false_positive": r["score"]["false_positive_ticket"],
                }
                for r in baseline_rows
            ],
        }

    if agent_rows:
        report["agent"] = {
            "approach": "Multi-agent orchestration (analysis, validation, duplicate, classify, severity, assign)",
            "aggregate": aggregate([r["score"] for r in agent_rows]),
            "cases": [
                {
                    "id": r["id"],
                    "pass": r["score"]["pass"],
                    "triage_score": r["score"]["triage_score"],
                    "action": r["score"]["action"],
                    "expected": r["score"]["expected_action"],
                    "latency_ms": r["latency_ms"],
                    "false_positive": r["score"]["false_positive_ticket"],
                }
                for r in agent_rows
            ],
        }

    if baseline_rows and agent_rows:
        b_agg = report["baseline"]["aggregate"]
        a_agg = report["agent"]["aggregate"]
        report["comparison"] = {
            "primary_metric": "mean_triage_score",
            "baseline_score": b_agg["mean_triage_score"],
            "agent_score": a_agg["mean_triage_score"],
            "improvement_points": round(a_agg["mean_triage_score"] - b_agg["mean_triage_score"], 1),
            "pass_rate_baseline": b_agg["pass_rate"],
            "pass_rate_agent": a_agg["pass_rate"],
            "false_positives_baseline": b_agg["false_positive_tickets"],
            "false_positives_agent": a_agg["false_positive_tickets"],
            "false_negatives_baseline": b_agg["false_negative_tickets"],
            "false_negatives_agent": a_agg["false_negative_tickets"],
        }

    return report


def print_report(report: dict) -> None:
    print("=" * 72)
    print("AI HELPDESK — BASELINE vs AGENTIC WORKFLOW EVALUATION")
    print("=" * 72)
    print(f"Cases: {report['case_count']}  |  Thresholds: {report['thresholds']}\n")

    if "baseline" in report:
        b = report["baseline"]["aggregate"]
        print("BASELINE (keyword + round-robin, always creates ticket)")
        print(f"  Mean triage score : {b['mean_triage_score']}%")
        print(f"  Pass rate         : {b['pass_rate']}%")
        print(f"  Action accuracy   : {b['action_accuracy']}%")
        print(f"  False positives   : {b['false_positive_tickets']} unnecessary tickets")
        print(f"  False negatives   : {b['false_negative_tickets']} missed tickets\n")

    if "agent" in report:
        a = report["agent"]["aggregate"]
        print("AGENT SOLUTION (multi-agent orchestration)")
        print(f"  Mean triage score : {a['mean_triage_score']}%")
        print(f"  Pass rate         : {a['pass_rate']}%")
        print(f"  Action accuracy   : {a['action_accuracy']}%")
        print(f"  False positives   : {a['false_positive_tickets']} unnecessary tickets")
        print(f"  False negatives   : {a['false_negative_tickets']} missed tickets\n")

    if "comparison" in report:
        c = report["comparison"]
        print("COMPARISON")
        print(f"  Primary metric improvement : +{c['improvement_points']} points")
        print(f"  Pass rate                  : {c['pass_rate_baseline']}% -> {c['pass_rate_agent']}%")
        print(f"  False positives            : {c['false_positives_baseline']} -> {c['false_positives_agent']}")
        print()

    print("PER-CASE RESULTS")
    print("-" * 72)
    if "baseline" in report and "agent" in report:
        print(f"{'Case ID':<22} {'Baseline':>10} {'Agent':>10} {'Expected':>10}")
        for bc, ac in zip(report["baseline"]["cases"], report["agent"]["cases"]):
            b_mark = "PASS" if bc["pass"] else "FAIL"
            a_mark = "PASS" if ac["pass"] else "FAIL"
            print(f"{bc['id']:<22} {b_mark:>10} {a_mark:>10} {bc['expected']:>10}")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Evaluate baseline vs agent triage")
    parser.add_argument("--json", action="store_true", help="Print/write JSON only")
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--agent-only", action="store_true")
    parser.add_argument("--no-write", action="store_true", help="Do not write results.json")
    args = parser.parse_args()

    mode = "both"
    if args.baseline_only:
        mode = "baseline"
    elif args.agent_only:
        mode = "agent"

    report = asyncio.run(evaluate(mode))

    if not args.no_write:
        RESULTS_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
        if not args.no_write:
            print(f"\nFull results written to: {RESULTS_PATH}")


if __name__ == "__main__":
    main()

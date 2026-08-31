"""Mock IT team for offline assignment evaluation (no database required)."""

from __future__ import annotations

ENGINEERS = [
    {
        "name": "Amit Patel",
        "expertise": ["Network", "VPN", "WiFi", "Connectivity"],
        "max_active_tickets": 10,
        "active_tickets": 5,
        "availability": True,
        "severity_capability": ["P1", "P2", "P3", "P4"],
    },
    {
        "name": "Priya Mehta",
        "expertise": ["Laptop", "Hardware", "Windows", "Software", "Application"],
        "max_active_tickets": 8,
        "active_tickets": 2,
        "availability": True,
        "severity_capability": ["P1", "P2", "P3", "P4"],
    },
    {
        "name": "Raj Shah",
        "expertise": ["Network", "VPN", "Server", "Database"],
        "max_active_tickets": 8,
        "active_tickets": 1,
        "availability": True,
        "severity_capability": ["P1", "P2", "P3", "P4"],
    },
]


def select_assignee(category: str, subcategory: str, severity: str) -> tuple[str, float, str]:
    """Same scoring logic as AssignmentEngine, using in-memory team state."""
    best_name = ""
    best_score = -1.0
    best_reason = ""

    for eng in ENGINEERS:
        score = 0.0
        haystack = f"{category} {subcategory}".lower()
        matches = sum(1 for e in eng["expertise"] if e.lower() in haystack or haystack.find(e.lower()) >= 0)
        if category.lower() in [e.lower() for e in eng["expertise"]]:
            matches += 2
        score += min(40, matches * (40 / 3))

        active = eng["active_tickets"]
        max_t = eng["max_active_tickets"]
        if active < max_t:
            score += max(0, (max_t - active) / max_t) * 30

        if eng["availability"]:
            score += 20
        if severity in eng["severity_capability"]:
            score += 10

        expertise_match = category in eng["expertise"]
        reason = f"Expertise in {category}" if expertise_match else f"Availability/workload (active: {active})"
        if score > best_score:
            best_score = score
            best_name = eng["name"]
            best_reason = reason

    return best_name, best_score, best_reason

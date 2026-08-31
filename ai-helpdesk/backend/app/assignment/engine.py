from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import ITProfile, Ticket, TicketStatus, User, UserRole


ACTIVE_STATUSES = [
    TicketStatus.OPEN,
    TicketStatus.ASSIGNED,
    TicketStatus.IN_PROGRESS,
    TicketStatus.WAITING_FOR_USER,
    TicketStatus.ESCALATED,
    TicketStatus.REOPENED,
]


class AssignmentEngine:
    def __init__(self, expertise_weight: float = 40, workload_weight: float = 30, availability_weight: float = 20, severity_weight: float = 10):
        self.expertise_weight = expertise_weight
        self.workload_weight = workload_weight
        self.availability_weight = availability_weight
        self.severity_weight = severity_weight

    def _workload_score(self, active_count: int, max_tickets: int) -> float:
        if active_count >= max_tickets:
            return 0
        return max(0, (max_tickets - active_count) / max_tickets) * self.workload_weight

    def _expertise_score(self, expertise: list[str], category: str, subcategory: str) -> float:
        if not expertise:
            return 0
        haystack = f"{category} {subcategory}".lower()
        matches = sum(1 for e in expertise if e.lower() in haystack or haystack.find(e.lower()) >= 0)
        if category.lower() in [e.lower() for e in expertise]:
            matches += 2
        return min(self.expertise_weight, matches * (self.expertise_weight / 3))

    def select_assignee(self, db: Session, category: str, subcategory: str, severity: str) -> tuple[User | None, float, str]:
        engineers = (
            db.query(User)
            .join(ITProfile, ITProfile.user_id == User.id)
            .filter(User.role == UserRole.IT_SUPPORT, User.is_active == True, ITProfile.availability == True)
            .all()
        )
        if not engineers:
            return None, 0, "No available IT engineers"

        best_user = None
        best_score = -1
        best_reason = ""

        for engineer in engineers:
            profile = engineer.it_profile
            active_count = (
                db.query(func.count(Ticket.id))
                .filter(Ticket.assigned_to == engineer.id, Ticket.status.in_(ACTIVE_STATUSES))
                .scalar()
            )
            score = 0
            score += self._expertise_score(profile.expertise or [], category or "", subcategory or "")
            score += self._workload_score(active_count or 0, profile.max_active_tickets)
            score += self.availability_weight if profile.availability else 0
            if severity in (profile.severity_capability or []):
                score += self.severity_weight

            expertise_match = category in (profile.expertise or [])
            reason = f"Assigned due to {'expertise in ' + category if expertise_match else 'availability and workload'} (active tickets: {active_count or 0})"
            if score > best_score:
                best_score = score
                best_user = engineer
                best_reason = reason

        return best_user, best_score, best_reason

from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.ai.service import AIHelpdeskService
from app.assignment.engine import AssignmentEngine
from app.audit.service import log_audit
from app.config import get_settings
from app.models import (
    AIAnalysis,
    AnalysisType,
    IssueRequest,
    SuppressionOutcome,
    Ticket,
    TicketAssignment,
    TicketComment,
    TicketStatus,
    User,
    UserRole,
)
from app.notifications.service import create_notification, notify_assignment, notify_managers_escalation
from app.schemas import IssueSubmit

settings = get_settings()
ai_service = AIHelpdeskService()
assignment_engine = AssignmentEngine()


def next_ticket_number(db: Session) -> str:
    last = db.query(Ticket).order_by(Ticket.id.desc()).first()
    num = (last.id + 1) if last else 1
    return f"INC-{num:06d}"


def _store_analysis(db: Session, ticket_id: int | None, analysis_type: AnalysisType, input_data: dict, output_data: dict):
    db.add(
        AIAnalysis(
            ticket_id=ticket_id,
            analysis_type=analysis_type,
            model=settings.ai_model,
            prompt_version="v1",
            input_data=input_data,
            output_data=output_data,
            confidence=output_data.get("confidence"),
        )
    )


async def process_issue_submission(db: Session, user: User, issue: IssueSubmit) -> dict:
    issue_data = issue.model_dump()
    issue_data["requester_email"] = user.email
    issue_data["requester_name"] = user.name

    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_([
            TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS,
            TicketStatus.WAITING_FOR_USER, TicketStatus.ESCALATED, TicketStatus.REOPENED,
        ]))
        .all()
    )
    issue_data["existing_tickets"] = [
        {"ticket_number": t.ticket_number, "title": t.title, "description": t.description}
        for t in open_tickets
    ]

    result = await ai_service.process_issue(
        issue_data,
        {"validation": settings.ai_validation_threshold, "duplicate": settings.ai_duplicate_threshold},
    )

    req = IssueRequest(
        requester_id=user.id,
        title=issue.title,
        description=issue.description,
        device=issue.device,
        operating_system=issue.operating_system,
        location=issue.location,
        application_system=issue.application_system,
        ai_result=result,
        status="COMPLETED" if result.get("create_ticket") or result.get("suppression_outcome") else "FAILED",
    )
    db.add(req)
    db.flush()

    _store_analysis(db, None, AnalysisType.INITIAL_ANALYSIS, issue_data, result.get("analysis", {}))
    _store_analysis(db, None, AnalysisType.VALIDATION, issue_data, result.get("validation", {}))
    _store_analysis(db, None, AnalysisType.SUGGESTION, issue_data, {"suggestions": result.get("suggestions", [])})

    if not result.get("create_ticket"):
        outcome = result.get("suppression_outcome", "SUPPRESSED")
        log_audit(db, actor_id=user.id, action="AI suppressed request", entity_type="issue_request", entity_id=req.id, new_value=outcome, reason=result.get("message"))
        req.status = outcome
        db.commit()
        duplicate_num = None
        if outcome == "DUPLICATE":
            duplicate_num = result.get("duplicate", {}).get("similar_ticket_id")
        return {
            "success": True,
            "ticket_created": False,
            "suppressed": True,
            "outcome": outcome,
            "message": result.get("message"),
            "analysis": {
                "summary": result.get("analysis", {}).get("problem_summary"),
                "category": result.get("analysis", {}).get("possible_category"),
                "confidence": result.get("analysis", {}).get("confidence"),
                "validation": result.get("validation"),
            },
            "suggestions": result.get("suggestions", []),
            "duplicate_ticket_number": duplicate_num,
        }

    cat = result.get("categorization", {})
    sev = result.get("severity", {})
    ticket_number = next_ticket_number(db)
    ticket = Ticket(
        ticket_number=ticket_number,
        title=issue.title,
        description=issue.description,
        requester_id=user.id,
        category=cat.get("category"),
        subcategory=cat.get("subcategory"),
        severity=sev.get("severity"),
        priority=sev.get("priority"),
        status=TicketStatus.OPEN,
        ai_confidence=result.get("analysis", {}).get("confidence"),
        ai_summary=result.get("analysis", {}).get("problem_summary"),
        ai_validation_result="GENUINE" if result.get("ai_available", True) else "AI_UNAVAILABLE",
        ai_reasoning=sev.get("reasoning") or result.get("validation", {}).get("reason"),
        device=issue.device,
        operating_system=issue.operating_system,
        location=issue.location,
        application_system=issue.application_system,
    )
    db.add(ticket)
    db.flush()

    assignee, score, reason = assignment_engine.select_assignee(
        db, ticket.category or "", ticket.subcategory or "", ticket.severity or "P3"
    )
    if assignee:
        ticket.assigned_to = assignee.id
        ticket.status = TicketStatus.ASSIGNED
        db.add(
            TicketAssignment(
                ticket_id=ticket.id,
                assignee_id=assignee.id,
                assignment_score=score,
                reason=reason,
            )
        )
        notify_assignment(
            db,
            assignee,
            ticket.id,
            ticket.ticket_number,
            ticket.title,
            f"{ticket.severity} - {ticket.priority}",
            ticket.category or "General",
            reason,
        )

    if ticket.severity == "P1":
        notify_managers_escalation(db, ticket.ticket_number, ticket.title)
        ticket.status = TicketStatus.ESCALATED

    _store_analysis(db, ticket.id, AnalysisType.CATEGORIZATION, issue_data, cat)
    _store_analysis(db, ticket.id, AnalysisType.SEVERITY, issue_data, sev)
    _store_analysis(db, ticket.id, AnalysisType.DUPLICATE_DETECTION, issue_data, result.get("duplicate", {}))

    log_audit(db, actor_id=user.id, action="Ticket created", entity_type="ticket", entity_id=ticket.id, new_value=ticket.ticket_number)
    if assignee:
        log_audit(db, actor_id=None, action="Ticket assigned", entity_type="ticket", entity_id=ticket.id, new_value=assignee.name, reason=reason)

    req.ticket_id = ticket.id
    db.commit()
    db.refresh(ticket)

    return {
        "success": True,
        "ticket_created": True,
        "suppressed": False,
        "message": "Your IT ticket has been created successfully.",
        "analysis": {
            "summary": ticket.ai_summary,
            "category": ticket.category,
            "severity": ticket.severity,
            "priority": ticket.priority,
            "confidence": ticket.ai_confidence,
            "validation": result.get("validation"),
        },
        "suggestions": result.get("suggestions", []),
        "ticket": ticket,
    }


def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.requester), joinedload(Ticket.assignee), joinedload(Ticket.comments).joinedload(TicketComment.author))
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def user_can_access_ticket(user: User, ticket: Ticket) -> bool:
    if user.role == UserRole.IT_MANAGER:
        return True
    if user.role == UserRole.IT_SUPPORT:
        return ticket.assigned_to == user.id or ticket.status in [TicketStatus.OPEN, TicketStatus.ASSIGNED]
    return ticket.requester_id == user.id


def update_ticket_status(db: Session, ticket: Ticket, new_status: TicketStatus, actor: User, reason: str | None = None, resolution_notes: str | None = None):
    old = ticket.status.value
    ticket.status = new_status
    ticket.updated_at = datetime.utcnow()
    if resolution_notes:
        ticket.resolution_notes = resolution_notes
    if new_status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.utcnow()
        create_notification(
            db,
            user_id=ticket.requester_id,
            title="Ticket Resolved",
            message=f"Your ticket {ticket.ticket_number} has been resolved. Please confirm closure.",
            notification_type=NotificationType.RESOLUTION,
            ticket_id=ticket.id,
        )
    if new_status == TicketStatus.CLOSED:
        ticket.closed_at = datetime.utcnow()
    log_audit(
        db,
        actor_id=actor.id,
        action="Status changed",
        entity_type="ticket",
        entity_id=ticket.id,
        old_value=old,
        new_value=new_status.value,
        reason=reason,
    )

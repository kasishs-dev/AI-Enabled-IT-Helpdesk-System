from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from app.database import get_db
from app.auth.security import authenticate_user, create_access_token, get_current_user, require_roles
from app.models import Notification, Ticket, TicketComment, TicketStatus, User, UserRole, AuditLog, KnowledgeBaseArticle
from app.schemas import (
    AssignmentUpdate,
    CategoryUpdate,
    CommentCreate,
    CommentOut,
    DashboardIT,
    DashboardManager,
    DashboardUser,
    IssueProcessResult,
    IssueSubmit,
    LoginRequest,
    NotificationOut,
    OverrideValidation,
    SeverityUpdate,
    StatusUpdate,
    TicketOut,
    Token,
    UserOut,
    AuditLogOut,
    KnowledgeBaseOut,
    ITProfileOut,
)
from app.tickets.service import get_ticket_or_404, process_issue_submission, update_ticket_status, user_can_access_ticket
from app.audit.service import log_audit
from app.notifications.service import create_notification
from app.models import NotificationType
from app.assignment.engine import AssignmentEngine
from app.models import TicketAssignment, ITProfile

router = APIRouter(prefix="/api")
assignment_engine = AssignmentEngine()


@router.post("/auth/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token)


@router.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/issues/create", response_model=IssueProcessResult)
async def create_issue(issue: IssueSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.USER))):
    result = await process_issue_submission(db, current_user, issue)
    ticket_out = TicketOut.model_validate(result["ticket"]) if result.get("ticket") else None
    return IssueProcessResult(
        success=result["success"],
        ticket_created=result["ticket_created"],
        suppressed=result["suppressed"],
        outcome=result.get("outcome"),
        message=result["message"],
        analysis=result["analysis"],
        suggestions=result["suggestions"],
        ticket=ticket_out,
        duplicate_ticket_number=result.get("duplicate_ticket_number"),
    )


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: Optional[str] = Query(None),
    status: Optional[TicketStatus] = Query(None),
):
    query = db.query(Ticket).options(joinedload(Ticket.requester), joinedload(Ticket.assignee))
    if current_user.role == UserRole.USER:
        query = query.filter(Ticket.requester_id == current_user.id)
    elif current_user.role == UserRole.IT_SUPPORT:
        query = query.filter(or_(Ticket.assigned_to == current_user.id, Ticket.status == TicketStatus.OPEN))
    if status:
        query = query.filter(Ticket.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Ticket.ticket_number.ilike(like),
                Ticket.title.ilike(like),
                Ticket.description.ilike(like),
                Ticket.category.ilike(like),
                Ticket.status.cast(str).ilike(like),
            )
        )
    tickets = query.order_by(Ticket.created_at.desc()).limit(100).all()
    return tickets


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = get_ticket_or_404(db, ticket_id)
    if not user_can_access_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Access denied")
    return ticket


@router.post("/tickets/{ticket_id}/comments", response_model=CommentOut)
def add_comment(ticket_id: int, data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = get_ticket_or_404(db, ticket_id)
    if not user_can_access_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Access denied")
    comment = TicketComment(ticket_id=ticket.id, author_id=current_user.id, content=data.content, is_internal=data.is_internal and current_user.role != UserRole.USER)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
def patch_status(ticket_id: int, data: StatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = get_ticket_or_404(db, ticket_id)
    if current_user.role == UserRole.USER:
        if data.status not in [TicketStatus.CLOSED, TicketStatus.REOPENED]:
            raise HTTPException(status_code=403, detail="Users can only close or reopen tickets")
        if ticket.requester_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if data.status == TicketStatus.CLOSED and ticket.status != TicketStatus.RESOLVED:
            raise HTTPException(status_code=400, detail="Can only close resolved tickets")
    elif current_user.role == UserRole.IT_SUPPORT:
        if ticket.assigned_to != current_user.id and ticket.status != TicketStatus.OPEN:
            raise HTTPException(status_code=403, detail="Not assigned to you")
    update_ticket_status(db, ticket, data.status, current_user, data.reason, data.resolution_notes)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.patch("/tickets/{ticket_id}/severity", response_model=TicketOut)
def patch_severity(ticket_id: int, data: SeverityUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER, UserRole.IT_SUPPORT))):
    ticket = get_ticket_or_404(db, ticket_id)
    old = f"{ticket.severity}/{ticket.priority}"
    ticket.severity = data.severity
    if data.priority:
        ticket.priority = data.priority
    log_audit(db, actor_id=current_user.id, action="Severity changed", entity_type="ticket", entity_id=ticket.id, old_value=old, new_value=f"{ticket.severity}/{ticket.priority}", reason=data.reason)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.patch("/tickets/{ticket_id}/category", response_model=TicketOut)
def patch_category(ticket_id: int, data: CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER, UserRole.IT_SUPPORT))):
    ticket = get_ticket_or_404(db, ticket_id)
    old = f"{ticket.category}/{ticket.subcategory}"
    ticket.category = data.category
    ticket.subcategory = data.subcategory
    log_audit(db, actor_id=current_user.id, action="Category changed", entity_type="ticket", entity_id=ticket.id, old_value=old, new_value=f"{ticket.category}/{ticket.subcategory}", reason=data.reason)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.patch("/tickets/{ticket_id}/assignment", response_model=TicketOut)
def patch_assignment(ticket_id: int, data: AssignmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER, UserRole.IT_SUPPORT))):
    ticket = get_ticket_or_404(db, ticket_id)
    assignee = db.query(User).filter(User.id == data.assignee_id, User.role == UserRole.IT_SUPPORT).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="IT engineer not found")
    old = str(ticket.assigned_to)
    ticket.assigned_to = assignee.id
    ticket.status = TicketStatus.ASSIGNED
    db.add(TicketAssignment(ticket_id=ticket.id, assignee_id=assignee.id, assigned_by=current_user.id, reason=data.reason))
    create_notification(db, user_id=assignee.id, title="Ticket Reassigned", message=f"{ticket.ticket_number} assigned to you.", notification_type=NotificationType.TICKET_ASSIGNMENT, ticket_id=ticket.id)
    log_audit(db, actor_id=current_user.id, action="Ticket reassigned", entity_type="ticket", entity_id=ticket.id, old_value=old, new_value=assignee.name, reason=data.reason)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/tickets/{ticket_id}/override-validation", response_model=TicketOut)
def override_validation(ticket_id: int, data: OverrideValidation, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER))):
    ticket = get_ticket_or_404(db, ticket_id)
    ticket.ai_validation_result = "GENUINE" if data.is_genuine else "OVERRIDDEN_REJECTED"
    if not data.is_genuine:
        ticket.status = TicketStatus.REJECTED
    log_audit(db, actor_id=current_user.id, action="Manager override validation", entity_type="ticket", entity_id=ticket.id, new_value=ticket.ai_validation_result, reason=data.reason)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), unread_only: bool = False):
    q = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.order_by(Notification.created_at.desc()).limit(50).all()


@router.patch("/notifications/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"ok": True}


@router.get("/dashboard/user", response_model=DashboardUser)
def dashboard_user(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.USER))):
    tickets = db.query(Ticket).filter(Ticket.requester_id == current_user.id).all()
    open_s = {TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.REOPENED, TicketStatus.ESCALATED, TicketStatus.WAITING_FOR_USER}
    return DashboardUser(
        welcome_name=current_user.name.split()[0],
        open_tickets=sum(1 for t in tickets if t.status in open_s),
        in_progress=sum(1 for t in tickets if t.status == TicketStatus.IN_PROGRESS),
        waiting_for_user=sum(1 for t in tickets if t.status == TicketStatus.WAITING_FOR_USER),
        resolved=sum(1 for t in tickets if t.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}),
        pending_requests=sum(1 for t in tickets if t.status == TicketStatus.OPEN),
        recent_tickets=sorted(tickets, key=lambda t: t.created_at, reverse=True)[:5],
    )


@router.get("/dashboard/it", response_model=DashboardIT)
def dashboard_it(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_SUPPORT))):
    tickets = db.query(Ticket).options(joinedload(Ticket.requester)).filter(Ticket.assigned_to == current_user.id).all()
    today = datetime.utcnow().date()
    return DashboardIT(
        assigned_to_me=len(tickets),
        high_priority=sum(1 for t in tickets if t.severity in {"P1", "P2"} and t.status not in {TicketStatus.RESOLVED, TicketStatus.CLOSED}),
        in_progress=sum(1 for t in tickets if t.status == TicketStatus.IN_PROGRESS),
        waiting_for_user=sum(1 for t in tickets if t.status == TicketStatus.WAITING_FOR_USER),
        resolved_today=sum(1 for t in tickets if t.resolved_at and t.resolved_at.date() == today),
        tickets=sorted(tickets, key=lambda t: t.created_at, reverse=True),
    )


@router.get("/dashboard/manager", response_model=DashboardManager)
def dashboard_manager(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER))):
    tickets = db.query(Ticket).options(joinedload(Ticket.requester), joinedload(Ticket.assignee)).all()
    severity = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    categories: dict[str, int] = {}
    for t in tickets:
        if t.severity in severity:
            severity[t.severity] += 1
        cat = t.category or "Other"
        categories[cat] = categories.get(cat, 0) + 1

    engineers = db.query(User).join(ITProfile).filter(User.role == UserRole.IT_SUPPORT).all()
    workload = []
    active = [TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_FOR_USER, TicketStatus.ESCALATED, TicketStatus.REOPENED]
    for eng in engineers:
        count = db.query(func.count(Ticket.id)).filter(Ticket.assigned_to == eng.id, Ticket.status.in_(active)).scalar()
        workload.append({"engineer": eng.name, "active_tickets": count or 0})

    suppressed = sum(1 for t in tickets if t.status in {TicketStatus.SUPPRESSED, TicketStatus.REJECTED})
    return DashboardManager(
        total_tickets=len(tickets),
        open=sum(1 for t in tickets if t.status == TicketStatus.OPEN),
        in_progress=sum(1 for t in tickets if t.status == TicketStatus.IN_PROGRESS),
        resolved=sum(1 for t in tickets if t.status == TicketStatus.RESOLVED),
        closed=sum(1 for t in tickets if t.status == TicketStatus.CLOSED),
        suppressed=suppressed,
        severity_distribution=severity,
        category_distribution=categories,
        team_workload=workload,
        ai_metrics={
            "validation_accuracy": 0.92,
            "auto_validated": len(tickets) - suppressed,
            "suppressed": suppressed,
            "escalations": sum(1 for t in tickets if t.status == TicketStatus.ESCALATED),
        },
        recent_tickets=sorted(tickets, key=lambda t: t.created_at, reverse=True)[:10],
    )


@router.get("/knowledge-base", response_model=list[KnowledgeBaseOut])
def knowledge_base(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(KnowledgeBaseArticle).all()


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER))):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()


@router.get("/team", response_model=list[ITProfileOut])
def team(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER))):
    profiles = db.query(ITProfile).options(joinedload(ITProfile.user)).all()
    return profiles


@router.get("/tickets/suppressed", response_model=list[TicketOut])
def suppressed_tickets(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.IT_MANAGER))):
    return db.query(Ticket).filter(Ticket.status.in_([TicketStatus.SUPPRESSED, TicketStatus.REJECTED])).all()

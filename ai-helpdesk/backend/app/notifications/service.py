from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Notification, NotificationType, User, UserRole

settings = get_settings()


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType,
    ticket_id: int | None = None,
) -> Notification | None:
    if not settings.notification_enabled:
        return None
    notification = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.add(notification)
    db.flush()
    return notification


def notify_assignment(db: Session, assignee: User, ticket_id: int, ticket_number: str, title: str, priority: str, category: str, reason: str):
    create_notification(
        db,
        user_id=assignee.id,
        title="New Ticket Assigned",
        message=f"{ticket_number}\n{title}\nPriority: {priority}\nCategory: {category}\n{reason}",
        notification_type=NotificationType.TICKET_ASSIGNMENT,
        ticket_id=ticket_id,
    )


def notify_managers_escalation(db: Session, ticket_number: str, title: str):
    managers = db.query(User).filter(User.role == UserRole.IT_MANAGER, User.is_active == True).all()
    for manager in managers:
        create_notification(
            db,
            user_id=manager.id,
            title="P1 Escalation Alert",
            message=f"Critical ticket {ticket_number}: {title} requires manager attention.",
            notification_type=NotificationType.ESCALATION,
        )

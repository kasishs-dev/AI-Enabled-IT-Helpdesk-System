from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.auth.security import get_password_hash
from app.models import (
    AIAnalysis,
    AnalysisType,
    AuditLog,
    ITProfile,
    KnowledgeBaseArticle,
    Notification,
    NotificationType,
    Ticket,
    TicketComment,
    TicketStatus,
    User,
    UserRole,
)


def seed_database(db: Session):
    if db.query(User).first():
        return

    users = [
        User(name="Rahul Sharma", email="rahul@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.USER),
        User(name="Amit Patel", email="amit@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.IT_SUPPORT),
        User(name="Priya Mehta", email="priya@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.IT_SUPPORT),
        User(name="Raj Shah", email="raj@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.IT_SUPPORT),
        User(name="Neha Shah", email="neha@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.IT_MANAGER),
        User(name="Sneha Gupta", email="sneha@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.USER),
        User(name="Vikram Singh", email="vikram@demo.com", hashed_password=get_password_hash("Demo@123"), role=UserRole.USER),
    ]
    db.add_all(users)
    db.flush()

    profiles = [
        ITProfile(user_id=users[1].id, expertise=["Network", "VPN", "WiFi", "Connectivity"], max_active_tickets=10),
        ITProfile(user_id=users[2].id, expertise=["Laptop", "Hardware", "Windows", "Software", "Application"], max_active_tickets=8),
        ITProfile(user_id=users[3].id, expertise=["Network", "VPN", "Server", "Database"], max_active_tickets=8),
    ]
    db.add_all(profiles)

    kb_articles = [
        ("How to reset your password", "Password / Account", "Use the self-service portal at https://portal.company.com/reset ..."),
        ("VPN troubleshooting", "VPN", "1. Check internet 2. Restart VPN client 3. Verify credentials ..."),
        ("WiFi troubleshooting", "WiFi", "Forget network, reconnect, verify corporate credentials ..."),
        ("Email configuration", "Email", "Configure Outlook with autodiscover ..."),
        ("Printer troubleshooting", "Printer", "Clear print queue, reinstall driver ..."),
        ("Windows troubleshooting", "Software", "Run sfc /scannow, check updates ..."),
        ("Software installation", "Application", "Request software via portal or contact IT ..."),
    ]
    for title, category, content in kb_articles:
        db.add(KnowledgeBaseArticle(title=title, category=category, content=content, tags=[category.lower()]))

    now = datetime.utcnow()
    ticket_specs = [
        ("INC-000001", "VPN unavailable for employees", "Multiple users report VPN connection failures.", users[0].id, users[1].id, "VPN", "VPN Outage", "P2", "HIGH", TicketStatus.IN_PROGRESS),
        ("INC-000002", "Laptop screen flickering", "Screen flickers intermittently during use.", users[5].id, users[2].id, "Hardware", "Display", "P3", "MEDIUM", TicketStatus.ASSIGNED),
        ("INC-000003", "Outlook not syncing", "Emails stuck in outbox since morning.", users[6].id, users[2].id, "Email", "Sync", "P3", "MEDIUM", TicketStatus.OPEN),
        ("INC-000004", "Cannot access shared drive", "Network drive X: unavailable.", users[0].id, users[3].id, "Network", "File Share", "P2", "HIGH", TicketStatus.WAITING_FOR_USER),
        ("INC-000005", "Printer jam on 3rd floor", "Printer showing paper jam error.", users[5].id, users[2].id, "Printer", "Hardware", "P4", "LOW", TicketStatus.RESOLVED),
        ("INC-000006", "Password expired", "Unable to login, password expired message.", users[6].id, None, "Password / Account", "Account", "P4", "LOW", TicketStatus.CLOSED),
        ("INC-000007", "Application crash on launch", "CRM app crashes immediately.", users[0].id, users[2].id, "Application", "CRM", "P3", "MEDIUM", TicketStatus.IN_PROGRESS),
        ("INC-000008", "WiFi disconnecting frequently", "Laptop drops WiFi every few minutes.", users[5].id, users[1].id, "WiFi", "Connectivity", "P3", "MEDIUM", TicketStatus.ASSIGNED),
        ("INC-000009", "Security alert - suspicious email", "Received phishing email, clicked link.", users[6].id, users[3].id, "Security", "Phishing", "P1", "CRITICAL", TicketStatus.ESCALATED),
        ("INC-000010", "Software install request", "Need Adobe Acrobat installed.", users[0].id, users[2].id, "Software", "Installation", "P4", "LOW", TicketStatus.OPEN),
        ("INC-000011", "Database connection timeout", "Reporting tool cannot connect to DB.", users[5].id, users[3].id, "Database", "Connection", "P2", "HIGH", TicketStatus.IN_PROGRESS),
        ("INC-000012", "VPN slow performance", "VPN connected but very slow.", users[6].id, users[1].id, "VPN", "Performance", "P3", "MEDIUM", TicketStatus.RESOLVED),
        ("INC-000013", "Hello", "Hello", users[0].id, None, "Other", "Invalid", "P4", "LOW", TicketStatus.REJECTED),
        ("INC-000014", "Mouse not working", "USB mouse not detected.", users[5].id, users[2].id, "Hardware", "Peripheral", "P4", "LOW", TicketStatus.CLOSED),
        ("INC-000015", "Server maintenance notification", "Need info about server downtime.", users[6].id, users[3].id, "Server", "Maintenance", "P4", "LOW", TicketStatus.RESOLVED),
        ("INC-000016", "Teams not loading", "Microsoft Teams stuck on loading screen.", users[0].id, users[2].id, "Application", "Teams", "P3", "MEDIUM", TicketStatus.OPEN),
        ("INC-000017", "Access request - finance folder", "Need read access to finance share.", users[5].id, None, "Access Request", "Permissions", "P3", "MEDIUM", TicketStatus.OPEN),
        ("INC-000018", "Blue screen on boot", "Laptop shows BSOD on startup.", users[6].id, users[2].id, "Hardware", "BSOD", "P2", "HIGH", TicketStatus.ASSIGNED),
    ]

    for num, title, desc, req_id, assign_id, cat, subcat, sev, pri, status in ticket_specs:
        t = Ticket(
            ticket_number=num,
            title=title,
            description=desc,
            requester_id=req_id,
            assigned_to=assign_id,
            category=cat,
            subcategory=subcat,
            severity=sev,
            priority=pri,
            status=status,
            ai_confidence=0.9,
            ai_summary=desc[:100],
            ai_validation_result="GENUINE" if status not in [TicketStatus.REJECTED, TicketStatus.SUPPRESSED] else "INVALID",
            ai_reasoning="Demo seeded ticket",
            created_at=now - timedelta(days=len(num) % 10, hours=int(num[-3:])),
            updated_at=now - timedelta(hours=int(num[-2:])),
        )
        if status == TicketStatus.RESOLVED:
            t.resolved_at = now - timedelta(hours=2)
        if status == TicketStatus.CLOSED:
            t.resolved_at = now - timedelta(days=1)
            t.closed_at = now - timedelta(hours=12)
        db.add(t)

    db.flush()

    tickets = db.query(Ticket).all()
    for t in tickets[:5]:
        db.add(TicketComment(ticket_id=t.id, author_id=t.requester_id, content="Initial report submitted.", is_internal=False))
        if t.assigned_to:
            db.add(TicketComment(ticket_id=t.id, author_id=t.assigned_to, content="Investigating the issue.", is_internal=True))

    for t in tickets:
        if t.assigned_to and t.status in [TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]:
            db.add(
                Notification(
                    user_id=t.assigned_to,
                    ticket_id=t.id,
                    type=NotificationType.TICKET_ASSIGNMENT,
                    title="Ticket Assigned",
                    message=f"{t.ticket_number} - {t.title}",
                    is_read=t.id % 2 == 0,
                )
            )

    audit_samples = [
        ("Ticket created", "ticket", 1, None, "INC-000001"),
        ("AI validated issue", "ticket", 1, None, "GENUINE"),
        ("Ticket assigned", "ticket", 1, None, "Amit Patel"),
        ("Status changed", "ticket", 2, "OPEN", "IN_PROGRESS"),
        ("Manager override", "ticket", 4, "P3", "P2"),
    ]
    for action, etype, eid, old, new in audit_samples:
        db.add(AuditLog(actor_id=users[4].id, action=action, entity_type=etype, entity_id=eid, old_value=old, new_value=new))

    db.add(
        AIAnalysis(
            ticket_id=1,
            analysis_type=AnalysisType.VALIDATION,
            model="mock-v1",
            prompt_version="v1",
            input_data={"title": "VPN unavailable"},
            output_data={"is_genuine": True, "confidence": 0.94},
            confidence=0.94,
        )
    )

    db.commit()

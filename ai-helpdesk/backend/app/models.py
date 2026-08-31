import enum
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    USER = "USER"
    IT_SUPPORT = "IT_SUPPORT"
    IT_MANAGER = "IT_MANAGER"


class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    SUPPRESSED = "SUPPRESSED"
    REJECTED = "REJECTED"


class SuppressionOutcome(str, enum.Enum):
    SUPPRESSED = "SUPPRESSED"
    REJECTED = "REJECTED"
    SELF_SERVICE = "SELF_SERVICE"
    DUPLICATE = "DUPLICATE"
    INVALID = "INVALID"


class AnalysisType(str, enum.Enum):
    INITIAL_ANALYSIS = "INITIAL_ANALYSIS"
    VALIDATION = "VALIDATION"
    CATEGORIZATION = "CATEGORIZATION"
    SEVERITY = "SEVERITY"
    DUPLICATE_DETECTION = "DUPLICATE_DETECTION"
    SUGGESTION = "SUGGESTION"


class NotificationType(str, enum.Enum):
    TICKET_ASSIGNMENT = "TICKET_ASSIGNMENT"
    TICKET_UPDATE = "TICKET_UPDATE"
    ESCALATION = "ESCALATION"
    RESOLUTION = "RESOLUTION"
    MANAGER_ALERT = "MANAGER_ALERT"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    it_profile = relationship("ITProfile", back_populates="user", uselist=False)
    tickets_requested = relationship("Ticket", back_populates="requester", foreign_keys="Ticket.requester_id")
    tickets_assigned = relationship("Ticket", back_populates="assignee", foreign_keys="Ticket.assigned_to")
    notifications = relationship("Notification", back_populates="user")


class ITProfile(Base):
    __tablename__ = "it_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    expertise = Column(JSON, default=list)
    availability = Column(Boolean, default=True)
    max_active_tickets = Column(Integer, default=10)
    severity_capability = Column(JSON, default=lambda: ["P1", "P2", "P3", "P4"])

    user = relationship("User", back_populates="it_profile")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(80))
    subcategory = Column(String(120))
    severity = Column(String(10))
    priority = Column(String(20))
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    ai_confidence = Column(Float)
    ai_summary = Column(Text)
    ai_validation_result = Column(String(50))
    ai_reasoning = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    device = Column(String(120))
    operating_system = Column(String(120))
    location = Column(String(120))
    application_system = Column(String(120))
    attachment_path = Column(String(500))
    duplicate_of_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    suppression_outcome = Column(Enum(SuppressionOutcome), nullable=True)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    requester = relationship("User", back_populates="tickets_requested", foreign_keys=[requester_id])
    assignee = relationship("User", back_populates="tickets_assigned", foreign_keys=[assigned_to])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    assignments = relationship("TicketAssignment", back_populates="ticket", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="ticket", cascade="all, delete-orphan")
    duplicate_of = relationship("Ticket", remote_side=[id])


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User")


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assignment_score = Column(Float)
    reason = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="assignments")
    assignee = relationship("User", foreign_keys=[assignee_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    ticket = relationship("Ticket")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    old_value = Column(Text)
    new_value = Column(Text)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    actor = relationship("User")


class KnowledgeBaseArticle(Base):
    __tablename__ = "knowledge_base_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(80))
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    model = Column(String(80))
    prompt_version = Column(String(40))
    input_data = Column(JSON)
    output_data = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="ai_analyses")


class IssueRequest(Base):
    __tablename__ = "issue_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    device = Column(String(120))
    operating_system = Column(String(120))
    location = Column(String(120))
    application_system = Column(String(120))
    status = Column(String(50), default="PROCESSING")
    ai_result = Column(JSON)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requester = relationship("User")
    ticket = relationship("Ticket")

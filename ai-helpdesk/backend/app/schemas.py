from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole, TicketStatus, NotificationType, SuppressionOutcome


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class ITProfileOut(BaseModel):
    id: int
    user_id: int
    expertise: list[str]
    availability: bool
    max_active_tickets: int
    severity_capability: list[str]
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True


class IssueSubmit(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)
    device: Optional[str] = None
    operating_system: Optional[str] = None
    location: Optional[str] = None
    application_system: Optional[str] = None


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    is_internal: bool = False


class CommentOut(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    content: str
    is_internal: bool
    created_at: datetime
    author: Optional[UserOut] = None

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    requester_id: int
    category: Optional[str]
    subcategory: Optional[str]
    severity: Optional[str]
    priority: Optional[str]
    status: TicketStatus
    ai_confidence: Optional[float]
    ai_summary: Optional[str]
    ai_validation_result: Optional[str]
    ai_reasoning: Optional[str]
    assigned_to: Optional[int]
    device: Optional[str]
    operating_system: Optional[str]
    location: Optional[str]
    application_system: Optional[str]
    duplicate_of_id: Optional[int]
    suppression_outcome: Optional[SuppressionOutcome]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    requester: Optional[UserOut] = None
    assignee: Optional[UserOut] = None
    comments: list[CommentOut] = []

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: TicketStatus
    reason: Optional[str] = None
    resolution_notes: Optional[str] = None


class SeverityUpdate(BaseModel):
    severity: str
    priority: Optional[str] = None
    reason: str


class CategoryUpdate(BaseModel):
    category: str
    subcategory: Optional[str] = None
    reason: str


class AssignmentUpdate(BaseModel):
    assignee_id: int
    reason: str


class OverrideValidation(BaseModel):
    is_genuine: bool
    reason: str


class NotificationOut(BaseModel):
    id: int
    user_id: int
    ticket_id: Optional[int]
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    actor_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseOut(BaseModel):
    id: int
    title: str
    category: Optional[str]
    content: str
    tags: list[str]

    class Config:
        from_attributes = True


class IssueProcessResult(BaseModel):
    success: bool
    ticket_created: bool
    suppressed: bool
    outcome: Optional[str] = None
    message: str
    analysis: dict[str, Any]
    suggestions: list[str]
    ticket: Optional[TicketOut] = None
    duplicate_ticket_number: Optional[str] = None


class DashboardUser(BaseModel):
    welcome_name: str
    open_tickets: int
    in_progress: int
    waiting_for_user: int
    resolved: int
    pending_requests: int
    recent_tickets: list[TicketOut]


class DashboardIT(BaseModel):
    assigned_to_me: int
    high_priority: int
    in_progress: int
    waiting_for_user: int
    resolved_today: int
    tickets: list[TicketOut]


class DashboardManager(BaseModel):
    total_tickets: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    suppressed: int
    severity_distribution: dict[str, int]
    category_distribution: dict[str, int]
    team_workload: list[dict[str, Any]]
    ai_metrics: dict[str, Any]
    recent_tickets: list[TicketOut]

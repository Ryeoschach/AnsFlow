"""
Pydantic schemas for API request/response models
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


# Enums
class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WebhookEventType(str, Enum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    MERGE_REQUEST = "merge_request"
    TAG = "tag"
    RELEASE = "release"
    BUILD_COMPLETE = "build_complete"
    DEPLOY_COMPLETE = "deploy_complete"


class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields"""
    
    class Config:
        from_attributes = True
        use_enum_values = True


# User schemas
class UserSchema(BaseSchema):
    """User schema"""
    id: str
    username: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreateSchema(BaseSchema):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    is_superuser: bool = False


class UserUpdateSchema(BaseSchema):
    """User update schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


# Project schemas
class ProjectSchema(BaseSchema):
    """Project schema"""
    id: str
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_by: str
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = {}


class ProjectCreateSchema(BaseSchema):
    """Project creation schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = None
    settings: Dict[str, Any] = {}


class ProjectUpdateSchema(BaseSchema):
    """Project update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[Dict[str, Any]] = None


# Pipeline schemas
class PipelineSchema(BaseSchema):
    """Pipeline schema"""
    id: str
    name: str
    project_id: str
    definition: Dict[str, Any]
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: datetime
    updated_at: datetime
    created_by: str


class PipelineCreateSchema(BaseSchema):
    """Pipeline creation schema"""
    name: str = Field(..., min_length=1, max_length=100)
    project_id: str
    definition: Dict[str, Any]


class PipelineUpdateSchema(BaseSchema):
    """Pipeline update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    definition: Optional[Dict[str, Any]] = None
    status: Optional[PipelineStatus] = None


# Pipeline run schemas
class PipelineRunSchema(BaseSchema):
    """Pipeline run schema"""
    id: str
    pipeline_id: str
    status: PipelineStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    logs: List[str] = []
    run_metadata: Dict[str, Any] = {}  # Renamed from metadata
    triggered_by: str
    created_at: datetime


class PipelineRunCreateSchema(BaseSchema):
    """Pipeline run creation schema"""
    pipeline_id: str
    run_metadata: Dict[str, Any] = {}  # Renamed from metadata


# Webhook schemas
class WebhookEventSchema(BaseSchema):
    """Webhook event schema"""
    id: str
    event_type: WebhookEventType
    source: str  # github, gitlab, jenkins, etc.
    payload: Dict[str, Any]
    project_id: Optional[str] = None
    processed: bool = False
    created_at: datetime


class WebhookCreateSchema(BaseSchema):
    """Webhook creation schema"""
    event_type: WebhookEventType
    source: str
    payload: Dict[str, Any]
    project_id: Optional[str] = None


# GitHub webhook schemas
class GitHubPushEventSchema(BaseSchema):
    """GitHub push event schema"""
    ref: str
    before: str
    after: str
    repository: Dict[str, Any]
    pusher: Dict[str, Any]
    commits: List[Dict[str, Any]] = []


class GitHubPullRequestEventSchema(BaseSchema):
    """GitHub pull request event schema"""
    action: str
    number: int
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]


# GitLab webhook schemas
class GitLabPushEventSchema(BaseSchema):
    """GitLab push event schema"""
    object_kind: str
    ref: str
    before: str
    after: str
    repository: Dict[str, Any]
    commits: List[Dict[str, Any]] = []


class GitLabMergeRequestEventSchema(BaseSchema):
    """GitLab merge request event schema"""
    object_kind: str
    user: Dict[str, Any]
    object_attributes: Dict[str, Any]
    repository: Dict[str, Any]


# Jenkins webhook schemas
class JenkinsEventSchema(BaseSchema):
    """Jenkins event schema"""
    name: str
    url: str
    build: Dict[str, Any]


# Notification schemas
class NotificationSchema(BaseSchema):
    """Notification schema"""
    id: str
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    read: bool = False
    created_at: datetime


class NotificationCreateSchema(BaseSchema):
    """Notification creation schema"""
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    level: NotificationLevel = NotificationLevel.INFO
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    pipeline_id: Optional[str] = None


# WebSocket message schemas
class WebSocketMessageSchema(BaseSchema):
    """WebSocket message schema"""
    type: str
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineUpdateMessageSchema(WebSocketMessageSchema):
    """Pipeline update WebSocket message"""
    type: str = "pipeline_update"
    pipeline_id: str
    status: PipelineStatus
    progress: Optional[int] = None  # 0-100
    logs: List[str] = []


class ProjectUpdateMessageSchema(WebSocketMessageSchema):
    """Project update WebSocket message"""
    type: str = "project_update"
    project_id: str
    event: str  # created, updated, deleted, etc.
    data: Dict[str, Any] = {}


class SystemNotificationMessageSchema(WebSocketMessageSchema):
    """System notification WebSocket message"""
    type: str = "system_notification"
    level: NotificationLevel
    title: str
    message: str


# Authentication schemas
class TokenSchema(BaseSchema):
    """Token schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginRequestSchema(BaseSchema):
    """Login request schema"""
    username: str
    password: str


# Response schemas
class ResponseSchema(BaseSchema):
    """Base response schema"""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None


class ErrorResponseSchema(BaseSchema):
    """Error response schema"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class PaginatedResponseSchema(BaseSchema):
    """Paginated response schema"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


# Health check schemas
class HealthCheckSchema(BaseSchema):
    """Health check schema"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: Dict[str, Any]
    services: Dict[str, Any] = {}


class ComponentHealthSchema(BaseSchema):
    """Component health schema"""
    name: str
    status: str  # healthy, unhealthy, degraded
    details: Optional[Dict[str, Any]] = None
    last_check: datetime

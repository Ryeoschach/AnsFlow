"""
SQLAlchemy database models
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from ..core.database import Base


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class User(BaseModel):
    """User model"""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    pipeline_runs = relationship("PipelineRun", back_populates="triggered_by_user")
    notifications = relationship("Notification", back_populates="user")


class Project(BaseModel):
    """Project model"""
    __tablename__ = "projects"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    repository_url = Column(String(500))
    status = Column(String(20), default="active", nullable=False, index=True)
    settings = Column(JSON, default={})
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    pipelines = relationship("Pipeline", back_populates="project", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEvent", back_populates="project")
    notifications = relationship("Notification", back_populates="project")
    
    # Indexes
    __table_args__ = (
        Index("idx_project_name_status", "name", "status"),
        Index("idx_project_created_by", "created_by"),
    )


class Pipeline(BaseModel):
    """Pipeline model"""
    __tablename__ = "pipelines"
    
    name = Column(String(100), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    definition = Column(JSON, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="pipelines")
    runs = relationship("PipelineRun", back_populates="pipeline", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="pipeline")
    
    # Indexes
    __table_args__ = (
        Index("idx_pipeline_project_status", "project_id", "status"),
        Index("idx_pipeline_name", "name"),
    )


class PipelineRun(BaseModel):
    """Pipeline run model"""
    __tablename__ = "pipeline_runs"
    
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    logs = Column(JSON, default=[])
    run_metadata = Column(JSON, default={})  # Renamed from metadata
    triggered_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="runs")
    triggered_by_user = relationship("User", back_populates="pipeline_runs")
    
    # Indexes
    __table_args__ = (
        Index("idx_pipeline_run_pipeline_status", "pipeline_id", "status"),
        Index("idx_pipeline_run_created_at", "created_at"),
        Index("idx_pipeline_run_triggered_by", "triggered_by"),
    )


class WebhookEvent(BaseModel):
    """Webhook event model"""
    __tablename__ = "webhook_events"
    
    event_type = Column(String(50), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)  # github, gitlab, jenkins, etc.
    payload = Column(JSON, nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"))
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processing_result = Column(JSON)
    
    # Relationships
    project = relationship("Project", back_populates="webhooks")
    
    # Indexes
    __table_args__ = (
        Index("idx_webhook_event_type_source", "event_type", "source"),
        Index("idx_webhook_processed", "processed"),
        Index("idx_webhook_created_at", "created_at"),
    )


class Notification(BaseModel):
    """Notification model"""
    __tablename__ = "notifications"
    
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(20), default="info", nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    project_id = Column(String(36), ForeignKey("projects.id"))
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"))
    read = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    project = relationship("Project", back_populates="notifications")
    pipeline = relationship("Pipeline", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index("idx_notification_user_read", "user_id", "read"),
        Index("idx_notification_level", "level"),
        Index("idx_notification_created_at", "created_at"),
    )


class ApiKey(BaseModel):
    """API key model for webhook authentication"""
    __tablename__ = "api_keys"
    
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    permissions = Column(JSON, default=[])  # List of permissions
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index("idx_api_key_active", "is_active"),
        Index("idx_api_key_created_by", "created_by"),
    )


class SystemMetric(BaseModel):
    """System metrics model for monitoring"""
    __tablename__ = "system_metrics"
    
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(String(500), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    labels = Column(JSON, default={})
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_system_metric_name_timestamp", "metric_name", "timestamp"),
        Index("idx_system_metric_type", "metric_type"),
    )


class AuditLog(BaseModel):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    changes = Column(JSON)  # Before/after changes
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text)
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_log_action_resource", "action", "resource_type"),
        Index("idx_audit_log_user", "user_id"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_created_at", "created_at"),
    )

"""
SQLAlchemy models for the CRDB tuning report generator (synchronous version)
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database_sync import Base
from typing import List, Optional
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    role = Column(String, server_default="analyst")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_reports = relationship(
        "Report",
        back_populates="creator",
        primaryjoin="User.id==Report.created_by",
        foreign_keys="Report.created_by",
    )
    status_changed_reports = relationship(
        "Report",
        back_populates="status_changer",
        primaryjoin="User.id==Report.status_changed_by",
        foreign_keys="Report.status_changed_by",
    )

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    cluster_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, server_default="draft")
    generated_at = Column(DateTime(timezone=True))
    version = Column(Integer, server_default="1")
    # Map Python attribute to DB column named 'metadata' (avoid reserved name in SQLAlchemy)
    report_metadata = Column("metadata", JSONB)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    status_changed_by = Column(String, ForeignKey("users.id"))
    status_changed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_reports", foreign_keys=[created_by])
    status_changer = relationship("User", back_populates="status_changed_reports", foreign_keys=[status_changed_by])
    findings = relationship("Finding", back_populates="report", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="report", cascade="all, delete-orphan")
    status_history = relationship("ReportStatusHistory", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(status.in_(["draft", "in_review", "published", "archived"]), name="check_status"),
    )

class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    category = Column(String, nullable=False)
    severity = Column(String, nullable=False, server_default="medium")
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    details = Column(JSONB)
    status = Column(String, nullable=False, server_default="open")
    tags = Column(ARRAY(String))
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    report = relationship("Report", back_populates="findings")
    creator = relationship("User", foreign_keys=[created_by])
    actions = relationship("RecommendedAction", back_populates="finding", cascade="all, delete-orphan")
    status_history = relationship("FindingStatusHistory", back_populates="finding", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(category.in_(["performance", "configuration", "security", "reliability", "monitoring"]), name="check_category"),
        CheckConstraint(severity.in_(["low", "medium", "high", "critical"]), name="check_severity"),
        CheckConstraint(status.in_(["open", "acknowledged", "resolved", "false_positive"]), name="check_finding_status"),
    )

class RecommendedAction(Base):
    __tablename__ = "recommended_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    action_type = Column(String, nullable=False)
    priority = Column(String, nullable=False, server_default="medium")
    estimated_effort = Column(String, server_default="medium")
    status = Column(String, nullable=False, server_default="pending")
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    implementation_notes = Column(Text)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    status_changed_by = Column(String, ForeignKey("users.id"))
    status_changed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    finding = relationship("Finding", back_populates="actions")
    creator = relationship("User", foreign_keys=[created_by])
    status_changer = relationship("User", foreign_keys=[status_changed_by])
    status_history = relationship("ActionStatusHistory", back_populates="action", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(action_type.in_(["configuration_change", "query_optimization", "index_creation", "hardware_upgrade", "monitoring_setup", "backup_strategy", "security_hardening"]), name="check_action_type"),
        CheckConstraint(priority.in_(["low", "medium", "high", "urgent"]), name="check_priority"),
        CheckConstraint(estimated_effort.in_(["low", "medium", "high"]), name="check_effort"),
        CheckConstraint(status.in_(["pending", "in_progress", "completed", "cancelled"]), name="check_action_status"),
    )

class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"))
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    report = relationship("Report", back_populates="comments", foreign_keys=[report_id])
    author = relationship("User", foreign_keys=[author_id])
    parent_comment = relationship("Comment", remote_side=[id], foreign_keys=[parent_comment_id])
    replies = relationship("Comment", back_populates="parent_comment", cascade="all, delete-orphan")

class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    old_status = Column(String)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, ForeignKey("users.id"), nullable=False)
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    report = relationship("Report", back_populates="status_history")
    changer = relationship("User", foreign_keys=[changed_by])

class FindingStatusHistory(Base):
    __tablename__ = "finding_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)
    old_status = Column(String)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, ForeignKey("users.id"), nullable=False)
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    finding = relationship("Finding", back_populates="status_history")
    changer = relationship("User", foreign_keys=[changed_by])

class ActionStatusHistory(Base):
    __tablename__ = "action_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    action_id = Column(UUID(as_uuid=True), ForeignKey("recommended_actions.id"), nullable=False)
    old_status = Column(String)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, ForeignKey("users.id"), nullable=False)
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    action = relationship("RecommendedAction", back_populates="status_history")
    changer = relationship("User", foreign_keys=[changed_by])

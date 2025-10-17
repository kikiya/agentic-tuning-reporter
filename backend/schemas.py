"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

# Base schema configurations
model_config = ConfigDict(from_attributes=True)

# User schemas
class UserBase(BaseModel):
    id: str
    name: str
    email: str
    role: str = "analyst"

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "analyst"

class UserResponse(UserBase):
    model_config = model_config
    created_at: datetime

# Report schemas
class ReportBase(BaseModel):
    cluster_id: str
    title: str
    description: Optional[str] = None
    status: str = "draft"

class ReportCreate(BaseModel):
    cluster_id: str
    title: str
    description: Optional[str] = None

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ReportResponse(ReportBase):
    model_config = model_config
    id: UUID
    generated_at: Optional[datetime] = None
    version: int = 1
    report_metadata: Optional[Dict[str, Any]] = None
    created_by: str
    status_changed_by: Optional[str] = None
    status_changed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# Finding schemas
class FindingBase(BaseModel):
    category: str
    severity: str = "medium"
    title: str
    description: str
    status: str = "open"
    tags: Optional[List[str]] = None

class FindingCreate(BaseModel):
    category: str
    severity: str = "medium"
    title: str
    description: str
    tags: Optional[List[str]] = None

class FindingUpdate(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

class FindingResponse(FindingBase):
    model_config = model_config
    id: UUID
    report_id: UUID
    details: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

# Recommended Action schemas
class RecommendedActionBase(BaseModel):
    title: str
    description: str
    action_type: str
    priority: str = "medium"
    estimated_effort: str = "medium"
    status: str = "pending"
    due_date: Optional[datetime] = None

class RecommendedActionCreate(BaseModel):
    title: str
    description: str
    action_type: str
    priority: str = "medium"
    estimated_effort: str = "medium"
    due_date: Optional[datetime] = None

class RecommendedActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    action_type: Optional[str] = None
    priority: Optional[str] = None
    estimated_effort: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    implementation_notes: Optional[str] = None

class RecommendedActionResponse(RecommendedActionBase):
    model_config = model_config
    id: UUID
    finding_id: UUID
    completed_at: Optional[datetime] = None
    implementation_notes: Optional[str] = None
    created_by: str
    status_changed_by: Optional[str] = None
    status_changed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# Comment schemas
class CommentBase(BaseModel):
    content: str
    parent_comment_id: Optional[UUID] = None

class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[UUID] = None

class CommentResponse(CommentBase):
    model_config = model_config
    id: UUID
    report_id: UUID
    author_id: str
    created_at: datetime
    updated_at: datetime

# Status History schemas
class ReportStatusHistoryResponse(BaseModel):
    model_config = model_config
    id: UUID
    report_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    change_reason: Optional[str] = None
    created_at: datetime

class FindingStatusHistoryResponse(BaseModel):
    model_config = model_config
    id: UUID
    finding_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    change_reason: Optional[str] = None
    created_at: datetime

class ActionStatusHistoryResponse(BaseModel):
    model_config = model_config
    id: UUID
    action_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    change_reason: Optional[str] = None
    created_at: datetime

# Response schemas with nested data
class FindingWithActions(FindingResponse):
    actions: List[RecommendedActionResponse] = []

class ReportWithFindings(ReportResponse):
    findings: List[FindingResponse] = []
    comments: List[CommentResponse] = []

class ReportDetail(ReportResponse):
    findings: List[FindingWithActions] = []
    comments: List[CommentResponse] = []
    status_history: List[ReportStatusHistoryResponse] = []

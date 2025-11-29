"""
Database service functions for CRUD operations (synchronous version)

This module provides database operations using synchronous SQLAlchemy.
All functions work with regular database sessions and are called from
FastAPI endpoints using dependency injection.

Functions in this module handle the business logic for creating, reading,
updating, and deleting entities while maintaining data integrity and audit trails.

Key features:
- Synchronous database operations
- Automatic audit trail creation for status changes
- Comprehensive error handling
- Type-safe parameter validation
- Cascade deletion handling
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
from typing import List, Optional
from datetime import datetime
import uuid

from models_sync import (
    User, Report, Finding, RecommendedAction, Comment,
    ReportStatusHistory, FindingStatusHistory, ActionStatusHistory,
    UserAccess
)
from schemas import (
    ReportCreate, ReportUpdate, FindingCreate, FindingUpdate,
    RecommendedActionCreate, RecommendedActionUpdate, CommentCreate
)

# Utility: ensure default 'system' user exists
def _ensure_system_user(db: Session):
    existing = db.query(User).filter(User.id == "system").first()
    if not existing:
        sys_user = User(
            id="system",
            name="System",
            email="system@example.com",
            role="admin",
        )
        db.add(sys_user)
        db.commit()

# ============================================================================
# USER SERVICES
# ============================================================================

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """
    Retrieve a user by their unique identifier.
    
    Args:
        db: Database session
        user_id: Unique string identifier for the user
    
    Returns:
        User object if found, None if no user exists with the given ID
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by their email address.
    
    Args:
        db: Database session
        email: Email address to search for
    
    Returns:
        User object if found, None if no user exists with the given email
    """
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_data) -> User:
    """
    Create a new user record in the database.
    
    Args:
        db: Database session
        user_data: Validated user creation data
    
    Returns:
        Newly created User object
    """
    db_user = User(**user_data.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ============================================================================
# REPORT SERVICES
# ============================================================================

def get_reports(db: Session, skip: int = 0, limit: int = 100) -> List[Report]:
    """
    Retrieve a paginated list of reports ordered by creation date.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of Report objects ordered by creation date (newest first)
    """
    return db.query(Report).order_by(desc(Report.created_at)).offset(skip).limit(limit).all()


def get_reports_for_user(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    include_admin: bool = True,
) -> List[Report]:
    """
    Retrieve reports accessible to a specific user based on customer access mappings.

    Args:
        db: Database session
        user_id: User identifier used in user_access table
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_admin: If True, users with role 'admin' get all reports

    Returns:
        List of accessible Report objects ordered by creation date
    """

    query = db.query(Report).order_by(desc(Report.created_at))

    # If we should honor admin role and user is admin, return all reports
    if include_admin:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "admin":
            return query.offset(skip).limit(limit).all()

    # Build subquery of accessible customer IDs
    accessible_customers_subquery = (
        select(UserAccess.customer_id)
        .where(UserAccess.user_id == user_id)
    )

    # Limit to reports from accessible customers
    query = query.filter(Report.customer_id.in_(accessible_customers_subquery))

    return query.offset(skip).limit(limit).all()

def get_report_by_id(db: Session, report_id: uuid.UUID) -> Optional[Report]:
    """
    Retrieve a specific report by its UUID with related data loaded.
    
    Args:
        db: Database session
        report_id: UUID of the report to retrieve
    
    Returns:
        Complete Report object with relationships loaded, or None if not found
    """
    return db.query(Report).filter(Report.id == report_id).first()

def get_reports_by_cluster(db: Session, cluster_id: str) -> List[Report]:
    """
    Retrieve all reports for a specific CRDB cluster.
    
    Args:
        db: Database session
        cluster_id: Unique identifier for the CRDB cluster
    
    Returns:
        List of Report objects for the specified cluster
    """
    return db.query(Report).filter(Report.cluster_id == cluster_id).order_by(desc(Report.created_at)).all()

def create_report(db: Session, report_data: ReportCreate, created_by: str) -> Report:
    """
    Create a new tuning report with initial audit trail.
    Automatically generates vector embedding for similarity search.
    
    Args:
        db: Database session
        report_data: Validated report creation data
        created_by: User ID of the person creating the report
    
    Returns:
        Newly created Report object
    """
    # Safety: make sure 'system' exists if using the default user
    if created_by == "system":
        _ensure_system_user(db)

    # Create report instance
    db_report = Report(
        **report_data.model_dump(),
        created_by=created_by,
        status_changed_by=created_by,
        status_changed_at=datetime.utcnow()
    )
    
    # Generate embedding if there's text content
    if db_report.title or db_report.description:
        try:
            from embedding_service import get_embedding_service
            embed_svc = get_embedding_service()
            text = f"{db_report.title}\n{db_report.description or ''}"
            db_report.embedding = embed_svc.embed_text(text)
            print(f"[INFO] Generated embedding for report '{db_report.title}'")
        except Exception as e:
            print(f"[WARNING] Failed to generate embedding for report: {e}")
            # Continue without embedding rather than failing the report creation
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # Add initial status history
    status_history = ReportStatusHistory(
        report_id=db_report.id,
        new_status=db_report.status,
        changed_by=created_by
    )
    db.add(status_history)
    db.commit()

    return db_report

def update_report(
    db: Session,
    report_id: uuid.UUID,
    report_update: ReportUpdate,
    changed_by: str
) -> Optional[Report]:
    """
    Update an existing report with change tracking and audit trail.
    
    Args:
        db: Database session
        report_id: UUID of the report to update
        report_update: Validated update data (may be partial)
        changed_by: User ID of the person making the changes
    
    Returns:
        Updated Report object if found, None if report doesn't exist
    """
    db_report = db.query(Report).filter(Report.id == report_id).first()

    if not db_report:
        return None

    # Track status change
    status_changed = False
    if report_update.status and report_update.status != db_report.status:
        status_changed = True
        old_status = db_report.status

    # Update fields
    update_data = report_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_report, field, value)

    # Update status change tracking
    if status_changed:
        db_report.status_changed_by = changed_by
        db_report.status_changed_at = datetime.utcnow()

        # Add status history record
        status_history = ReportStatusHistory(
            report_id=report_id,
            old_status=old_status,
            new_status=report_update.status,
            changed_by=changed_by
        )
        db.add(status_history)

    db.commit()
    db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: uuid.UUID) -> bool:
    """
    Delete a report and all its related data.
    
    Args:
        db: Database session
        report_id: UUID of the report to delete
    
    Returns:
        True if report was deleted, False if report was not found
    """
    db_report = db.query(Report).filter(Report.id == report_id).first()

    if not db_report:
        return False

    db.delete(db_report)
    db.commit()
    return True

# ============================================================================
# FINDING SERVICES
# ============================================================================

def get_findings_by_report(db: Session, report_id: uuid.UUID) -> List[Finding]:
    """
    Retrieve all findings associated with a specific report.
    
    Args:
        db: Database session
        report_id: UUID of the report to get findings for
    
    Returns:
        List of Finding objects ordered by creation date
    """
    return db.query(Finding).filter(Finding.report_id == report_id).order_by(desc(Finding.created_at)).all()

def get_finding_by_id(db: Session, finding_id: uuid.UUID) -> Optional[Finding]:
    """
    Retrieve a specific finding by its UUID.
    
    Args:
        db: Database session
        finding_id: UUID of the finding to retrieve
    
    Returns:
        Finding object if found, None if no finding exists with the given ID
    """
    return db.query(Finding).filter(Finding.id == finding_id).first()

def create_finding(
    db: Session,
    finding_data: FindingCreate,
    report_id: uuid.UUID,
    created_by: str
) -> Finding:
    """
    Create a new finding for a specific report with audit trail.
    Automatically generates vector embedding for similarity search.
    
    Args:
        db: Database session
        finding_data: Validated finding creation data
        report_id: UUID of the report this finding belongs to
        created_by: User ID of the person creating the finding
    
    Returns:
        Newly created Finding object
    """
    db_finding = Finding(
        **finding_data.model_dump(),
        report_id=report_id,
        created_by=created_by
    )
    
    # Generate embedding for the finding
    if db_finding.title or db_finding.description:
        try:
            from embedding_service import get_embedding_service
            embed_svc = get_embedding_service()
            text = f"{db_finding.title}\n{db_finding.description}\nCategory: {db_finding.category}\nSeverity: {db_finding.severity}"
            db_finding.embedding = embed_svc.embed_text(text)
            print(f"[INFO] Generated embedding for finding '{db_finding.title}'")
        except Exception as e:
            print(f"[WARNING] Failed to generate embedding for finding: {e}")
            # Continue without embedding
    
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)

    # Add initial status history
    status_history = FindingStatusHistory(
        finding_id=db_finding.id,
        new_status=db_finding.status,
        changed_by=created_by
    )
    db.add(status_history)
    db.commit()

    return db_finding

def update_finding(
    db: Session,
    finding_id: uuid.UUID,
    finding_update: FindingUpdate,
    changed_by: str
) -> Optional[Finding]:
    """
    Update an existing finding with change tracking.
    
    Args:
        db: Database session
        finding_id: UUID of the finding to update
        finding_update: Validated update data (may be partial)
        changed_by: User ID of the person making the changes
    
    Returns:
        Updated Finding object if found, None if finding doesn't exist
    """
    db_finding = db.query(Finding).filter(Finding.id == finding_id).first()

    if not db_finding:
        return None

    # Track status change
    status_changed = False
    if finding_update.status and finding_update.status != db_finding.status:
        status_changed = True
        old_status = db_finding.status

    # Update fields
    update_data = finding_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_finding, field, value)

    if status_changed:
        # Add status history record
        status_history = FindingStatusHistory(
            finding_id=finding_id,
            old_status=old_status,
            new_status=finding_update.status,
            changed_by=changed_by
        )
        db.add(status_history)

    db.commit()
    db.refresh(db_finding)
    return db_finding

def delete_finding(db: Session, finding_id: uuid.UUID) -> bool:
    """
    Delete a finding and all its related actions.
    
    Args:
        db: Database session
        finding_id: UUID of the finding to delete
    
    Returns:
        True if finding was deleted, False if finding was not found
    """
    db_finding = db.query(Finding).filter(Finding.id == finding_id).first()

    if not db_finding:
        return False

    db.delete(db_finding)
    db.commit()
    return True

# ============================================================================
# RECOMMENDED ACTION SERVICES
# ============================================================================

def get_actions_by_finding(db: Session, finding_id: uuid.UUID) -> List[RecommendedAction]:
    """
    Retrieve all recommended actions for a specific finding.
    
    Args:
        db: Database session
        finding_id: UUID of the finding to get actions for
    
    Returns:
        List of RecommendedAction objects ordered by creation date
    """
    return db.query(RecommendedAction).filter(RecommendedAction.finding_id == finding_id).order_by(desc(RecommendedAction.created_at)).all()

def create_action(
    db: Session,
    action_data: RecommendedActionCreate,
    finding_id: uuid.UUID,
    created_by: str
) -> RecommendedAction:
    """
    Create a new recommended action for a finding with audit trail.
    
    Args:
        db: Database session
        action_data: Validated action creation data
        finding_id: UUID of the finding this action belongs to
        created_by: User ID of the person creating the action
    
    Returns:
        Newly created RecommendedAction object
    """
    db_action = RecommendedAction(
        **action_data.model_dump(),
        finding_id=finding_id,
        created_by=created_by,
        status_changed_by=created_by,
        status_changed_at=datetime.utcnow()
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)

    # Add initial status history
    status_history = ActionStatusHistory(
        action_id=db_action.id,
        new_status=db_action.status,
        changed_by=created_by
    )
    db.add(status_history)
    db.commit()

    return db_action

def update_action(
    db: Session,
    action_id: uuid.UUID,
    action_update: RecommendedActionUpdate,
    changed_by: str
) -> Optional[RecommendedAction]:
    """
    Update an existing recommended action with status change tracking.
    
    Args:
        db: Database session
        action_id: UUID of the action to update
        action_update: Validated update data (may be partial)
        changed_by: User ID of the person making the changes
    
    Returns:
        Updated RecommendedAction object if found, None if action doesn't exist
    """
    db_action = db.query(RecommendedAction).filter(RecommendedAction.id == action_id).first()

    if not db_action:
        return None

    # Track status change
    status_changed = False
    if action_update.status and action_update.status != db_action.status:
        status_changed = True
        old_status = db_action.status

        # Handle completion timestamp
        if action_update.status == "completed":
            db_action.completed_at = datetime.utcnow()

    # Update fields
    update_data = action_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_action, field, value)

    if status_changed:
        db_action.status_changed_by = changed_by
        db_action.status_changed_at = datetime.utcnow()

        # Add status history record
        status_history = ActionStatusHistory(
            action_id=action_id,
            old_status=old_status,
            new_status=action_update.status,
            changed_by=changed_by
        )
        db.add(status_history)

    db.commit()
    db.refresh(db_action)
    return db_action

# ============================================================================
# COMMENT SERVICES
# ============================================================================

def get_comments_by_report(db: Session, report_id: uuid.UUID) -> List[Comment]:
    """
    Retrieve all comments for a specific report.
    
    Args:
        db: Database session
        report_id: UUID of the report to get comments for
    
    Returns:
        List of Comment objects ordered by creation date
    """
    return db.query(Comment).filter(Comment.report_id == report_id).order_by(Comment.created_at).all()

def create_comment(
    db: Session,
    comment_data: CommentCreate,
    report_id: uuid.UUID,
    author_id: str
) -> Comment:
    """
    Create a new comment for a report.
    
    Args:
        db: Database session
        comment_data: Validated comment creation data
        report_id: UUID of the report this comment belongs to
        author_id: User ID of the person creating the comment
    
    Returns:
        Newly created Comment object
    """
    db_comment = Comment(
        **comment_data.model_dump(),
        report_id=report_id,
        author_id=author_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

# ============================================================================
# STATUS HISTORY SERVICES
# ============================================================================

def get_report_status_history(db: Session, report_id: uuid.UUID) -> List[ReportStatusHistory]:
    """
    Retrieve the complete status change history for a report.
    
    Args:
        db: Database session
        report_id: UUID of the report to get status history for
    
    Returns:
        List of ReportStatusHistory objects ordered by creation date
    """
    return db.query(ReportStatusHistory).filter(ReportStatusHistory.report_id == report_id).order_by(desc(ReportStatusHistory.created_at)).all()

def get_finding_status_history(db: Session, finding_id: uuid.UUID) -> List[FindingStatusHistory]:
    """
    Retrieve the complete status change history for a finding.
    
    Args:
        db: Database session
        finding_id: UUID of the finding to get status history for
    
    Returns:
        List of FindingStatusHistory objects ordered by creation date
    """
    return db.query(FindingStatusHistory).filter(FindingStatusHistory.finding_id == finding_id).order_by(desc(FindingStatusHistory.created_at)).all()

def get_action_status_history(db: Session, action_id: uuid.UUID) -> List[ActionStatusHistory]:
    """
    Retrieve the complete status change history for a recommended action.
    
    Args:
        db: Database session
        action_id: UUID of the action to get status history for
    
    Returns:
        List of ActionStatusHistory objects ordered by creation date
    """
    return db.query(ActionStatusHistory).filter(ActionStatusHistory.action_id == action_id).order_by(desc(ActionStatusHistory.created_at)).all()


# ============================================================================
# SIMILARITY SEARCH SERVICES
# ============================================================================

def search_similar_reports(
    db: Session,
    query_embedding: List[float],
    limit: int = 5,
    exclude_id: Optional[uuid.UUID] = None,
    user_id: Optional[str] = None,
    region: Optional[str] = None,
    min_status: Optional[str] = None,
    enforce_access: bool = True
) -> List[tuple]:
    """
    Find reports similar to the given embedding vector with access control.
    Uses vector distance for semantic similarity search.
    
    Args:
        db: Database session
        query_embedding: Vector embedding to search against (1536 dimensions)
        limit: Maximum number of results to return
        exclude_id: Optional report ID to exclude from results (e.g., the source report)
        user_id: User ID for access control filtering
        region: Optional region filter for compliance boundaries
        min_status: Optional minimum status filter (e.g., only 'published' reports)
        enforce_access: If True and user_id provided, enforce customer access control
    
    Returns:
        List of tuples containing (Report, distance_score)
        Lower distance = more similar
    """
    from sqlalchemy import bindparam, cast
    from sqlalchemy.types import ARRAY, Float, UserDefinedType
    from models_sync import UserAccess
    
    # Define VECTOR type for casting
    class VECTOR(UserDefinedType):
        cache_ok = True  # Safe to cache, dimensions are immutable
        
        def __init__(self, dim=1536):
            self.dim = dim
        
        def get_col_spec(self, **kw):
            return f"VECTOR({self.dim})"
    
    # Convert query_embedding to list if it's a numpy array
    if hasattr(query_embedding, 'tolist'):
        query_embedding = query_embedding.tolist()
    
    # Cast the bound parameter to VECTOR(1536) so CRDB recognizes it
    qv = cast(bindparam("qv", value=query_embedding, type_=ARRAY(Float)), VECTOR(1536))
    
    # Use the <-> operator for cosine distance
    distance = cast(Report.embedding.op("<->")(qv), Float).label('distance')
    
    # Build query with SQLAlchemy ORM
    query = (
        select(Report, distance)
        .where(Report.embedding.isnot(None))
    )
    
    # Apply access control if user_id is provided and enforcement is enabled
    if user_id and enforce_access:
        # Join with user_access to filter by accessible customers
        authorized_customers_subquery = (
            select(UserAccess.customer_id)
            .where(UserAccess.user_id == user_id)
            .subquery()
        )
        query = query.where(Report.customer_id.in_(select(authorized_customers_subquery)))
    
    # Apply other filters
    if exclude_id:
        query = query.where(Report.id != exclude_id)
    
    # Status filtering (only show published/reviewed reports by default)
    if min_status:
        query = query.where(Report.status == min_status)
    else:
        # Default: published and in_review
        query = query.where(Report.status.in_(['published', 'in_review']))
    
    # Region filtering (for compliance)
    if region:
        query = query.where(Report.region == region)
    
    # Exclude PII-flagged reports by default (safety)
    query = query.where(Report.pii_flag == False)
    
    # Order by distance (ascending: smaller = more similar) and limit
    query = query.order_by(distance).limit(limit)
    
    # Execute query (embedding already in bindparam)
    results = db.execute(query).all()
    
    return [(row.Report, row.distance) for row in results]


def search_similar_findings(
    db: Session,
    query_embedding: List[float],
    limit: int = 10,
    exclude_id: Optional[uuid.UUID] = None,
    categories: Optional[List[str]] = None,
    min_severity: Optional[str] = None
) -> List[tuple]:
    """
    Find findings similar to the given embedding vector.
    
    Args:
        db: Database session
        query_embedding: Vector embedding to search against
        limit: Maximum number of results to return
        exclude_id: Optional finding ID to exclude
        categories: Optional list of categories to filter by
        min_severity: Optional minimum severity level ('low', 'medium', 'high', 'critical')
    
    Returns:
        List of tuples containing (Finding, distance_score)
    """
    from sqlalchemy import bindparam, cast
    from sqlalchemy.types import ARRAY, Float, UserDefinedType
    
    # Define VECTOR type for casting
    class VECTOR(UserDefinedType):
        cache_ok = True  # Safe to cache, dimensions are immutable
        
        def __init__(self, dim=1536):
            self.dim = dim
        
        def get_col_spec(self, **kw):
            return f"VECTOR({self.dim})"
    
    # Convert query_embedding to list if it's a numpy array
    if hasattr(query_embedding, 'tolist'):
        query_embedding = query_embedding.tolist()
    
    severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    
    # Cast to VECTOR(1536)
    qv = cast(bindparam("qv", value=query_embedding, type_=ARRAY(Float)), VECTOR(1536))
    distance = cast(Finding.embedding.op("<->")(qv), Float).label('distance')
    
    query = (
        select(Finding, distance)
        .where(Finding.embedding.isnot(None))
    )
    
    if exclude_id:
        query = query.where(Finding.id != exclude_id)
    
    # Filter out false positives
    query = query.where(Finding.status != "false_positive")
    
    # Filter by categories if specified
    if categories:
        query = query.where(Finding.category.in_(categories))
    
    # Filter by severity if specified
    if min_severity:
        min_level = severity_levels.get(min_severity, 2)
        valid_severities = [k for k, v in severity_levels.items() if v >= min_level]
        query = query.where(Finding.severity.in_(valid_severities))
    
    query = query.order_by(distance).limit(limit)
    
    # Execute query (embedding already in bindparam)
    results = db.execute(query).all()
    return [(row.Finding, row.distance) for row in results]


def generate_report_embedding(db: Session, report: Report) -> bool:
    """
    Generate and save embedding for a report.
    
    Args:
        db: Database session
        report: Report object to generate embedding for
    
    Returns:
        True if embedding was generated successfully, False otherwise
    """
    try:
        from embedding_service import get_embedding_service
        
        embed_svc = get_embedding_service()
        embedding = embed_svc.embed_report(report)
        
        report.embedding = embedding
        db.commit()
        db.refresh(report)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to generate embedding for report {report.id}: {e}")
        db.rollback()
        return False


def generate_finding_embedding(db: Session, finding: Finding) -> bool:
    """
    Generate and save embedding for a finding.
    
    Args:
        db: Database session
        finding: Finding object to generate embedding for
    
    Returns:
        True if embedding was generated successfully, False otherwise
    """
    try:
        from embedding_service import get_embedding_service
        
        embed_svc = get_embedding_service()
        embedding = embed_svc.embed_finding(finding)
        
        finding.embedding = embedding
        db.commit()
        db.refresh(finding)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to generate embedding for finding {finding.id}: {e}")
        db.rollback()
        return False

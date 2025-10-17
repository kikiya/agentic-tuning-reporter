"""
API routes for reports (synchronous version)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database_sync import get_db
from schemas import (
    ReportResponse, ReportCreate, ReportUpdate, ReportDetail,
    FindingResponse, FindingCreate, FindingUpdate, FindingWithActions,
    RecommendedActionResponse, RecommendedActionCreate, RecommendedActionUpdate,
    CommentResponse, CommentCreate, ReportStatusHistoryResponse,
)
from services_sync import (
    get_reports, get_reports_by_cluster, get_report_by_id, create_report, update_report, delete_report,
    get_findings_by_report, create_finding, update_finding, delete_finding,
    get_actions_by_finding, create_action, update_action,
    get_comments_by_report, create_comment,
    get_report_status_history
)

router = APIRouter()

# Reports endpoints
@router.get("/reports", response_model=List[ReportResponse])
def list_reports(
    skip: int = 0,
    limit: int = 100,
    cluster_id: str = None,
    db: Session = Depends(get_db)
):
    """Get all reports with optional filtering"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    if cluster_id:
        reports = get_reports_by_cluster(db, cluster_id)
        return reports[skip:skip + limit]
    return get_reports(db, skip=skip, limit=limit)

@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: UUID, db: Session = Depends(get_db)):
    """Get a specific report with all related data"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Load related data
    findings = get_findings_by_report(db, report_id)
    comments = get_comments_by_report(db, report_id)
    status_history = get_report_status_history(db, report_id)

    # Build findings with actions
    findings_with_actions: List[FindingWithActions] = []
    for f in findings:
        actions = get_actions_by_finding(db, f.id)
        f_schema = FindingResponse.model_validate(f)
        actions_schema = [RecommendedActionResponse.model_validate(a) for a in actions]
        findings_with_actions.append(
            FindingWithActions(**f_schema.model_dump(), actions=actions_schema)
        )

    return ReportDetail(
        **ReportResponse.model_validate(report).model_dump(),
        findings=findings_with_actions,
        comments=[CommentResponse.model_validate(c) for c in comments],
        status_history=[ReportStatusHistoryResponse.model_validate(s) for s in status_history],
    )

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_new_report(
    report_data: ReportCreate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Create a new report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    report = create_report(db, report_data, current_user)
    return ReportResponse.model_validate(report)

@router.put("/reports/{report_id}", response_model=ReportResponse)
def update_existing_report(
    report_id: UUID,
    report_update: ReportUpdate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Update an existing report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    report = update_report(db, report_id, report_update, current_user)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse.model_validate(report)

@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_report(report_id: UUID, db: Session = Depends(get_db)):
    """Delete a report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    success = delete_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")

# Findings endpoints
@router.get("/reports/{report_id}/findings", response_model=List[FindingResponse])
def list_findings(report_id: UUID, db: Session = Depends(get_db)):
    """Get all findings for a report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    findings = get_findings_by_report(db, report_id)
    return [FindingResponse.model_validate(f) for f in findings]

@router.post("/reports/{report_id}/findings", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
def create_finding_for_report(
    report_id: UUID,
    finding_data: FindingCreate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Create a new finding for a report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    finding = create_finding(db, finding_data, report_id, current_user)
    return FindingResponse.model_validate(finding)

@router.put("/findings/{finding_id}", response_model=FindingResponse)
def update_finding_details(
    finding_id: UUID,
    finding_update: FindingUpdate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Update a finding"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    finding = update_finding(db, finding_id, finding_update, current_user)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)

@router.delete("/findings/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finding_record(finding_id: UUID, db: Session = Depends(get_db)):
    """Delete a finding"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    success = delete_finding(db, finding_id)
    if not success:
        raise HTTPException(status_code=404, detail="Finding not found")

# Actions endpoints
@router.get("/findings/{finding_id}/actions", response_model=List[RecommendedActionResponse])
def list_actions(finding_id: UUID, db: Session = Depends(get_db)):
    """Get all actions for a finding"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    actions = get_actions_by_finding(db, finding_id)
    return [RecommendedActionResponse.model_validate(a) for a in actions]

@router.post("/findings/{finding_id}/actions", response_model=RecommendedActionResponse, status_code=status.HTTP_201_CREATED)
def create_action_for_finding(
    finding_id: UUID,
    action_data: RecommendedActionCreate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Create a new action for a finding"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    action = create_action(db, action_data, finding_id, current_user)
    return RecommendedActionResponse.model_validate(action)

@router.put("/actions/{action_id}", response_model=RecommendedActionResponse)
def update_action_details(
    action_id: UUID,
    action_update: RecommendedActionUpdate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Update an action"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    action = update_action(db, action_id, action_update, current_user)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return RecommendedActionResponse.model_validate(action)

# Comments endpoints
@router.get("/reports/{report_id}/comments", response_model=List[CommentResponse])
def list_comments(report_id: UUID, db: Session = Depends(get_db)):
    """Get all comments for a report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    comments = get_comments_by_report(db, report_id)
    return [CommentResponse.model_validate(c) for c in comments]

@router.post("/reports/{report_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment_for_report(
    report_id: UUID,
    comment_data: CommentCreate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Create a new comment for a report"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    comment = create_comment(db, comment_data, report_id, current_user)
    return CommentResponse.model_validate(comment)

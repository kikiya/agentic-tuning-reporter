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
    get_reports, get_reports_for_user, get_reports_by_cluster, get_report_by_id, create_report, update_report, delete_report,
    get_findings_by_report, create_finding, update_finding, delete_finding,
    get_actions_by_finding, create_action, update_action,
    get_comments_by_report, create_comment,
    get_report_status_history,
    search_similar_reports
)

router = APIRouter()

# Reports endpoints
@router.get("/reports", response_model=List[ReportResponse])
def list_reports(
    skip: int = 0,
    limit: int = 100,
    cluster_id: str = None,
    user_id: str | None = None,
    enforce_access: bool = True,
    db: Session = Depends(get_db)
):
    """Get reports with optional filtering and access control"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    if cluster_id:
        reports = get_reports_by_cluster(db, cluster_id)
        return reports[skip:skip + limit]
    if user_id and enforce_access:
        return get_reports_for_user(db, user_id, skip=skip, limit=limit)
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

# Similarity search endpoints
@router.get("/reports/{report_id}/similar")
def find_similar_reports(
    report_id: UUID,
    limit: int = 5,
    user_id: str = "analyst_alice",  # Default for demo - in production, get from auth token
    enforce_access: bool = True,
    db: Session = Depends(get_db)
):
    """
    Find reports similar to the specified report using vector similarity search.
    Returns reports with similar content, problems, and characteristics.
    
    Access control:
    - If enforce_access=True, only returns reports the user has access to via customer mappings
    - If enforce_access=False, returns all matching reports (admin mode)
    
    Demo users:
    - analyst_alice: Can see Acme Corp reports only
    - analyst_bob: Can see Globex Industries reports only  
    - admin_charlie: Can see all reports
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    print(f"[SIMILARITY SEARCH] Request from user_id={user_id} for report_id={report_id}, limit={limit}, enforce_access={enforce_access}")
    
    # Get the source report
    report = get_report_by_id(db, report_id)
    if not report:
        print(f"[SIMILARITY SEARCH ERROR] Report {report_id} not found")
        raise HTTPException(status_code=404, detail="Report not found")
    
    print(f"[SIMILARITY SEARCH] Found report: '{report.title}', has_embedding={report.embedding is not None}")
    
    if report.embedding is None:
        print(f"[SIMILARITY SEARCH ERROR] Report {report_id} has no embedding - needs regeneration")
        raise HTTPException(
            status_code=400, 
            detail=f"Report '{report.title}' doesn't have an embedding yet. Create a new report or edit this one to generate embeddings."
        )
    
    # Search for similar reports with access control
    try:
        similar_reports = search_similar_reports(
            db=db,
            query_embedding=report.embedding,
            limit=limit,
            exclude_id=report_id,
            user_id=user_id,
            enforce_access=enforce_access
        )
        
        # Format response
        results = []
        for similar_report, distance in similar_reports:
            # Convert distance to similarity score (0-1, where 1 is most similar)
            # Lower distance = more similar, so we invert it
            similarity_score = max(0.0, 1.0 - (distance / 2.0))  # Normalize distance
            
            results.append({
                "id": str(similar_report.id),
                "title": similar_report.title,
                "cluster_id": similar_report.cluster_id,
                "status": similar_report.status,
                "created_at": similar_report.created_at.isoformat() if similar_report.created_at else None,
                "created_by": similar_report.created_by,
                "similarity_score": round(similarity_score, 4),
                "distance": round(distance, 4)
            })
        
        print(f"[SIMILARITY SEARCH SUCCESS] Found {len(results)} similar reports for user {user_id}")
        
        return {
            "source_report_id": str(report_id),
            "source_report_title": report.title,
            "count": len(results),
            "viewing_as": user_id,
            "access_control_enabled": enforce_access,
            "similar_reports": results
        }
    except Exception as e:
        print(f"[SIMILARITY SEARCH ERROR] Search failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Similarity search failed: {str(e)}"
        )

"""
Finding management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas import FindingResponse, FindingUpdate, FindingSeverityEnum, FindingStatusEnum
from app.models import User, Finding, Scan

router = APIRouter()


@router.get("", response_model=List[FindingResponse])
async def list_findings(
    scan_id: Optional[int] = Query(None),
    severity: Optional[FindingSeverityEnum] = Query(None),
    status: Optional[FindingStatusEnum] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List findings with optional filters
    """
    query = db.query(Finding)
    
    # Filter by scan
    if scan_id:
        query = query.filter(Finding.scan_id == scan_id)
    
    # Filter by severity
    if severity:
        query = query.filter(Finding.severity == severity)
    
    # Filter by status
    if status:
        query = query.filter(Finding.status == status)
    
    # Filter by ownership for non-admin users
    if not current_user.is_superuser:
        query = query.join(Scan).join(Scan.target).filter(
            Scan.target.has(owner_id=current_user.id)
        )
    
    # Order by severity (critical first) and priority rank
    severity_order = {
        FindingSeverityEnum.CRITICAL: 5,
        FindingSeverityEnum.HIGH: 4,
        FindingSeverityEnum.MEDIUM: 3,
        FindingSeverityEnum.LOW: 2,
        FindingSeverityEnum.INFO: 1,
    }
    
    findings = query.offset(skip).limit(limit).all()
    
    # Sort by severity and AI priority
    findings.sort(
        key=lambda f: (
            -severity_order.get(f.severity, 0),
            f.ai_priority_rank or 999
        )
    )
    
    return findings


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get finding details by ID"""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID {finding_id} not found"
        )
    
    # Check access
    if not current_user.is_superuser:
        if finding.scan.target.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this finding"
            )
    
    return finding


@router.put("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: int,
    finding_data: FindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update finding (e.g., change status, severity, add notes)"""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID {finding_id} not found"
        )
    
    # Check access
    if not current_user.is_superuser:
        if finding.scan.target.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this finding"
            )
    
    # Update fields
    update_data = finding_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(finding, field, value)
    
    from datetime import datetime
    finding.updated_at = datetime.utcnow()
    if finding_data.status and finding_data.status != FindingStatusEnum.OPEN:
        finding.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(finding)
    
    return finding


@router.get("/stats/summary")
async def get_findings_summary(
    scan_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get summary statistics for findings
    """
    from sqlalchemy import func
    
    query = db.query(
        Finding.severity,
        Finding.status,
        func.count(Finding.id).label("count")
    )
    
    # Filter by scan if provided
    if scan_id:
        query = query.filter(Finding.scan_id == scan_id)
    
    # Filter by ownership for non-admin users
    if not current_user.is_superuser:
        query = query.join(Scan).join(Scan.target).filter(
            Scan.target.has(owner_id=current_user.id)
        )
    
    query = query.group_by(Finding.severity, Finding.status)
    
    results = query.all()
    
    # Format results
    summary = {
        "by_severity": {},
        "by_status": {},
        "total": 0
    }
    
    for severity, status, count in results:
        # By severity
        if severity.value not in summary["by_severity"]:
            summary["by_severity"][severity.value] = 0
        summary["by_severity"][severity.value] += count
        
        # By status
        if status.value not in summary["by_status"]:
            summary["by_status"][status.value] = 0
        summary["by_status"][status.value] += count
        
        summary["total"] += count
    
    return summary

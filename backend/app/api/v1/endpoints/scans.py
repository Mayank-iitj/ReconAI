"""
Scan management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.exceptions import ScanNotFoundError, TargetNotFoundError, ConcurrentScanLimitError
from app.core.config import settings
from app.schemas import ScanCreate, ScanScheduleCreate, ScanResponse
from app.models import User, Scan, Target, ScanStatus
from app.worker.tasks import run_scan_task

router = APIRouter()


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create and start a new scan
    
    Scan will be executed asynchronously by Celery workers
    """
    # Verify target exists and user has access
    target = db.query(Target).filter(Target.id == scan_data.target_id).first()
    if not target:
        raise TargetNotFoundError(scan_data.target_id)
    
    # Check ownership
    if not current_user.is_superuser and target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to scan this target"
        )
    
    # Check authorization
    if not target.authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target is not authorized for testing"
        )
    
    # Check concurrent scan limit
    running_scans = db.query(Scan).filter(
        Scan.target_id == scan_data.target_id,
        Scan.status == ScanStatus.RUNNING
    ).count()
    
    if running_scans >= settings.MAX_CONCURRENT_SCANS:
        raise ConcurrentScanLimitError(running_scans, settings.MAX_CONCURRENT_SCANS)
    
    # Create scan
    scan = Scan(
        **scan_data.dict(),
        created_by=current_user.id,
        status=ScanStatus.PENDING
    )
    
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Queue scan task
    background_tasks.add_task(run_scan_task.delay, scan.id)
    
    return scan


@router.post("/schedule", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def schedule_scan(
    scan_data: ScanScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Schedule a recurring scan with cron expression
    
    Example: "0 0 * * *" for daily at midnight
    """
    # Verify target exists and user has access
    target = db.query(Target).filter(Target.id == scan_data.target_id).first()
    if not target:
        raise TargetNotFoundError(scan_data.target_id)
    
    # Check ownership
    if not current_user.is_superuser and target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to scan this target"
        )
    
    # Validate cron expression
    from croniter import croniter
    if not croniter.is_valid(scan_data.cron_schedule):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cron expression"
        )
    
    # Create scheduled scan
    scan = Scan(
        **scan_data.dict(),
        created_by=current_user.id,
        status=ScanStatus.PENDING,
        is_scheduled=True
    )
    
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # TODO: Register with Celery beat scheduler
    
    return scan


@router.get("", response_model=List[ScanResponse])
async def list_scans(
    target_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List scans with optional filters
    """
    query = db.query(Scan)
    
    # Filter by target
    if target_id:
        query = query.filter(Scan.target_id == target_id)
    
    # Filter by status
    if status:
        query = query.filter(Scan.status == status)
    
    # Filter by ownership for non-admin users
    if not current_user.is_superuser:
        query = query.join(Target).filter(Target.owner_id == current_user.id)
    
    # Order by most recent first
    query = query.order_by(Scan.created_at.desc())
    
    scans = query.offset(skip).limit(limit).all()
    return scans


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get scan details by ID"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise ScanNotFoundError(scan_id)
    
    # Check access
    if not current_user.is_superuser and scan.target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this scan"
        )
    
    return scan


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a running scan"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise ScanNotFoundError(scan_id)
    
    # Check access
    if not current_user.is_superuser and scan.target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this scan"
        )
    
    # Can only cancel pending or running scans
    if scan.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel scan in {scan.status.value} status"
        )
    
    # Update status
    scan.status = ScanStatus.CANCELLED
    db.commit()
    db.refresh(scan)
    
    # TODO: Signal Celery task to stop
    
    return scan


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete scan and all associated findings"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise ScanNotFoundError(scan_id)
    
    # Check access
    if not current_user.is_superuser and scan.target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this scan"
        )
    
    db.delete(scan)
    db.commit()
    
    return None

"""
Report generation endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.exceptions import ScanNotFoundError
from app.schemas import ReportCreate, ReportResponse
from app.models import User, Scan, Report
from app.services.report_engine import ReportEngine

router = APIRouter()
report_engine = ReportEngine()


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a report for a scan
    
    Supports multiple formats: markdown, html, pdf, json
    """
    # Verify scan exists and user has access
    scan = db.query(Scan).filter(Scan.id == report_data.scan_id).first()
    if not scan:
        raise ScanNotFoundError(report_data.scan_id)
    
    # Check access
    if not current_user.is_superuser and scan.target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate report for this scan"
        )
    
    # Create report record
    report = Report(
        **report_data.dict(),
        generated_by=current_user.id,
        generated_by_llm=True  # Will be updated by report engine
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Generate report asynchronously
    background_tasks.add_task(
        report_engine.generate_report,
        report_id=report.id,
        scan_id=scan.id,
        db=db
    )
    
    return report


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    scan_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all reports"""
    query = db.query(Report)
    
    # Filter by scan
    if scan_id:
        query = query.filter(Report.scan_id == scan_id)
    
    # Filter by ownership for non-admin users
    if not current_user.is_superuser:
        query = query.join(Scan).join(Scan.target).filter(
            Scan.target.has(owner_id=current_user.id)
        )
    
    reports = query.order_by(Report.created_at.desc()).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get report details"""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    
    # Check access
    if not current_user.is_superuser:
        if report.scan.target.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download report file"""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    
    # Check access
    if not current_user.is_superuser:
        if report.scan.target.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this report"
            )
    
    # Check if file exists
    if report.format in ["markdown", "json"]:
        # Return content directly
        from fastapi.responses import Response
        media_type = "text/markdown" if report.format == "markdown" else "application/json"
        return Response(
            content=report.content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=report-{report_id}.{report.format}"
            }
        )
    elif report.format in ["html", "pdf"]:
        # Return file
        if not report.file_path or not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found"
            )
        
        media_type = "text/html" if report.format == "html" else "application/pdf"
        return FileResponse(
            path=report.file_path,
            media_type=media_type,
            filename=f"report-{report_id}.{report.format}"
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported report format: {report.format}"
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete report"""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    
    # Check access
    if not current_user.is_superuser:
        if report.scan.target.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this report"
            )
    
    # Delete file if exists
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)
    
    db.delete(report)
    db.commit()
    
    return None

"""
Target management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_active_user, check_permission
from app.core.exceptions import TargetNotFoundError, AuthorizationError
from app.schemas import TargetCreate, TargetUpdate, TargetResponse, PaginatedResponse
from app.models import User, Target
from app.services.scope_validator import ScopeValidator

router = APIRouter()
scope_validator = ScopeValidator()


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new target for recon scanning
    
    Requires explicit authorization confirmation
    """
    # Check authorization
    if not target_data.authorized:
        raise AuthorizationError(
            message="You must explicitly confirm authorization to test this target"
        )
    
    # Validate scope
    validation_result = scope_validator.validate_target(target_data.dict())
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scope validation failed: {', '.join(validation_result['errors'])}"
        )
    
    # Create target
    target = Target(
        **target_data.dict(),
        owner_id=current_user.id
    )
    
    db.add(target)
    db.commit()
    db.refresh(target)
    
    return target


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all targets
    
    Regular users see only their own targets
    Admins see all targets
    """
    query = db.query(Target)
    
    # Filter by owner for non-admin users
    if not current_user.is_superuser:
        query = query.filter(Target.owner_id == current_user.id)
    
    targets = query.offset(skip).limit(limit).all()
    return targets


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get target by ID"""
    target = db.query(Target).filter(Target.id == target_id).first()
    
    if not target:
        raise TargetNotFoundError(target_id)
    
    # Check ownership
    if not current_user.is_superuser and target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this target"
        )
    
    return target


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update target configuration"""
    target = db.query(Target).filter(Target.id == target_id).first()
    
    if not target:
        raise TargetNotFoundError(target_id)
    
    # Check ownership
    if not current_user.is_superuser and target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this target"
        )
    
    # Update fields
    update_data = target_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target, field, value)
    
    db.commit()
    db.refresh(target)
    
    return target


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete target and all associated scans/findings"""
    target = db.query(Target).filter(Target.id == target_id).first()
    
    if not target:
        raise TargetNotFoundError(target_id)
    
    # Check ownership
    if not current_user.is_superuser and target.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this target"
        )
    
    db.delete(target)
    db.commit()
    
    return None

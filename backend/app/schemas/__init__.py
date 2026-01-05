"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class ScanStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanTypeEnum(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    CUSTOM = "custom"


class FindingSeverityEnum(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatusEnum(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"
    DUPLICATE = "duplicate"
    WONT_FIX = "wont_fix"
    FIXED = "fixed"


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Target schemas
class TargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    root_domains: List[str] = Field(default_factory=list)
    in_scope: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    ip_ranges: List[str] = Field(default_factory=list)
    rate_limit: int = Field(default=10, ge=1, le=100)
    max_concurrency: int = Field(default=5, ge=1, le=50)
    tags: List[str] = Field(default_factory=list)
    program_name: Optional[str] = None
    program_url: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)


class TargetCreate(TargetBase):
    authorized: bool = Field(..., description="Explicit confirmation of authorization to test this target")
    authorization_proof: Optional[str] = Field(
        None,
        description="Documentation or proof of authorization (e.g., program URL, email confirmation)"
    )


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    in_scope: Optional[List[str]] = None
    out_of_scope: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    max_concurrency: Optional[int] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = None


class TargetResponse(TargetBase):
    id: int
    authorized: bool
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Scan schemas
class ScanBase(BaseModel):
    name: Optional[str] = None
    scan_type: ScanTypeEnum = ScanTypeEnum.STANDARD
    enable_subdomain_discovery: bool = True
    enable_port_scan: bool = False
    enable_fuzzing: bool = True
    enable_nuclei: bool = True
    enable_takeover_check: bool = True
    tool_config: Dict[str, Any] = Field(default_factory=dict)


class ScanCreate(ScanBase):
    target_id: int


class ScanScheduleCreate(ScanBase):
    target_id: int
    cron_schedule: str = Field(..., description="Cron expression (e.g., '0 0 * * *' for daily at midnight)")


class ScanResponse(ScanBase):
    id: int
    target_id: int
    status: ScanStatusEnum
    created_by: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    info_findings: int = 0
    error_message: Optional[str] = None
    is_scheduled: bool = False
    cron_schedule: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Finding schemas
class FindingBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str
    severity: FindingSeverityEnum
    status: FindingStatusEnum = FindingStatusEnum.OPEN
    vuln_type: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[str] = None
    cvss_vector: Optional[str] = None
    affected_url: Optional[str] = None
    http_request: Optional[str] = None
    http_response: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    poc: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


class FindingCreate(FindingBase):
    scan_id: int
    asset_id: Optional[int] = None
    tool_name: Optional[str] = None
    tool_output: Optional[Dict[str, Any]] = None


class FindingUpdate(BaseModel):
    status: Optional[FindingStatusEnum] = None
    severity: Optional[FindingSeverityEnum] = None
    description: Optional[str] = None
    poc: Optional[str] = None
    tags: Optional[List[str]] = None


class FindingResponse(FindingBase):
    id: int
    scan_id: int
    asset_id: Optional[int] = None
    tool_name: Optional[str] = None
    ai_priority_rank: Optional[int] = None
    likelihood_score: Optional[int] = None
    suggested_steps: List[str] = Field(default_factory=list)
    discovered_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Asset schemas
class AssetBase(BaseModel):
    asset_type: str = Field(..., description="Type of asset: subdomain, ip, url, endpoint")
    value: str = Field(..., max_length=2048)
    http_status: Optional[int] = None
    http_title: Optional[str] = None
    http_server: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    dns_records: Dict[str, Any] = Field(default_factory=dict)
    is_alive: bool = False
    tags: List[str] = Field(default_factory=list)


class AssetResponse(AssetBase):
    id: int
    target_id: int
    confidence_score: int
    discovered_by: Optional[str] = None
    last_checked: Optional[datetime] = None
    discovered_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Report schemas
class ReportCreate(BaseModel):
    scan_id: int
    title: str = Field(..., max_length=255)
    report_type: str = Field(default="bug_bounty", description="Report type: bug_bounty, internal, executive")
    format: str = Field(default="markdown", description="Export format: markdown, html, pdf, json")
    include_sections: List[str] = Field(
        default_factory=lambda: ["executive_summary", "assets", "findings", "remediation"],
        description="Sections to include in report"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters for findings (e.g., {'severity': ['high', 'critical'], 'status': ['open']})"
    )


class ReportResponse(BaseModel):
    id: int
    scan_id: int
    title: str
    report_type: str
    format: str
    file_path: Optional[str] = None
    generated_by_llm: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Pagination
class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[Any]


# Health check
class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    checks: Optional[Dict[str, str]] = None

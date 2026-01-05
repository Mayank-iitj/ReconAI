"""
Database models for SmartRecon-AI
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
    Index,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


# Enums
class ScanStatus(str, enum.Enum):
    """Scan status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, enum.Enum):
    """Scan type enum"""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    CUSTOM = "custom"


class FindingSeverity(str, enum.Enum):
    """Finding severity enum"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, enum.Enum):
    """Finding status enum"""
    OPEN = "open"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"
    DUPLICATE = "duplicate"
    WONT_FIX = "wont_fix"
    FIXED = "fixed"


# Models
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")
    
    targets = relationship("Target", back_populates="owner", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="created_by_user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    permissions = Column(JSON, default=list)  # List of permission strings
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Role {self.name}>"


class Target(Base):
    """Target model for scan targets"""
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Scope definition
    root_domains = Column(JSON, default=list)  # List of root domains
    in_scope = Column(JSON, default=list)  # List of in-scope patterns
    out_of_scope = Column(JSON, default=list)  # List of out-of-scope patterns
    ip_ranges = Column(JSON, default=list)  # List of IP/CIDR ranges
    
    # Authorization & compliance
    authorized = Column(Boolean, default=False, nullable=False)
    authorization_proof = Column(Text)  # Documentation/proof of authorization
    
    # Configuration
    rate_limit = Column(Integer, default=10)  # Requests per second
    max_concurrency = Column(Integer, default=5)
    tags = Column(JSON, default=list)  # List of tags (e.g., ["bugbounty", "high-priority"])
    
    # Metadata
    program_name = Column(String(255))
    program_url = Column(String(255))
    priority = Column(Integer, default=1)  # 1-5, 5 being highest
    
    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="targets")
    
    scans = relationship("Scan", back_populates="target", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="target", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_targets_owner_name', 'owner_id', 'name'),
    )
    
    def __repr__(self):
        return f"<Target {self.name}>"


class Scan(Base):
    """Scan model for recon scans"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    
    # Scan configuration
    scan_type = Column(SQLEnum(ScanType), default=ScanType.STANDARD, nullable=False)
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False, index=True)
    
    # Options
    enable_subdomain_discovery = Column(Boolean, default=True)
    enable_port_scan = Column(Boolean, default=False)
    enable_fuzzing = Column(Boolean, default=True)
    enable_nuclei = Column(Boolean, default=True)
    enable_takeover_check = Column(Boolean, default=True)
    
    # Tool configuration
    tool_config = Column(JSON, default=dict)  # Custom tool configurations
    
    # Execution metadata
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Results
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    info_findings = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    cron_schedule = Column(String(100))  # Cron expression for scheduled scans
    
    # Relationships
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    target = relationship("Target", back_populates="scans")
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User", back_populates="scans")
    
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    tool_runs = relationship("ToolRun", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_scans_target_status', 'target_id', 'status'),
        Index('ix_scans_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Scan {self.id} - {self.status.value}>"


class Asset(Base):
    """Asset model for discovered assets (subdomains, IPs, URLs)"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Asset identification
    asset_type = Column(String(50), nullable=False)  # subdomain, ip, url, endpoint
    value = Column(String(2048), nullable=False, index=True)  # The actual asset value
    
    # HTTP metadata (for web assets)
    http_status = Column(Integer)
    http_title = Column(String(500))
    http_server = Column(String(255))
    tech_stack = Column(JSON, default=list)  # List of detected technologies
    
    # DNS metadata
    dns_records = Column(JSON, default=dict)  # A, AAAA, CNAME, etc.
    
    # Status
    is_alive = Column(Boolean, default=False)
    last_checked = Column(DateTime(timezone=True))
    
    # Metadata
    confidence_score = Column(Integer, default=100)  # 0-100
    discovered_by = Column(String(100))  # Tool that discovered it
    tags = Column(JSON, default=list)
    
    # Relationships
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    target = relationship("Target", back_populates="assets")
    
    findings = relationship("Finding", back_populates="asset")
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_assets_target_type_value', 'target_id', 'asset_type', 'value'),
        UniqueConstraint('target_id', 'asset_type', 'value', name='uix_target_asset'),
    )
    
    def __repr__(self):
        return f"<Asset {self.asset_type}: {self.value}>"


class Finding(Base):
    """Finding model for vulnerabilities and issues"""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Finding details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(FindingSeverity), nullable=False, index=True)
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.OPEN, nullable=False, index=True)
    
    # Classification
    vuln_type = Column(String(100))  # e.g., "XSS", "SQLi", "IDOR", "Open Redirect"
    cwe_id = Column(String(20))  # CWE identifier
    cvss_score = Column(String(10))  # CVSS score
    cvss_vector = Column(String(200))  # CVSS vector string
    
    # Evidence
    affected_url = Column(String(2048))
    http_request = Column(Text)  # Raw HTTP request
    http_response = Column(Text)  # Raw HTTP response
    evidence = Column(JSON, default=dict)  # Additional evidence data
    poc = Column(Text)  # Proof of concept
    
    # Source
    tool_name = Column(String(100))  # Tool that found it (e.g., "nuclei", "ffuf")
    tool_output = Column(JSON)  # Raw tool output
    
    # AI analysis
    ai_analysis = Column(JSON)  # LLM-generated analysis
    ai_priority_rank = Column(Integer)  # LLM-assigned priority (1-N)
    likelihood_score = Column(Integer)  # 0-100, likelihood of being valid bug
    suggested_steps = Column(JSON, default=list)  # Suggested manual verification steps
    
    # Metadata
    tags = Column(JSON, default=list)
    references = Column(JSON, default=list)  # List of reference URLs
    
    # Relationships
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    scan = relationship("Scan", back_populates="findings")
    
    asset_id = Column(Integer, ForeignKey("assets.id"), index=True)
    asset = relationship("Asset", back_populates="findings")
    
    comments = relationship("Comment", back_populates="finding", cascade="all, delete-orphan")
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_findings_scan_severity', 'scan_id', 'severity'),
        Index('ix_findings_status_severity', 'status', 'severity'),
    )
    
    def __repr__(self):
        return f"<Finding {self.id} - {self.title}>"


class ToolRun(Base):
    """ToolRun model to track individual tool executions"""
    __tablename__ = "tool_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Tool information
    tool_name = Column(String(100), nullable=False, index=True)
    tool_version = Column(String(50))
    command = Column(Text)  # Actual command executed
    
    # Execution
    status = Column(String(50), nullable=False)  # success, failed, timeout, cancelled
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Results
    output = Column(Text)  # Tool stdout
    error_output = Column(Text)  # Tool stderr
    exit_code = Column(Integer)
    results_count = Column(Integer, default=0)  # Number of results found
    
    # Relationships
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    scan = relationship("Scan", back_populates="tool_runs")
    
    __table_args__ = (
        Index('ix_tool_runs_scan_tool', 'scan_id', 'tool_name'),
    )
    
    def __repr__(self):
        return f"<ToolRun {self.tool_name} - {self.status}>"


class Report(Base):
    """Report model for generated reports"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Report metadata
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # bug_bounty, internal, executive
    format = Column(String(20), nullable=False)  # markdown, html, pdf, json
    
    # Content
    content = Column(Text)  # Report content (Markdown or HTML)
    file_path = Column(String(500))  # Path to generated file (for PDF)
    
    # Configuration
    include_sections = Column(JSON, default=list)  # Sections to include
    filters = Column(JSON, default=dict)  # Filters applied (severity, status, etc.)
    
    # Metadata
    generated_by_llm = Column(Boolean, default=False)
    
    # Relationships
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    scan = relationship("Scan", back_populates="reports")
    
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Report {self.id} - {self.title}>"


class Comment(Base):
    """Comment model for finding discussions"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Relationships
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False, index=True)
    finding = relationship("Finding", back_populates="comments")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="comments")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Comment {self.id}>"

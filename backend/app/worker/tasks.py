"""
Celery tasks for scan orchestration
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.worker import celery_app
from app.core.database import SessionLocal
from app.models import Scan, Target, Finding, Asset, ToolRun, ScanStatus, FindingSeverity
from app.services.tools.subfinder import SubfinderWrapper
from app.services.tools.httpx_tool import HTTPXWrapper
from app.services.tools.nuclei import NucleiWrapper
from app.services.scope_validator import ScopeValidator
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="smartrecon.run_scan")
def run_scan_task(self, scan_id: int):
    """
    Main task to orchestrate a complete recon scan
    
    Args:
        scan_id: ID of the scan to execute
    """
    db = SessionLocal()
    
    try:
        # Get scan
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return
        
        # Update status
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Starting scan {scan_id} for target {scan.target.name}")
        
        # Get target and scope
        target = scan.target
        scope_validator = ScopeValidator()
        
        # Step 1: Subdomain Discovery
        if scan.enable_subdomain_discovery:
            logger.info(f"Scan {scan_id}: Starting subdomain discovery")
            subdomains = discover_subdomains(scan, target, db)
            logger.info(f"Scan {scan_id}: Discovered {len(subdomains)} subdomains")
        else:
            # Use root domains only
            subdomains = [{"subdomain": d} for d in target.root_domains]
        
        # Step 2: HTTP Probing
        logger.info(f"Scan {scan_id}: Starting HTTP probing")
        alive_hosts = probe_http(scan, subdomains, target, db)
        logger.info(f"Scan {scan_id}: Found {len(alive_hosts)} alive hosts")
        
        # Step 3: Vulnerability Scanning
        if scan.enable_nuclei and alive_hosts:
            logger.info(f"Scan {scan_id}: Starting vulnerability scanning")
            findings = scan_vulnerabilities(scan, alive_hosts, target, db)
            logger.info(f"Scan {scan_id}: Found {len(findings)} potential vulnerabilities")
            
            # Step 4: AI Analysis
            logger.info(f"Scan {scan_id}: Running AI analysis")
            analyze_findings_with_llm(scan, findings, target, db)
        
        # Update scan status
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())
        
        # Update finding counts
        update_finding_counts(scan, db)
        
        db.commit()
        
        logger.info(f"Scan {scan_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}", exc_info=True)
        
        # Update scan status
        scan.status = ScanStatus.FAILED
        scan.error_message = str(e)
        scan.completed_at = datetime.utcnow()
        if scan.started_at:
            scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())
        db.commit()
        
    finally:
        db.close()


def discover_subdomains(scan: Scan, target: Target, db: Session) -> List[Dict[str, Any]]:
    """Run subdomain discovery tools"""
    all_subdomains = []
    scope_validator = ScopeValidator()
    
    # Run Subfinder
    try:
        tool_start = datetime.utcnow()
        subfinder = SubfinderWrapper()
        
        for root_domain in target.root_domains:
            result = subfinder.execute(domain=root_domain)
            
            # Record tool run
            tool_run = ToolRun(
                scan_id=scan.id,
                tool_name="subfinder",
                status="success" if result["success"] else "failed",
                started_at=tool_start,
                completed_at=datetime.utcnow(),
                duration_seconds=result["duration"],
                output=result["raw_output"],
                error_output=result.get("error"),
                exit_code=result["exit_code"],
                results_count=len(result["results"])
            )
            db.add(tool_run)
            
            # Collect results
            for subdomain_data in result["results"]:
                subdomain = subdomain_data["subdomain"]
                
                # Validate scope
                if not scope_validator.is_in_scope(subdomain, target.__dict__):
                    logger.info(f"Skipping out-of-scope subdomain: {subdomain}")
                    continue
                
                # Create asset
                asset = Asset(
                    target_id=target.id,
                    asset_type="subdomain",
                    value=subdomain,
                    discovered_by="subfinder",
                    discovered_at=datetime.utcnow()
                )
                db.add(asset)
                
                all_subdomains.append(subdomain_data)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Subfinder failed: {e}")
    
    return all_subdomains


def probe_http(scan: Scan, subdomains: List[Dict[str, Any]], target: Target, db: Session) -> List[str]:
    """Probe subdomains for HTTP services"""
    alive_hosts = []
    
    try:
        tool_start = datetime.utcnow()
        httpx = HTTPXWrapper()
        
        # Extract subdomain values
        subdomain_list = [s.get("subdomain", s.get("value", "")) for s in subdomains]
        
        result = httpx.execute(targets=subdomain_list)
        
        # Record tool run
        tool_run = ToolRun(
            scan_id=scan.id,
            tool_name="httpx",
            status="success" if result["success"] else "failed",
            started_at=tool_start,
            completed_at=datetime.utcnow(),
            duration_seconds=result["duration"],
            output=result["raw_output"],
            error_output=result.get("error"),
            exit_code=result["exit_code"],
            results_count=len(result["results"])
        )
        db.add(tool_run)
        
        # Process results
        for http_data in result["results"]:
            url = http_data["url"]
            
            # Update or create asset
            asset = db.query(Asset).filter(
                Asset.target_id == target.id,
                Asset.value == http_data["host"]
            ).first()
            
            if asset:
                asset.is_alive = True
                asset.http_status = http_data.get("status_code")
                asset.http_title = http_data.get("title")
                asset.http_server = http_data.get("server")
                asset.tech_stack = http_data.get("technologies", [])
                asset.last_checked = datetime.utcnow()
            else:
                asset = Asset(
                    target_id=target.id,
                    asset_type="url",
                    value=url,
                    is_alive=True,
                    http_status=http_data.get("status_code"),
                    http_title=http_data.get("title"),
                    http_server=http_data.get("server"),
                    tech_stack=http_data.get("technologies", []),
                    discovered_by="httpx",
                    discovered_at=datetime.utcnow()
                )
                db.add(asset)
            
            alive_hosts.append(url)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"HTTPX failed: {e}")
    
    return alive_hosts


def scan_vulnerabilities(scan: Scan, targets: List[str], target: Target, db: Session) -> List[Finding]:
    """Run Nuclei vulnerability scanning"""
    findings = []
    
    try:
        tool_start = datetime.utcnow()
        nuclei = NucleiWrapper()
        
        result = nuclei.execute(
            targets=targets,
            severity=["critical", "high", "medium"]
        )
        
        # Record tool run
        tool_run = ToolRun(
            scan_id=scan.id,
            tool_name="nuclei",
            status="success" if result["success"] else "failed",
            started_at=tool_start,
            completed_at=datetime.utcnow(),
            duration_seconds=result["duration"],
            output=result["raw_output"][:10000],  # Limit size
            error_output=result.get("error"),
            exit_code=result["exit_code"],
            results_count=len(result["results"])
        )
        db.add(tool_run)
        
        # Create findings
        for vuln_data in result["results"]:
            # Map severity
            severity_map = {
                "critical": FindingSeverity.CRITICAL,
                "high": FindingSeverity.HIGH,
                "medium": FindingSeverity.MEDIUM,
                "low": FindingSeverity.LOW,
                "info": FindingSeverity.INFO
            }
            severity = severity_map.get(vuln_data["severity"].lower(), FindingSeverity.INFO)
            
            # Create finding
            finding = Finding(
                scan_id=scan.id,
                title=vuln_data["template_name"],
                description=vuln_data.get("description", ""),
                severity=severity,
                vuln_type=vuln_data["type"],
                cwe_id=vuln_data.get("cwe_id"),
                cvss_score=vuln_data.get("cvss_score"),
                affected_url=vuln_data["matched_at"],
                tool_name="nuclei",
                tool_output=vuln_data,
                evidence={"template_id": vuln_data["template_id"]},
                discovered_at=datetime.utcnow()
            )
            db.add(finding)
            findings.append(finding)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Nuclei failed: {e}")
    
    return findings


def analyze_findings_with_llm(scan: Scan, findings: List[Finding], target: Target, db: Session):
    """Analyze findings with LLM for prioritization"""
    import asyncio
    
    try:
        llm_service = LLMService()
        
        # Prepare findings data
        findings_data = [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "url": f.affected_url,
                "description": f.description,
                "tool": f.tool_name
            }
            for f in findings
        ]
        
        target_info = {
            "name": target.name,
            "domains": target.root_domains,
            "priority": target.priority
        }
        
        # Run LLM analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        prioritized = loop.run_until_complete(
            llm_service.prioritize_findings(findings_data, target_info)
        )
        loop.close()
        
        # Update findings with AI analysis
        for analysis in prioritized:
            finding_id = analysis.get("original_finding_id")
            finding = db.query(Finding).filter(Finding.id == finding_id).first()
            
            if finding:
                finding.ai_priority_rank = analysis.get("priority_rank")
                finding.likelihood_score = analysis.get("likelihood_of_valid_bug")
                finding.suggested_steps = analysis.get("suggested_manual_steps", [])
                finding.ai_analysis = analysis
        
        db.commit()
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")


def update_finding_counts(scan: Scan, db: Session):
    """Update finding counts on scan"""
    from sqlalchemy import func
    
    counts = db.query(
        Finding.severity,
        func.count(Finding.id)
    ).filter(Finding.scan_id == scan.id).group_by(Finding.severity).all()
    
    scan.total_findings = sum(count for _, count in counts)
    
    for severity, count in counts:
        if severity == FindingSeverity.CRITICAL:
            scan.critical_findings = count
        elif severity == FindingSeverity.HIGH:
            scan.high_findings = count
        elif severity == FindingSeverity.MEDIUM:
            scan.medium_findings = count
        elif severity == FindingSeverity.LOW:
            scan.low_findings = count
        elif severity == FindingSeverity.INFO:
            scan.info_findings = count

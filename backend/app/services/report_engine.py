"""
Report generation engine
Generates professional bug bounty reports in multiple formats
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import os
import markdown
from jinja2 import Template

from app.core.config import settings
from app.models import Report, Scan, Finding, FindingSeverity
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ReportEngine:
    """Generate professional security reports"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_report(self, report_id: int, scan_id: int, db):
        """
        Generate a report for a scan
        
        Args:
            report_id: Report record ID
            scan_id: Scan ID
            db: Database session
        """
        try:
            # Get report and scan
            report = db.query(Report).filter(Report.id == report_id).first()
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            
            if not report or not scan:
                logger.error(f"Report {report_id} or Scan {scan_id} not found")
                return
            
            # Get findings
            findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()
            
            # Apply filters
            findings = self._apply_filters(findings, report.filters)
            
            # Generate report content based on format
            if report.format == "markdown":
                content = await self._generate_markdown_report(scan, findings, report)
                report.content = content
            
            elif report.format == "html":
                markdown_content = await self._generate_markdown_report(scan, findings, report)
                html_content = markdown.markdown(markdown_content, extensions=["tables", "fenced_code"])
                report.content = html_content
                
                # Save to file
                file_path = os.path.join(
                    settings.REPORTS_DIR,
                    f"report-{report_id}.html"
                )
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(self._wrap_html(html_content, scan.target.name))
                report.file_path = file_path
            
            elif report.format == "json":
                import json
                content = self._generate_json_report(scan, findings)
                report.content = json.dumps(content, indent=2)
            
            db.commit()
            logger.info(f"Report {report_id} generated successfully")
            
        except Exception as e:
            logger.error(f"Failed to generate report {report_id}: {e}", exc_info=True)
    
    def _apply_filters(self, findings: List[Finding], filters: Dict[str, Any]) -> List[Finding]:
        """Apply filters to findings"""
        filtered = findings
        
        # Filter by severity
        if "severity" in filters:
            severity_filter = [FindingSeverity(s) for s in filters["severity"]]
            filtered = [f for f in filtered if f.severity in severity_filter]
        
        # Filter by status
        if "status" in filters:
            status_filter = filters["status"]
            filtered = [f for f in filtered if f.status.value in status_filter]
        
        return filtered
    
    async def _generate_markdown_report(
        self,
        scan: Scan,
        findings: List[Finding],
        report: Report
    ) -> str:
        """Generate Markdown report"""
        sections = []
        
        # Title
        sections.append(f"# Security Assessment Report: {scan.target.name}")
        sections.append(f"\n**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        sections.append("---\n")
        
        # Executive Summary (if requested)
        if "executive_summary" in report.include_sections:
            scan_data = {
                "target": scan.target.name,
                "scan_type": scan.scan_type.value,
                "duration": scan.duration_seconds,
                "date": scan.completed_at.isoformat() if scan.completed_at else None
            }
            
            findings_list = [
                {
                    "severity": f.severity.value,
                    "title": f.title
                }
                for f in findings
            ]
            
            summary = await self.llm_service.generate_report_summary(scan_data, findings_list)
            sections.append("## Executive Summary\n")
            sections.append(summary)
            sections.append("\n")
        
        # Scope
        if "scope" in report.include_sections:
            sections.append("## Scope\n")
            sections.append(f"**Root Domains:** {', '.join(scan.target.root_domains)}\n")
            sections.append(f"**In Scope:** {', '.join(scan.target.in_scope)}\n")
            if scan.target.out_of_scope:
                sections.append(f"**Out of Scope:** {', '.join(scan.target.out_of_scope)}\n")
            sections.append("\n")
        
        # Methodology
        if "methodology" in report.include_sections:
            sections.append("## Methodology\n")
            sections.append("### Tools Used\n")
            sections.append("- **Subfinder**: Subdomain enumeration\n")
            sections.append("- **HTTPX**: HTTP probing and technology detection\n")
            if scan.enable_nuclei:
                sections.append("- **Nuclei**: Vulnerability scanning\n")
            sections.append("\n")
        
        # Findings Summary
        if "findings" in report.include_sections:
            sections.append("## Findings Summary\n")
            
            severity_counts = {}
            for f in findings:
                severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1
            
            sections.append("| Severity | Count |\n")
            sections.append("|----------|-------|\n")
            for severity in ["critical", "high", "medium", "low", "info"]:
                count = severity_counts.get(severity, 0)
                sections.append(f"| {severity.upper()} | {count} |\n")
            sections.append("\n")
            
            # Detailed findings
            sections.append("## Detailed Findings\n")
            
            # Sort by severity and priority
            severity_order = {
                FindingSeverity.CRITICAL: 5,
                FindingSeverity.HIGH: 4,
                FindingSeverity.MEDIUM: 3,
                FindingSeverity.LOW: 2,
                FindingSeverity.INFO: 1
            }
            sorted_findings = sorted(
                findings,
                key=lambda f: (-severity_order[f.severity], f.ai_priority_rank or 999)
            )
            
            for i, finding in enumerate(sorted_findings[:50], 1):  # Limit to top 50
                sections.append(f"### {i}. {finding.title}\n")
                sections.append(f"**Severity:** {finding.severity.value.upper()}\n")
                sections.append(f"**Affected URL:** {finding.affected_url}\n")
                if finding.cwe_id:
                    sections.append(f"**CWE:** {finding.cwe_id}\n")
                if finding.cvss_score:
                    sections.append(f"**CVSS Score:** {finding.cvss_score}\n")
                sections.append(f"\n**Description:**\n{finding.description}\n")
                
                if finding.poc:
                    sections.append(f"\n**Proof of Concept:**\n```\n{finding.poc}\n```\n")
                
                if finding.suggested_steps:
                    sections.append("\n**Suggested Verification Steps:**\n")
                    for step in finding.suggested_steps:
                        sections.append(f"- {step}\n")
                
                sections.append("\n---\n")
        
        # Remediation
        if "remediation" in report.include_sections:
            sections.append("## Remediation Recommendations\n")
            sections.append("1. Prioritize findings marked as CRITICAL and HIGH severity\n")
            sections.append("2. Validate all findings through manual testing\n")
            sections.append("3. Apply security patches and configuration updates\n")
            sections.append("4. Implement security best practices\n")
            sections.append("5. Consider a follow-up assessment after remediation\n")
            sections.append("\n")
        
        # Footer
        sections.append("---\n")
        sections.append("*Generated by SmartRecon-AI - FOR AUTHORIZED TESTING ONLY*\n")
        
        return "\n".join(sections)
    
    def _generate_json_report(self, scan: Scan, findings: List[Finding]) -> Dict[str, Any]:
        """Generate JSON report"""
        return {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "scan_id": scan.id,
                "target": scan.target.name
            },
            "scan_info": {
                "type": scan.scan_type.value,
                "started_at": scan.started_at.isoformat() if scan.started_at else None,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "duration_seconds": scan.duration_seconds
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "status": f.status.value,
                    "affected_url": f.affected_url,
                    "description": f.description,
                    "cwe_id": f.cwe_id,
                    "cvss_score": f.cvss_score,
                    "poc": f.poc,
                    "ai_priority_rank": f.ai_priority_rank,
                    "likelihood_score": f.likelihood_score
                }
                for f in findings
            ]
        }
    
    def _wrap_html(self, content: str, title: str) -> str:
        """Wrap HTML content with proper document structure"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title} - Security Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
        .high {{ color: #f57c00; font-weight: bold; }}
        .medium {{ color: #fbc02d; font-weight: bold; }}
        .low {{ color: #388e3c; }}
    </style>
</head>
<body>
{content}
</body>
</html>"""

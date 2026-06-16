"""
BATCH REPORT EXPORTER: AGGREGATED METRICS SUMMARY (BE-Y11)
==========================================================

Role: Compiles multi-site batch audit results into a unified CSV schema.
Provides clean structured data for business stakeholders and machine learning inferences.
"""

import csv
import os
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlmodel import select # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from auditor.infrastructure.persistence_models import TargetModel, AuditSessionModel, ViolationModel
from auditor.shared.paths import EXPORTS_DIR
from auditor.shared.logging import auditor_logger

class BatchReportExporter:
    """
    Service to compile and generate aggregated CSV exports for all audited targets.
    """
    
    def __init__(self, db_engine: Any):
        self.engine = db_engine
        self.logger = auditor_logger.getChild("BatchExporter")

    async def generate_aggregated_csv(self) -> Optional[str]:
        """
        Queries all audit targets, retrieves their latest completed session,
        aggregates metrics, and writes them into a unified CSV.
        
        Returns the absolute filepath of the generated CSV file.
        """
        self.logger.info("Starting aggregated CSV report compilation...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filepath = os.path.join(EXPORTS_DIR, f"batch_export_summary_{timestamp}.csv")
        
        try:
            async with AsyncSession(self.engine) as session:
                # 1. Fetch all targets
                targets_res = await session.exec(select(TargetModel))
                targets = targets_res.all()
                
                if not targets:
                    self.logger.warning("No targets found in database. Exporting empty CSV template.")
                    self._write_empty_template(export_filepath)
                    return export_filepath
                
                rows = []
                for target in targets:
                    # 2. Find the latest completed master session for this target
                    session_query = (
                        select(AuditSessionModel)
                        .where(AuditSessionModel.target_url == target.url)
                        .where(AuditSessionModel.status == "completed")
                        .order_by(AuditSessionModel.completed_at.desc())
                        .limit(1)
                        .options(selectinload(AuditSessionModel.violations))
                    )
                    session_res = await session.exec(session_query)
                    latest_session = session_res.first()
                    
                    if not latest_session:
                        # Target has never been scanned or finished
                        rows.append(self._build_empty_row(target.url, target.status))
                        continue
                    
                    # 3. Aggregate violation metrics
                    row_data = self._aggregate_session_data(target.url, latest_session)
                    rows.append(row_data)
                
                # 4. Write CSV
                self._write_csv_file(export_filepath, rows)
                self.logger.info(f"Aggregated CSV report compiled successfully at: {export_filepath}")
                return export_filepath
                
        except Exception as e:
            self.logger.exception(f"Aggregated CSV compilation failed: {e}")
            return None

    def _aggregate_session_data(self, target_url: str, session: AuditSessionModel) -> Dict[str, Any]:
        """
        Analyzes and aggregates all violation metrics inside a completed audit session.
        """
        violations = session.violations or []
        
        # Unique pages affected (based on unique url strings in violations)
        unique_pages = {v.url for v in violations if v.url}
        
        critical_count = 0
        serious_count = 0
        moderate_count = 0
        minor_count = 0
        
        wcag_20_count = 0
        wcag_21_count = 0
        section_508_count = 0
        
        rule_frequency = {}
        rule_descriptions = {}
        
        for v in violations:
            # Impact counting
            impact_lower = (v.impact or "").lower()
            if "critical" in impact_lower:
                critical_count += 1
            elif "serious" in impact_lower:
                serious_count += 1
            elif "moderate" in impact_lower:
                moderate_count += 1
            elif "minor" in impact_lower:
                minor_count += 1
                
            # Rule frequency
            rule_id = v.rule_id
            rule_frequency[rule_id] = rule_frequency.get(rule_id, 0) + 1
            if v.description:
                rule_descriptions[rule_id] = v.description
                
            # WCAG / Standards counting
            tags = v.tags or []
            is_wcag20 = False
            is_wcag21 = False
            is_508 = False
            for tag in tags:
                tag_lower = tag.lower()
                if "wcag2a" in tag_lower or "wcag2aa" in tag_lower:
                    is_wcag20 = True
                if "wcag21" in tag_lower:
                    is_wcag21 = True
                if "section508" in tag_lower or "508" in tag_lower:
                    is_508 = True
                    
            if is_wcag20: wcag_20_count += 1
            if is_wcag21: wcag_21_count += 1
            if is_508: section_508_count += 1
            
        # Identify top violating rule
        top_rule_id = "N/A"
        top_rule_desc = "N/A"
        if rule_frequency:
            top_rule_id = max(rule_frequency, key=rule_frequency.get)
            top_rule_desc = rule_descriptions.get(top_rule_id, "N/A")
            
        completed_at_str = session.completed_at.isoformat() if session.completed_at else "N/A"
        
        return {
            "Target URL": target_url,
            "Scan Status": "COMPLETED",
            "Audit Completed At": completed_at_str,
            "Total Pages Crawled": len(unique_pages) or 1, # fallback to 1 if empty
            "Total Violations Count": len(violations),
            "Critical Violations": critical_count,
            "Serious Violations": serious_count,
            "Moderate Violations": moderate_count,
            "Minor Violations": minor_count,
            "Top Violating Rule ID": top_rule_id,
            "Top Violating Rule Description": top_rule_desc,
            "WCAG 2.0 Violations": wcag_20_count,
            "WCAG 2.1 Violations": wcag_21_count,
            "Section 508 Violations": section_508_count,
            "Remediation Complexity Score": (critical_count * 5) + (serious_count * 3) + (moderate_count * 1.5) + (minor_count * 0.5)
        }

    def _build_empty_row(self, target_url: str, status: str) -> Dict[str, Any]:
        """
        Creates a fallback empty row dictionary for non-completed targets.
        """
        return {
            "Target URL": target_url,
            "Scan Status": status.upper(),
            "Audit Completed At": "N/A",
            "Total Pages Crawled": 0,
            "Total Violations Count": 0,
            "Critical Violations": 0,
            "Serious Violations": 0,
            "Moderate Violations": 0,
            "Minor Violations": 0,
            "Top Violating Rule ID": "N/A",
            "Top Violating Rule Description": "N/A",
            "WCAG 2.0 Violations": 0,
            "WCAG 2.1 Violations": 0,
            "Section 508 Violations": 0,
            "Remediation Complexity Score": 0.0
        }

    def _write_csv_file(self, filepath: str, rows: List[Dict[str, Any]]):
        """
        Helper method to write records using standard python CSV writer.
        """
        headers = [
            "Target URL", "Scan Status", "Audit Completed At", "Total Pages Crawled", 
            "Total Violations Count", "Critical Violations", "Serious Violations", 
            "Moderate Violations", "Minor Violations", "Top Violating Rule ID", 
            "Top Violating Rule Description", "WCAG 2.0 Violations", "WCAG 2.1 Violations", 
            "Section 508 Violations", "Remediation Complexity Score"
        ]
        
        # Write with UTF-8 BOM to support direct Excel opening
        with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def _write_empty_template(self, filepath: str):
        """
        Writes a header-only CSV file if no targets exist.
        """
        self._write_csv_file(filepath, [])

    async def generate_detailed_violations_csv(self) -> Optional[str]:
        """
        Compiles a highly detailed CSV of all individual violations across
        all sites, including exact selectors, rule descriptions, and violating HTML snippets.
        """
        self.logger.info("Starting detailed violations CSV compilation...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filepath = os.path.join(EXPORTS_DIR, f"batch_violations_detail_{timestamp}.csv")
        
        try:
            async with AsyncSession(self.engine) as session:
                # 1. Fetch all targets
                targets_res = await session.exec(select(TargetModel))
                targets = targets_res.all()
                
                rows = []
                for target in targets:
                    # Find latest completed master session for this target
                    session_query = (
                        select(AuditSessionModel)
                        .where(AuditSessionModel.target_url == target.url)
                        .where(AuditSessionModel.status == "completed")
                        .order_by(AuditSessionModel.completed_at.desc())
                        .limit(1)
                        .options(selectinload(AuditSessionModel.violations))
                    )
                    session_res = await session.exec(session_query)
                    latest_session = session_res.first()
                    
                    if not latest_session:
                        continue
                        
                    for v in (latest_session.violations or []):
                        # Extract the violating HTML snippets from nodes
                        html_snippets = []
                        if v.nodes:
                            for node in v.nodes:
                                if isinstance(node, dict) and node.get("html"):
                                    html_snippets.append(node["html"])
                        
                        joined_html = " | ".join(html_snippets[:5]) # Join first 5 nodes
                        
                        rows.append({
                            "Target Site URL": target.url,
                            "Page URL": v.url or "N/A",
                            "Rule ID": v.rule_id,
                            "Impact": v.impact,
                            "Description": v.description,
                            "Selector": v.selector or "N/A",
                            "Violating HTML Snippet": joined_html or "N/A",
                            "WCAG Tags": ", ".join(v.tags or []),
                            "Help URL": v.help_url or "N/A"
                        })
                
                # Write CSV
                headers = [
                    "Target Site URL", "Page URL", "Rule ID", "Impact", "Description", 
                    "Selector", "Violating HTML Snippet", "WCAG Tags", "Help URL"
                ]
                with open(export_filepath, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows)
                    
                self.logger.info(f"Detailed violations CSV compiled successfully at: {export_filepath}")
                return export_filepath
                
        except Exception as e:
            self.logger.exception(f"Detailed violations CSV compilation failed: {e}")
            return None

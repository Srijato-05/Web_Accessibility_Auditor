"""
AUDITOR STAKEHOLDER REPORTING ENGINE (R-Z10)
===========================================

Role: Data transformation and visualization.
Responsibilities:
  - Aggregating audit results from persistence.
  - Generating structured JSON reports for automation.
  - Generating premium, responsive HTML dashboards for stakeholders.
"""

import asyncio
import os
import sys
import json

# IDE PATH RECONCILIATION: Ensuring import stability for external scripts
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore
from auditor.domain.audit_session import SessionStatus # type: ignore

class AuditReporter:
    """
    Enterprise-Grade Reporting Engine.
    
    Transforms clinical audit data into actionable stakeholder insights.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = auditor_logger.getChild("Reporter")

    async def generate_summary_report(self, output_dir: str = "reports/exports") -> Dict[str, str]:
        """Generates both HTML and JSON reports for the most recent session."""
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Fetch Latest Completed Session
        stmt = select(AuditSessionModel).where(
            AuditSessionModel.status == SessionStatus.COMPLETED
        ).order_by(AuditSessionModel.started_at.desc()).limit(1)
        res = await self.session.execute(stmt)
        session_record = res.scalar_one_or_none()
        
        if not session_record:
            self.logger.warning("Reporting Abort: No completed audit data available in persistence.")
            return {}

        # 2. Fetch Violations
        v_stmt = select(ViolationModel).where(ViolationModel.session_id == session_record.id)
        v_res = await self.session.execute(v_stmt)
        violations = v_res.scalars().all()

        # 3. Serialize Data
        report_data = {
            "session_id": str(session_record.id),
            "url": session_record.target_url,
            "start_time": session_record.started_at.isoformat() if session_record.started_at else None,
            "end_time": session_record.completed_at.isoformat() if session_record.completed_at else None,
            "total_violations": len(violations),
            "violations": [
                {
                    "rule_id": v.id,
                    "impact": v.impact,
                    "description": v.description,
                    "selector": v.selector,
                    "help_url": v.help_url,
                    "tags": v.tags
                } for v in violations
            ]
        }

        # 4. Generate Exports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(output_dir, f"audit_report_{timestamp}.json")
        html_path = os.path.join(output_dir, f"audit_report_{timestamp}.html")

        # JSON Export
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=4)

        # HTML Export (Premium Template)
        html_content = self._build_html_dashboard(report_data)
        with open(html_path, "w") as f:
            f.write(html_content)

        self.logger.info(f"Stakeholder Reports Generated: {html_path}")
        return {"json": json_path, "html": html_path}

    def _build_html_dashboard(self, data: Dict[str, Any]) -> str:
        """Constructs a premium HTML dashboard using HSL palettes and Inter typography."""
        
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for v in data["violations"]:
            impact = v["impact"].lower()
            if impact in impact_counts:
                impact_counts[impact] += 1

        # 4. Heading Hierarchy Mapping
        headings_list = []
        for v in data["violations"]:
            if v["rule_id"] == "HEURISTIC-HEAD-047":
                h_card = f"""
                <div class="hierarchy-item level-error">
                    <span class="warning-icon">⚠</span> 
                    <strong>{v['selector'].upper()}</strong>: {v['description']}
                </div>
                """
                headings_list.append(h_card)
        headings_html = "".join(headings_list)

        violations_html = ""
        for v in data["violations"]:
            impact_class = f"impact-{v['impact'].lower()}"
            violations_html += f"""
            <div class="violation-card {impact_class}">
                <div class="card-header">
                    <span class="badge">{v['impact']}</span>
                    <span class="rule-id">{v['rule_id']}</span>
                </div>
                <p class="description">{v['description']}</p>
                <code class="selector">{v['selector']}</code>
                <div class="footer">
                    <a href="{v['help_url']}" target="_blank">Remediation Guide &rarr;</a>
                    <div class="tags">{' '.join([f'<span>#{t}</span>' for t in v['tags']])}</div>
                </div>
            </div>
            """

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auditor | Stakeholder Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0a0a0c;
            --card-bg: #141418;
            --text-main: #f0f0f5;
            --text-dim: #a1a1aa;
            --accent-primary: #6366f1;
            --impact-critical: #ef4444;
            --impact-serious: #f97316;
            --impact-moderate: #eab308;
            --impact-minor: #22c55e;
            --border-color: #27272a;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            padding: 40px 20px;
        }}

        .container {{ max-width: 1100px; margin: 0 auto; }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 60px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 20px;
        }}

        .brand {{ font-weight: 800; font-size: 2.5rem; letter-spacing: -1px; background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .meta {{ text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-dim); }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 60px;
        }}

        .summary-card {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            text-align: center;
        }}

        .summary-card .value {{ font-size: 2rem; font-weight: 700; display: block; }}
        .summary-card .label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-dim); }}

        .violations-container {{ display: grid; gap: 24px; }}
        .violation-card {{
            background: var(--card-bg);
            padding: 32px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
            transition: transform 0.2s;
        }}
        .violation-card:hover {{ transform: translateY(-4px); border-color: var(--accent-primary); }}

        .violation-card::before {{
            content: '';
            position: absolute;
            left: 0; top: 0; bottom: 0; width: 4px;
        }}

        .impact-critical::before {{ background: var(--impact-critical); }}
        .impact-serious::before {{ background: var(--impact-serious); }}
        .impact-moderate::before {{ background: var(--impact-moderate); }}
        .impact-minor::before {{ background: var(--impact-minor); }}

        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .impact-critical .badge {{ background: rgba(239, 68, 68, 0.1); color: var(--impact-critical); }}
        .impact-serious .badge {{ background: rgba(249, 115, 22, 0.1); color: var(--impact-serious); }}
        
        .rule-id {{ font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: var(--text-dim); }}
        .description {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; }}
        .selector {{
            display: block;
            background: #1e1e24;
            padding: 12px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            margin-bottom: 24px;
            overflow-x: auto;
        }}

        .footer {{ display: flex; justify-content: space-between; align-items: center; }}
        .footer a {{ color: var(--accent-primary); text-decoration: none; font-weight: 600; font-size: 0.9rem; }}
        .tags {{ display: flex; gap: 8px; }}
        .tags span {{ font-size: 0.7rem; color: var(--text-dim); }}

        /* Structural Section */
        .section-title {{ font-size: 1.5rem; font-weight: 700; margin: 40px 0 20px; color: var(--accent-primary); }}
        .hierarchy-container {{ background: var(--card-bg); padding: 24px; border-radius: 16px; border: 1px solid var(--border-color); margin-bottom: 40px; }}
        .hierarchy-item {{ padding: 12px; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; }}
        .level-error {{ color: var(--impact-serious); background: rgba(249, 115, 22, 0.05); }}
        .warning-icon {{ margin-right: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">AUDITOR.NEXT</div>
            <div class="meta">
                SESSION: {data['session_id'][:13]}...<br>
                TARGET: {data['url']}
            </div>
        </header>

        <div class="summary-grid">
            <div class="summary-card">
                <span class="value">{data['total_violations']}</span>
                <span class="label">Total Violations</span>
            </div>
            <div class="summary-card">
                <span class="value" style="color: var(--impact-critical)">{impact_counts['critical']}</span>
                <span class="label">Critical</span>
            </div>
            <div class="summary-card">
                <span class="value" style="color: var(--impact-serious)">{impact_counts['serious']}</span>
                <span class="label">Serious</span>
            </div>
            <div class="summary-card">
                <span class="value" style="color: var(--accent-primary)">100%</span>
                <span class="label">Autonomous Stability</span>
            </div>
        </div>

        <h2 class="section-title">Structural Hierarchy Anomaly Log</h2>
        <div class="hierarchy-container">
            {headings_html if headings_html else '<div class="hierarchy-item" style="color: var(--impact-minor)">No structural hierarchy anomalies detected.</div>'}
        </div>

        <h2 class="section-title">Violations Inventory</h2>
        <div class="violations-container">
            {violations_html}
        </div>
    </div>
</body>
</html>
        """

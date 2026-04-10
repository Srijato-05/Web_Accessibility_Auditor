"""
AUDITOR STAKEHOLDER REPORTING ENGINE (R-Z10)
===========================================

Role: Data transformation and visualization.
Responsibilities:
  - Aggregating audit results from persistence.
  - Generating structured JSON reports for automation.
  - Generating premium, responsive HTML dashboards for stakeholders.
"""

import os
import sys
import json

from auditor.shared.paths import EXPORTS_DIR

from datetime import datetime
from typing import Dict, Any
from sqlmodel import select, desc # type: ignore
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

    async def generate_summary_report(self, session_id: Any = None, output_dir: str = None) -> Dict[str, str]:
        """Generates both HTML and JSON reports for a specific session (or latest if None)."""
        if output_dir is None:
            output_dir = str(EXPORTS_DIR)
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Fetch Targeted Session
        if session_id:
            from uuid import UUID
            if isinstance(session_id, str):
                session_id = UUID(session_id)
            stmt = select(AuditSessionModel).where(AuditSessionModel.id == session_id)
        else:
            stmt = select(AuditSessionModel).where(
                AuditSessionModel.status == SessionStatus.COMPLETED
            ).order_by(desc(AuditSessionModel.started_at)).limit(1)

        res = await self.session.exec(stmt)
        session_record = res.first()
        
        if not session_record:
            self.logger.warning(f"Reporting Abort: Session {session_id} not found or no completed audits.")
            return {}

        # 2. Fetch Violations
        v_stmt = select(ViolationModel).where(ViolationModel.session_id == session_record.id)
        v_res = await self.session.exec(v_stmt)
        violations = v_res.all()

        # 3. Serialize Data
        report_data = {
            "session_id": str(session_record.id),
            "url": session_record.target_url,
            "start_time": session_record.started_at.isoformat() if session_record.started_at else None,
            "end_time": session_record.completed_at.isoformat() if session_record.completed_at else None,
            "total_violations": len(violations),
            "focus_path": getattr(session_record, 'focus_path', []),
            "aria_events": getattr(session_record, 'aria_events', []),
            "violations": [
                {
                    "rule_id": getattr(v, "rule_id", "UNKNOWN"),
                    "uuid": str(getattr(v, "id", "")),
                    "impact": getattr(v, "impact", "minor"),
                    "description": getattr(v, "description", ""),
                    "selector": getattr(v, "selector", ""),
                    "help_url": getattr(v, "help_url", ""),
                    "tags": getattr(v, "tags", []),
                    "agent": getattr(v, "agent", "axe"),
                    "compliance_level": getattr(v, "compliance_level", "N/A"),
                    "category": getattr(v, "category", "General"),
                    "severity_matrix": getattr(v, "severity_matrix", "Moderate"),
                    "url": getattr(v, "url", "")
                } for v in violations
            ]
        }

        # 3b. Compute Forensic Matrix (Agents vs Principles)
        # ... (matrix logic remains same, but I'll ensure I don't break it)
        matrix = {
            "axe": {"Perceivable": 0, "Operable": 0, "Understandable": 0, "Robust": 0, "General": 0},
            "visual": {"Perceivable": 0, "Operable": 0, "Understandable": 0, "Robust": 0, "General": 0},
            "motor": {"Perceivable": 0, "Operable": 0, "Understandable": 0, "Robust": 0, "General": 0},
            "cognitive": {"Perceivable": 0, "Operable": 0, "Understandable": 0, "Robust": 0, "General": 0},
            "neural": {"Perceivable": 0, "Operable": 0, "Understandable": 0, "Robust": 0, "General": 0}
        }
        for v_entry in report_data["violations"]:
            if not isinstance(v_entry, dict):
                continue
            agent = str(v_entry.get("agent", "axe")).lower()
            category = str(v_entry.get("category", "General"))
            if agent in matrix:
                if category in matrix[agent]:
                    matrix[agent][category] += 1
                else:
                    matrix[agent]["General"] += 1
        
        report_data["matrix"] = matrix
        report_data["target_url"] = session_record.target_url # For PDF parity
        report_data["url"] = session_record.target_url # For HTML parity

        # 4. Generate Exports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_id = str(session_record.id)[:8] # type: ignore
        json_path = os.path.join(output_dir, f"audit_report_{safe_id}_{timestamp}.json")
        html_path = os.path.join(output_dir, f"audit_report_{safe_id}_{timestamp}.html")
        pdf_path = os.path.join(output_dir, f"audit_report_{safe_id}_{timestamp}.pdf")

        # JSON Export
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=4)

        # HTML Export (Premium Template)
        html_content = self._build_html_dashboard(report_data)
        with open(html_path, "w") as f:
            f.write(html_content)

        # PDF Export (Same Design Principle)
        try:
            from auditor.infrastructure.pdf_reporter import convert_json_to_pdf
            convert_json_to_pdf(json_path, pdf_path)
            self.logger.info(f"PDF Stakeholder Report Generated: {pdf_path}")
        except Exception as e:
            self.logger.error(f"PDF Generation Failed: {e}")
            pdf_path = None

        self.logger.info(f"Stakeholder Reports Generated: {html_path}")
        return {"json": json_path, "html": html_path, "pdf": str(pdf_path) if pdf_path else ""}

    def _build_html_dashboard(self, data: Dict[str, Any]) -> str:
        """Constructs a premium HTML dashboard using HSL palettes and Inter typography."""
        
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for v in data["violations"]:
            impact = (v.get("impact") or "minor").lower()
            if impact in impact_counts:
                impact_counts[impact] += 1

        # 4. Heading Hierarchy Mapping
        headings_html = "".join([f"""
            <div class="hierarchy-item level-error">
                <span class="warning-icon">⚠</span> 
                <strong>{v['selector'].upper()}</strong>: {v['description']}
            </div>
            """ for v in data["violations"] if v["rule_id"] == "HEURISTIC-HEAD-047"])

        # 5. Focus Path SVG Reconstruction (Phase VII/X)
        focus_svg = ""
        if data.get("focus_path"):
            path_points = []
            for i, p in enumerate(data["focus_path"]):
                p_x, p_y = p.get('x', 0), p.get('y', 0) 
                path_points.append(f"{p_x},{p_y}")
                focus_svg += f'<circle cx="{p_x}" cy="{p_y}" r="8" fill="var(--accent-primary)" />'
                if i > 0:
                    prev_x, prev_y = data["focus_path"][i-1].get('x', 0), data["focus_path"][i-1].get('y', 0)
                    focus_svg += f'<line x1="{prev_x}" y1="{prev_y}" x2="{p_x}" y2="{p_y}" stroke="var(--accent-primary)" stroke-width="2" opacity="0.4" />'
        else:
            focus_svg = '<text x="50%" y="50%" text-anchor="middle" fill="var(--text-dim)" font-family="Inter">No navigation telemetry recorded.</text>'
            
        # 6. ARIA-Live Event Log (Phase VII)
        aria_html = "".join([f"""
            <div class="aria-event">
                <span class="timestamp">+{e.get('timestamp', 0) % 10000}ms</span>
                <span class="type">{e.get('type')}</span>
                <span class="content">"{e.get('content')}"</span>
                <span class="target">@ {e.get('selector')}</span>
            </div>
            """ for e in data.get("aria_events", [])])

        violations_html = ""
        for v in data["violations"]:
            impact_raw = v.get("impact") or "minor"
            impact_class = f"impact-{impact_raw.lower()}"
            violations_html += f"""
            <div class="violation-card {impact_class}">
                <div class="card-header">
                    <span class="badge {(v.get('compliance_level') or 'Non-Standard').lower().replace(' ', '-')}">{v.get('severity_matrix') or 'Unclassified'}</span>
                    <span class="compliance-badge">{v.get('compliance_level') or 'N/A'}</span>
                    <span class="agent-badge">{(v.get('agent') or 'axe').upper()}</span>
                    <span class="rule-id">{v.get('rule_id')}</span>
                </div>
                <div class="category-tag">{v['category']}</div>
                <p class="description">{v['description']}</p>
                <code class="selector">{v['selector']}</code>
                <div class="footer">
                    <a href="{v['help_url']}" target="_blank">Remediation Guide &rarr;</a>
                    <div class="tags">{' '.join([f'<span>#{t}</span>' for t in v['tags']])}</div>
                </div>
            </div>
            """

        # 7. Forensic Matrix HTML
        matrix_html = """
        <div class="matrix-container">
            <h3>Forensic Diagnostic Matrix (Agents vs WCAG Principles)</h3>
            <div class="matrix-grid">
                <div class="matrix-header">Agent / Principle</div>
                <div class="matrix-header">Perceivable</div>
                <div class="matrix-header">Operable</div>
                <div class="matrix-header">Understandable</div>
                <div class="matrix-header">Robust</div>
        """
        for agent, principles in data["matrix"].items():
            matrix_html += f'<div class="matrix-row-label">{agent.upper()}</div>'
            for principle in ["Perceivable", "Operable", "Understandable", "Robust"]:
                count = principles.get(principle, 0)
                cell_class = "cell-empty" if count == 0 else "cell-active"
                matrix_html += f'<div class="matrix-cell {cell_class}">{count}</div>'
        
        matrix_html += "</div></div>"

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

        .compliance-badge {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--accent-primary);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 8px;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }}

        .agent-badge {{
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 8px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge.below-a {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid #ef4444;
        }}

        /* Matrix Visualization */
        .matrix-container {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 40px;
            border: 1px solid var(--border-color);
        }}
        .matrix-container h3 {{ margin-top: 0; margin-bottom: 20px; font-size: 1.1rem; color: var(--text-primary); }}
        .matrix-grid {{
            display: grid;
            grid-template-columns: 150px repeat(4, 1fr);
            gap: 12px;
            text-align: center;
        }}
        .matrix-header {{ font-weight: 700; color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }}
        .matrix-row-label {{ font-weight: 600; text-align: left; align-self: center; color: var(--text-primary); }}
        .matrix-cell {{
            padding: 12px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 1.1rem;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .cell-active {{ color: var(--accent-primary); background: rgba(99, 102, 241, 0.1); border-color: rgba(99, 102, 241, 0.2); }}
        .cell-empty {{ color: var(--text-dim); opacity: 0.3; }}

        .category-tag {{
            font-size: 0.8rem;
            color: var(--text-dim);
            margin-bottom: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .warning-icon {{ margin-right: 8px; }}

        /* Phase VII: Visual Diagnostics */
        .visualization-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 40px; }}
        .forensic-box {{ background: var(--card-bg); padding: 24px; border-radius: 16px; border: 1px solid var(--border-color); }}
        .svg-map {{ width: 100%; height: 300px; background: #000; border-radius: 8px; border: 1px solid #333; }}
        .aria-log {{ height: 300px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; padding: 10px; }}
        .aria-event {{ padding: 8px; border-bottom: 1px solid #222; display: flex; gap: 12px; align-items: center; }}
        .aria-event .timestamp {{ color: var(--accent-primary); }}
        .aria-event .type {{ color: #22c55e; font-weight: 700; }}
        .aria-event .content {{ color: #ddd; font-style: italic; }}
        .aria-event .target {{ color: var(--text-dim); font-size: 0.7rem; }}
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
                <span class="value" style="color: var(--impact-critical)">{len([v for v in data['violations'] if v['compliance_level'] == 'Below A'])}</span>
                <span class="label">Below A (Major)</span>
            </div>
            <div class="summary-card">
                <span class="value" style="color: var(--impact-serious)">{len([v for v in data['violations'] if v['compliance_level'] == 'A'])}</span>
                <span class="label">Level A Risks</span>
            </div>
            <div class="summary-card">
                <span class="value" style="color: var(--accent-primary)">{len([v for v in data['violations'] if v['compliance_level'] == 'AA'])}</span>
                <span class="label">Level AA Risks</span>
            </div>
        </div>
        
        {matrix_html}

        <div class="hierarchy-container">
            {headings_html if headings_html else '<div class="hierarchy-item" style="color: var(--impact-minor)">No structural hierarchy anomalies detected.</div>'}
        </div>

        <div class="visualization-container">
            <div class="forensic-box">
                <h3 class="section-title" style="margin-top:0">Visual Focus Path</h3>
                <svg class="svg-map" viewBox="0 0 1920 1080">
                    <rect width="100%" height="100%" fill="#0a0a0f" />
                    {focus_svg}
                </svg>
            </div>
            <div class="forensic-box">
                <h3 class="section-title" style="margin-top:0">Dynamic ARIA-Live Log</h3>
                <div class="aria-log">
                    {aria_html if aria_html else '<div style="color:var(--text-dim)">No dynamic ARIA events recorded.</div>'}
                </div>
            </div>
        </div>

        <h2 class="section-title">Violations Inventory</h2>
        <div class="violations-container">
            {violations_html}
        </div>
    </div>
</body>
</html>
        """

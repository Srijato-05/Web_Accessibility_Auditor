import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from html import escape as html_escape

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from playwright.sync_api import sync_playwright # type: ignore

def generate_html_from_json(data: Dict[str, Any], override_findings: list = None, hide_header: bool = False) -> str:
    """Generates a Clinical-Grade HTML report from the JSON audit findings."""
    session_id = data.get("session_id", "Unknown")
    target_url = data.get("target_url", "Multiple Targets" if data.get("is_crawl", False) else "Unknown")
    generated_at_raw = data.get("generated_at", "")
    try:
        dt = datetime.fromisoformat(generated_at_raw)
        generated_at = dt.strftime("%B %d, %Y - %H:%M:%S")
    except Exception:
        generated_at = generated_at_raw

    raw_findings = override_findings if override_findings is not None else data.get("findings", data.get("violations", []))
    findings = list(raw_findings) if raw_findings is not None else []
    full_findings = data.get("findings", data.get("violations", [])) or []
    total_findings = data.get("total_findings", len(full_findings))

    by_agent = data.get("by_agent", {})
    if not by_agent:
        by_agent = {}
        for f in full_findings:
            if isinstance(f, dict):
                agent = f.get("agent", "unknown").lower()
                by_agent[agent] = by_agent.get(agent, 0) + 1
    
    # Optimize rendering performance for massive datasets
    render_as_table = True
    is_truncated = False

    # Matrix Support
    matrix = data.get("matrix", {})
    
    # Core Agents + Static Axe Engine
    agents_list = ["axe", "htmlcs", "visual", "motor", "cognitive", "neural"]
    full_matrix = {}
    for a in agents_list:
        full_matrix[a] = {"Perceivable": 0, "Operable": 0, "Understandable": 0, "Robust": 0, "General": 0}
        
    if full_findings:
        from auditor.shared.compliance_mapper import ComplianceMapper
        principles = list(ComplianceMapper.WCAG_PRINCIPLES.values())
        for f in full_findings:
            if isinstance(f, dict):
                agent = str(f.get("agent", "visual")).lower()
                category = str(f.get("category", "General")).lower()
                
                norm_cat = "General"
                for p in principles:
                    if p.lower() in category:
                        norm_cat = p
                        break
                
                if norm_cat == "General":
                    tags = f.get("tags") or []
                    rule_id = f.get("rule_id") or f.get("violation") or ""
                    re_cat = ComplianceMapper.get_category(tags, rule_id, agent)
                    for p in principles:
                        if p.lower() in re_cat.lower():
                            norm_cat = p
                            break
                
                if agent in full_matrix:
                    full_matrix[agent][norm_cat] += 1
    elif matrix:
        for a, categories in matrix.items():
            a_lower = str(a).lower()
            if a_lower in full_matrix:
                for cat, val in categories.items():
                    from auditor.shared.compliance_mapper import ComplianceMapper
                    principles = list(ComplianceMapper.WCAG_PRINCIPLES.values())
                    cat_lower = str(cat).lower()
                    norm_cat = "General"
                    for p in principles:
                        if p.lower() in cat_lower:
                            norm_cat = p
                            break
                    full_matrix[a_lower][norm_cat] += val

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>A11yAudit Accessibility Report</title>
        <style>
            body {{
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                color: #0f172a;
                background-color: #ffffff;
                margin: 0;
                padding: 24px;
                -webkit-print-color-adjust: exact;
            }}
            .container {{
                max-width: 100%;
                margin: 0;
                background: transparent;
                padding: 0;
                border-radius: 0;
                box-shadow: none;
            }}
            .header-banner {{
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                margin-bottom: 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .header-banner h1 {{
                margin: 0;
                font-size: 2.2em;
                font-weight: 800;
                letter-spacing: -0.04em;
                color: #f8fafc;
            }}
            .meta-info {{
                text-align: right;
                font-size: 0.85em;
                color: #94a3b8;
            }}
            .meta-info p {{ margin: 3px 0; }}
            .meta-info strong {{ color: #e2e8f0; }}
            
            h2 {{ color: #1e293b; font-size: 1.5em; margin-top: 24px; margin-bottom: 12px; font-weight: 700; letter-spacing: -0.02em; }}
            
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 10px;
                margin-bottom: 24px;
            }}
            .card {{
                background: #f8fafc;
                padding: 12px 8px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #e2e8f0;
                position: relative;
                overflow: hidden;
            }}
            .card.total {{ background: #eff6ff; border-color: #bfdbfe; grid-column: span 1; }}
            .card h3 {{ margin: 0 0 6px 0; font-size: 0.7em; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
            .card .number {{ font-size: 1.8em; font-weight: 800; margin: 0; color: #0f172a; line-height: 1; }}
            
            .card.axe {{ border-top: 4px solid #64748b; }}
            .card.htmlcs {{ border-top: 4px solid #d97706; }}
            .card.visual {{ border-top: 4px solid #3b82f6; }}
            .card.motor {{ border-top: 4px solid #10b981; }}
            .card.cognitive {{ border-top: 4px solid #8b5cf6; }}
            .card.neural {{ border-top: 4px solid #ef4444; }}

            /* Matrix Styling */
            .matrix-container {{ background: white; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; page-break-inside: avoid; break-inside: avoid; }}
            .matrix-table {{ width: 100%; border-collapse: collapse; text-align: center; }}
            .matrix-table th {{ background: #f8fafc; padding: 10px 12px; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; border-bottom: 2px solid #e2e8f0; }}
            .matrix-table td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; font-weight: 600; font-size: 0.95em; }}
            .matrix-table td:last-child {{ border-right: none; }}
            .matrix-table tbody tr:last-child td {{ border-bottom: none; }}
            .matrix-label {{ text-align: left !important; background: #f8fafc; border-right: 2px solid #e2e8f0 !important; color: #334155; font-size: 0.85em !important; text-transform: uppercase; letter-spacing: 0.05em; }}
            
            .val-high {{ color: #ef4444; font-weight: 800; }}
            .val-med {{ color: #f59e0b; font-weight: 800; }}
            .val-low {{ color: #3b82f6; font-weight: 700; }}
            .val-zero {{ color: #cbd5e1; font-weight: 400; }}

            .findings-table-container {{
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                overflow: hidden;
                margin-top: 10px;
                margin-bottom: 30px;
                background: #ffffff;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }}
            .findings-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .findings-table th {{
                background: #f1f5f9;
                color: #334155;
                font-weight: 700;
                text-transform: uppercase;
                font-size: 0.75em;
                letter-spacing: 0.05em;
                padding: 12px 16px;
                border-bottom: 2px solid #cbd5e1;
                text-align: left;
            }}
            .findings-table td {{
                padding: 14px 16px;
                vertical-align: top;
                border-bottom: 1px solid #e2e8f0;
                font-size: 0.88em;
                line-height: 1.5;
                color: #334155;
            }}
            .findings-table tr:nth-child(even) {{
                background: #f8fafc;
            }}
            .findings-table tr:last-child td {{
                border-bottom: none;
            }}
            .findings-table tr {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            .findings-table .anomaly-title {{
                font-weight: 700;
                color: #0f172a;
                font-size: 0.95em;
            }}
            .findings-table .anomaly-guideline {{
                color: #64748b;
                font-size: 0.8em;
                font-weight: 600;
                margin-top: 4px;
                display: block;
            }}
            .findings-table .fix-guide {{
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                color: #166534;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.85em;
                margin-top: 6px;
                display: inline-block;
                width: 95%;
            }}
            .findings-table .dom-code {{
                font-family: Consolas, "Liberation Mono", Courier, monospace;
                font-size: 0.82em;
                background: #f8fafc;
                color: #334155;
                padding: 6px 10px;
                border-radius: 4px;
                border: 1px solid #cbd5e1;
                word-wrap: break-word;
                white-space: pre-wrap;
                display: block;
                max-width: 100%;
                overflow-x: auto;
            }}
            
            .badge {{
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 0.75em;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                display: inline-block;
            }}
            .badge.axe {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
            .badge.htmlcs {{ background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }}
            .badge.visual {{ background: #dbeafe; color: #1d4ed8; }}
            .badge.motor {{ background: #d1fae5; color: #047857; }}
            .badge.cognitive {{ background: #ede9fe; color: #6d28d9; }}
            .badge.neural {{ background: #fee2e2; color: #b91c1c; }}
            .badge.guideline {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
        </style>
    </head>
    """
    if hide_header:
        html += f"""
        <body>
            <div class="container">
                <h2 style="margin-top: 20px;">Vector Findings Telemetry (Continued)</h2>
        """
    else:
        html += f"""
        <body>
            <div class="container">
                <div class="header-banner">
                    <h1>A11yAudit Accessibility Report</h1>
                    <div class="meta-info">
                        <p><strong>Target:</strong> {target_url}</p>
                        <p><strong>Session ID:</strong> {session_id}</p>
                        <p><strong>Generated:</strong> {generated_at}</p>
                    </div>
                </div>
                
                <div class="summary-grid">
                    {f'<div class="card" style="grid-column: span 7; background: #fffbeb; border-color: #fcd34d; color: #b45309;"><strong>WARNING:</strong> Maximum PDF limit reached. Displaying the top 250 findings. Check JSON export for complete dataset.</div>' if is_truncated else ''}
                    <div class="card total">
                        <h3>Total Anomalies</h3>
                        <p class="number">{total_findings}</p>
                    </div>
                    <div class="card axe" style="grid-column: span 1;">
                        <h3>Standard (Axe)</h3>
                        <p class="number">{by_agent.get('axe', 0)}</p>
                    </div>
                    <div class="card htmlcs">
                        <h3>Standard (HTMLCS)</h3>
                        <p class="number">{by_agent.get('htmlcs', 0)}</p>
                    </div>
                    <div class="card visual">
                        <h3>Visual AI</h3>
                        <p class="number">{by_agent.get('visual', 0)}</p>
                    </div>
                    <div class="card motor">
                        <h3>Motor Physics</h3>
                        <p class="number">{by_agent.get('motor', 0)}</p>
                    </div>
                    <div class="card cognitive">
                        <h3>Cognitive NLP</h3>
                        <p class="number">{by_agent.get('cognitive', 0)}</p>
                    </div>
                    <div class="card neural">
                        <h3>Neural Kinetic</h3>
                        <p class="number">{by_agent.get('neural', 0)}</p>
                    </div>
                </div>

                <h2>Diagnostic Matrix</h2>
                <div class="matrix-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 20%;">Agent Engine</th>
                                <th style="width: 20%;">Perceivable</th>
                                <th style="width: 20%;">Operable</th>
                                <th style="width: 20%;">Understandable</th>
                                <th style="width: 20%;">Robust</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td class="matrix-label">{
                                    'Standard (Axe)' if agent=='axe' else 
                                    'Standard (HTMLCS)' if agent=='htmlcs' else 
                                    'Visual AI' if agent=='visual' else 
                                    'Motor Physics' if agent=='motor' else 
                                    'Cognitive NLP' if agent=='cognitive' else 
                                    'Neural Kinetic'
                                }</td>
                                <td class="{('val-high' if full_matrix[agent].get('Perceivable',0) > 10 else 'val-med' if full_matrix[agent].get('Perceivable',0) > 0 else 'val-zero')}">{full_matrix[agent].get('Perceivable', 0)}</td>
                                <td class="{('val-high' if full_matrix[agent].get('Operable',0) > 10 else 'val-med' if full_matrix[agent].get('Operable',0) > 0 else 'val-zero')}">{full_matrix[agent].get('Operable', 0)}</td>
                                <td class="{('val-high' if full_matrix[agent].get('Understandable',0) > 10 else 'val-med' if full_matrix[agent].get('Understandable',0) > 0 else 'val-zero')}">{full_matrix[agent].get('Understandable', 0)}</td>
                                <td class="{('val-high' if full_matrix[agent].get('Robust',0) > 10 else 'val-med' if full_matrix[agent].get('Robust',0) > 0 else 'val-zero')}">{full_matrix[agent].get('Robust', 0)}</td>
                            </tr>''' for agent in agents_list])}
                        </tbody>
                    </table>
                </div>
                
                <div style="page-break-after: always; break-after: page;"></div>
                
                <h2>Vector Findings Telemetry</h2>
        """

    grouped_findings = { "axe": [], "htmlcs": [], "visual": [], "motor": [], "cognitive": [], "neural": [] }
    for f in findings:
        agent = str(f.get("agent", "unknown")).lower()
        if agent in grouped_findings:
            grouped_findings[agent].append(f)

    agent_titles = {
        "axe": "Static Baseline (Axe Core)",
        "htmlcs": "Static Baseline (HTML CodeSniffer)",
        "visual": "Visual & Luminance Anomalies",
        "motor": "Motor & Spatial Physics Collisions",
        "cognitive": "Cognitive & Semantic NLP Deviations",
        "neural": "Neural & Kinetic Vestibular Triggers"
    }

    global_idx = 1
    for agent_key in ["axe", "htmlcs", "visual", "motor", "cognitive", "neural"]:
        agent_list = grouped_findings[agent_key]
        if not agent_list:
            continue
            
        agent_title = agent_titles[agent_key]
        html += f"""
            <h3 style="margin-top: 50px; margin-bottom: 20px; font-size: 1.4em; color: #334155; display: flex; align-items: center; gap: 10px;">
                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: {
                    '#64748b' if agent_key=='axe' else '#d97706' if agent_key=='htmlcs' else '#3b82f6' if agent_key=='visual' else '#10b981' if agent_key=='motor' else '#8b5cf6' if agent_key=='cognitive' else '#ef4444'
                }"></span>
                {agent_title} ({len(agent_list)})
            </h3>
        """
        
        if render_as_table:
            html += f"""
            <div class="findings-table-container">
            <table class="findings-table">
                <thead>
                    <tr>
                        <th style="width: 25%;">Rule / Anomaly</th>
                        <th style="width: 10%;">Impact</th>
                        <th style="width: 40%;">Diagnosis & Remediation</th>
                        <th style="width: 25%;">DOM Signature</th>
                    </tr>
                </thead>
                <tbody>
            """
            for finding in agent_list:
                violation_val = finding.get("violation") or finding.get("rule_id") or "Anomaly Detected"
                violation = html_escape(str(violation_val).replace("_", " ").title())
                guideline = html_escape(str(finding.get("guideline") or finding.get("compliance_level") or "G-Level"))
                issue_desc = html_escape(str(finding.get("issue") or finding.get("description") or "No description provided."))
                impact = html_escape(str(finding.get("impact") or "N/A"))
                element = finding.get("element") or finding.get("selector") or ""
                fix = html_escape(str(finding.get("fix") or "No programmatic fix available."))
                
                safe_element = html_escape(str(element))
                if len(safe_element) > 300: safe_element = safe_element[:297] + "..."
                
                html += f"""
                    <tr>
                        <td>
                            <div class="anomaly-title">{violation}</div>
                            <span class="anomaly-guideline">{guideline}</span>
                        </td>
                        <td><span class="badge {agent_key}">{impact}</span></td>
                        <td>
                            <div style="color: #334155; margin-bottom: 6px;">{issue_desc}</div>
                            <div class="fix-guide"><strong>Fix:</strong> {fix}</div>
                        </td>
                        <td>
                            <code class="dom-code">{safe_element}</code>
                        </td>
                    </tr>
                """
                global_idx += 1
            html += "</tbody></table></div>"
            
        else:
            pass

    html += """
        </div>
    </body>
    </html>
    """
    return html


def _render_chunks_to_pdfs(chunks_data: list, output_dir: str):
    """
    Renders multiple HTML contents to their respective PDF paths using a single Playwright browser instance.
    chunks_data: list of tuples (html_content, output_pdf_path)
    """
    import tempfile
    import pathlib
    
    temp_files = []
    try:
        tasks = []
        for html_content, pdf_path in chunks_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8", dir=output_dir) as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            temp_files.append(temp_html_path)
            tasks.append((temp_html_path, pdf_path))
            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
            context = browser.new_context(java_script_enabled=False)
            page = context.new_page()
            page.emulate_media(media="print")
            page.set_default_timeout(0) # Uncap engine limits for massive PDF generations
            
            for temp_html_path, pdf_path in tasks:
                file_uri = pathlib.Path(temp_html_path).as_uri()
                page.goto(file_uri, wait_until="domcontentloaded", timeout=120000)
                page.pdf(
                    path=pdf_path,
                    format="Letter",
                    landscape=True,
                    print_background=True,
                    margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"}
                )
            browser.close()
    except Exception as e:
        safe_msg = repr(e).encode('ascii', 'replace').decode('ascii')
        print(f"Playwright error during PDF rendering: {safe_msg}")
        raise RuntimeError(f"Playwright PDF Engine Error: {safe_msg}")
    finally:
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as cleanup_err:
                    print(f"Cleanup warning: Could not remove temporary HTML {path}: {cleanup_err}")

def convert_json_to_pdf(json_path: str, output_pdf_path: str):
    """
    Reads a JSON findings file, generates an HTML report, and
    uses Playwright to convert the HTML to a PDF. Can handle massive reports
    by writing to a temporary file before rendering.
    Uses PDF chunking and stitching to prevent OOM / layout engine crashes on massive datasets.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    raw_findings = data.get('findings', data.get('violations', []))
    findings = list(raw_findings) if raw_findings is not None else []
    total_findings = len(findings)
    print(f"Total findings to render: {total_findings}")

    # Threshold for chunking (switch to chunking if dataset is massive)
    CHUNK_THRESHOLD = 150
    CHUNK_SIZE = 150

    output_dir = os.path.dirname(os.path.abspath(output_pdf_path))

    if total_findings <= CHUNK_THRESHOLD:
        # Standard rendering flow (no chunking needed)
        html_content = generate_html_from_json(data)
        _render_chunks_to_pdfs([(html_content, output_pdf_path)], output_dir)
        return

    # Option 2: Chunking & Stitching Flow
    print(f"Dataset exceeds threshold ({total_findings} > {CHUNK_THRESHOLD}). Activating PDF Chunking & Stitching...")
    
    # Dynamically verify / install pypdf
    try:
        import pypdf
    except ImportError:
        print("pypdf is missing. Dynamically installing pypdf...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
            import pypdf
        except Exception as inst_err:
            print(f"Warning: Failed to install pypdf via pip: {inst_err}.")
            raise RuntimeError(f"Required dependency pypdf is missing and could not be installed: {inst_err}")

    # Split findings into chunks
    chunks = [findings[i:i + CHUNK_SIZE] for i in range(0, total_findings, CHUNK_SIZE)]
    
    # Build list of rendering tasks
    render_tasks = []
    temp_pdf_paths = []
    
    for index, chunk in enumerate(chunks):
        hide_header = index > 0
        html_content = generate_html_from_json(data, override_findings=chunk, hide_header=hide_header)
        temp_pdf_path = os.path.join(output_dir, f"temp_chunk_{index}_{os.path.basename(output_pdf_path)}")
        render_tasks.append((html_content, temp_pdf_path))
        temp_pdf_paths.append(temp_pdf_path)

    try:
        print(f"Rendering {len(render_tasks)} PDF chunks to disk using single Playwright context...")
        _render_chunks_to_pdfs(render_tasks, output_dir)

        # Merge PDFs using pypdf
        print("Stitching PDF chunks together...")
        try:
            from pypdf import PdfWriter
        except ImportError:
            from pypdf import PdfFileWriter as PdfWriter
        
        merger = PdfWriter()
        for path in temp_pdf_paths:
            merger.append(path)
        
        merger.write(output_pdf_path)
        merger.close()
        print(f"Successfully created stitched PDF: {output_pdf_path}")

    finally:
        # Cleanup temporary PDF files
        for path in temp_pdf_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as cleanup_err:
                    print(f"Cleanup warning: Could not remove temporary PDF chunk {path}: {cleanup_err}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert Agent Findings JSON to PDF")
    parser.add_argument("json_path", help="Path to the JSON finding file")
    parser.add_argument("--output", "-o", help="Path to save the PDF (optional)", default=None)
    
    args = parser.parse_args()
    
    json_path = args.json_path
    if not os.path.exists(json_path):
        print(f"Error: File '{json_path}' not found.")
        exit(1)
        
    output_pdf = args.output
    if not output_pdf:
        output_pdf = os.path.splitext(json_path)[0] + ".pdf"
        
    convert_json_to_pdf(json_path, output_pdf)

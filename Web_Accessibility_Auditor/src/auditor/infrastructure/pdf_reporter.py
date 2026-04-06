import json
import os
from datetime import datetime
from typing import Dict, Any

from playwright.sync_api import sync_playwright

def generate_html_from_json(data: Dict[str, Any]) -> str:
    """Generates an HTML report from the JSON audit findings."""
    session_id = data.get("session_id", "Unknown")
    generated_at_raw = data.get("generated_at", "")
    try:
        dt = datetime.fromisoformat(generated_at_raw)
        generated_at = dt.strftime("%B %d, %Y - %H:%M:%S")
    except Exception:
        generated_at = generated_at_raw

    total_findings = data.get("total_findings", 0)
    by_agent = data.get("by_agent", {})
    findings = data.get("findings", [])

    # Start building HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Accessibility Audit Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f9fafb;
                margin: 0;
                padding: 40px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #1a202c;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            .meta-info {{
                margin-bottom: 30px;
                color: #4a5568;
                font-size: 0.95em;
            }}
            .meta-info p {{ margin: 5px 0; }}
            .summary-box {{
                display: flex;
                gap: 20px;
                margin-bottom: 40px;
            }}
            .card {{
                flex: 1;
                background: #ebf4ff;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #bee3f8;
            }}
            .card h3 {{ margin: 0 0 10px 0; font-size: 1.1em; color: #2b6cb0; }}
            .card .number {{ font-size: 2em; font-weight: bold; color: #2c5282; margin: 0; }}
            
            h2 {{ color: #2d3748; margin-top: 40px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }}
            
            .finding {{
                background: #fff;
                border: 1px solid #e2e8f0;
                border-left: 4px solid #ed8936;
                border-radius: 6px;
                padding: 20px;
                margin-bottom: 20px;
                page-break-inside: avoid;
            }}
            .finding.visual {{ border-left-color: #4299e1; }}
            .finding.motor {{ border-left-color: #48bb78; }}
            .finding.cognitive {{ border-left-color: #9f7aea; }}
            
            .finding-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            .finding-title {{
                margin: 0;
                font-size: 1.2em;
                color: #2d3748;
                font-weight: bold;
                text-transform: capitalize;
            }}
            .badge {{
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.8em;
                font-weight: bold;
                color: white;
                text-transform: uppercase;
            }}
            .badge.visual {{ background: #4299e1; }}
            .badge.motor {{ background: #48bb78; }}
            .badge.cognitive {{ background: #9f7aea; }}
            .badge.unknown {{ background: #a0aec0; }}
            
            .row {{ margin-bottom: 10px; }}
            .label {{ font-weight: bold; color: #4a5568; width: 100px; display: inline-block; }}
            
            .code-block {{
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
                font-size: 0.9em;
                word-wrap: break-word;
                white-space: pre-wrap;
                margin: 5px 0 15px 0;
            }}
            
            .fix-block {{
                background: #f0fff4;
                border: 1px solid #c6f6d5;
                padding: 15px;
                border-radius: 6px;
                margin-top: 15px;
            }}
            .fix-title {{ font-weight: bold; color: #276749; margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Accessibility Audit Report</h1>
            
            <div class="meta-info">
                <p><strong>Session ID:</strong> {session_id}</p>
                <p><strong>Date Generated:</strong> {generated_at}</p>
            </div>
            
            <div class="summary-box">
                <div class="card">
                    <h3>Total Findings</h3>
                    <p class="number">{total_findings}</p>
                </div>
                <div class="card">
                    <h3>Visual Agent</h3>
                    <p class="number">{by_agent.get('visual', 0)}</p>
                </div>
                <div class="card">
                    <h3>Motor Agent</h3>
                    <p class="number">{by_agent.get('motor', 0)}</p>
                </div>
                <div class="card">
                    <h3>Cognitive Agent</h3>
                    <p class="number">{by_agent.get('cognitive', 0)}</p>
                </div>
                <div class="card">
                    <h3>Neural Agent</h3>
                    <p class="number">{by_agent.get('neural', 0)}</p>
                </div>
            </div>
            
            <h2>Detailed Findings</h2>
    """

    for idx, finding in enumerate(findings, 1):
        agent = finding.get("agent", "unknown").lower()
        violation = finding.get("violation", "Issue").replace("_", " ")
        guideline = finding.get("guideline", "N/A")
        issue_desc = finding.get("issue", "No description provided.")
        impact = finding.get("impact", "N/A")
        element = finding.get("element", "")
        fix = finding.get("fix", "No fix recommended.")
        
        html += f"""
            <div class="finding {agent}">
                <div class="finding-header">
                    <h3 class="finding-title">{idx}. {violation} (WCAG {guideline})</h3>
                    <span class="badge {agent}">{agent}</span>
                </div>
                <div class="row">
                    <span class="label">Impact:</span> {impact}
                </div>
                <div class="row">
                    <span class="label">Issue:</span> {issue_desc}
                </div>
        """
        
        if element:
            # Escape HTML tags for display
            safe_element = element.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html += f"""
                <div class="row" style="margin-top: 15px;">
                    <span class="label" style="display: block; margin-bottom: 5px;">Element:</span>
                    <div class="code-block">{safe_element}</div>
                </div>
            """
            
        html += f"""
                <div class="fix-block">
                    <div class="fix-title">Recommended Fix:</div>
                    <div>{fix}</div>
                </div>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def convert_json_to_pdf(json_path: str, output_pdf_path: str):
    """
    Reads a JSON findings file, generates an HTML report, and
    uses Playwright to convert the HTML to a PDF. Can handle massive reports
    by writing to a temporary file before rendering.
    """
    import tempfile
    import pathlib
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    html_content = generate_html_from_json(data)
    
    print(f"Generating PDF for {len(data.get('findings', []))} findings...")
    
    # Write to a temporary HTML file to bypass Playwright IPC string size limits
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_html:
        temp_html.write(html_content)
        temp_html_path = temp_html.name
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
            context = browser.new_context(java_script_enabled=False)
            page = context.new_page()
            
            # Safe rendering by loading local file
            file_uri = pathlib.Path(temp_html_path).as_uri()
            page.goto(file_uri, wait_until="networkidle", timeout=60000)
            page.emulate_media(media="print")
            
            page.pdf(
                path=output_pdf_path,
                format="A4",
                print_background=True,
                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"}
            )
            browser.close()
            
        print(f"Successfully created PDF: {output_pdf_path}")
    except Exception as e:
        print(f"Playwright error during PDF rendering: {e}")
        # In a multiprocessing environment, print to stdout as it might not land in the logger easily
        raise e
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)

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

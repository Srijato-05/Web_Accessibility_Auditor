import asyncio
import sys
import os
import uuid
from sqlalchemy.ext.asyncio import create_async_engine # type: ignore
from sqlmodel import SQLModel # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore

# IDE PATH RECONCILIATION: Redundant path hinting for static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

# MANDATORY WINDOWS FIX for Playwright subprocess support
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Extreme Registry Imports
# Extreme Registry Imports
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel # type: ignore
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository # type: ignore
from auditor.infrastructure.playwright_engine import PlaywrightEngine # type: ignore
from auditor.application.audit_service import AuditService # type: ignore
from auditor.application.reporter import AuditReporter # type: ignore
from auditor.infrastructure.pdf_reporter import convert_json_to_pdf # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore
from auditor.shared.paths import REPORTS_DIR, DATABASE_URL, EXPORTS_DIR, PROJECT_ROOT # type: ignore

async def main():
    # 1. CLI Argument Handling
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Accessibility Auditor Single-Target CLI [v0.1.0]
Usage: python single_url.py <url> [options]

Options:
  --help, -h    Show this help message
  --no-neural   Skip AI-powered analysis (Neural Agent)
        """)
        return

    if len(sys.argv) < 2:
        auditor_logger.error("Usage: python single_url.py <url>")
        return

    # Automated Directory Reconciliation
    for folder in ["logs", "data", "exports"]:
        os.makedirs(os.path.join(REPORTS_DIR, folder), exist_ok=True)

    url = sys.argv[1]
    skip_neural = "--no-neural" in sys.argv
    if skip_neural:
        # Remove --no-neural from argv if we need to process other things, 
        # but here we just need the flag.
        sys.argv.remove("--no-neural")
        
    auditor_logger.info(f"Auditor Single-Target Audit Console [v0.1.0] ONLINE for: {url}")

    # 1. Setup Infrastructure
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 2. DDD Component Lifecycle
    async with AsyncSession(engine) as db_session:
        repository = SqlAlchemyAuditRepository(db_session)
        # Note: AuditService does not take reports_dir in this version's constructor
        service = AuditService(None, repository)
        
        try:
            result = await service.execute_audit(url, skip_neural=skip_neural)
            auditor_logger.info(f"Audit Session {result.id} COMPLETE. Status: {result.status.value}")

            # 3. Generate Stakeholder Report (including Agentic Advice)
            reports_out = os.path.join(REPORTS_DIR, "exports")
            reporter = AuditReporter(db_session)
            report_paths = await reporter.generate_summary_report()
            auditor_logger.info(f"Stakeholder Dashboard Generated: {report_paths.get('html', 'N/A')}")
            
            return result.id
        except Exception as e:
            auditor_logger.critical(f"FATAL: Audit protocol aborted for {url}: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    try:
        session_id = asyncio.run(main())
        
        # 4. Finalize PDF Production (Reliable sequence OUTSIDE asyncio loop)
        if session_id and len(sys.argv) >= 2:
            import glob
            from urllib.parse import urlparse
            url = sys.argv[1]
            
            reports_out = str(EXPORTS_DIR)
            
            # Match patterns
            findings_pattern = os.path.join(reports_out, f"agent_findings_{str(session_id)[:8]}_*.json") # type: ignore
            domain = urlparse(url).netloc.replace("www.", "")
            findings_pattern_url = os.path.join(reports_out, f"{domain}_*.json")
            
            matches = glob.glob(findings_pattern) + glob.glob(findings_pattern_url)
            if matches:
                latest_json = max(matches, key=os.path.getctime)
                out_pdf = latest_json.replace(".json", ".pdf")
                print(f"Post-Audit: Generating PDF Advice from {os.path.basename(latest_json)}...")
                convert_json_to_pdf(latest_json, out_pdf)
                print(f"PDF Remediation Advice Generated: {out_pdf}")
                
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")
    finally:
        # Give the Windows Proactor time to settle pipes
        if sys.platform == 'win32':
            import time
            time.sleep(0.5)

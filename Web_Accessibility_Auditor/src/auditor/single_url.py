import asyncio
import sys
import os

# IDE PATH RECONCILIATION: Redundant path hinting for static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Extreme Registry Imports
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.application.audit_service import AuditService
from auditor.application.reporter import AuditReporter
from auditor.infrastructure.pdf_reporter import convert_json_to_pdf
from auditor.shared.logging import auditor_logger

# Path Reconciliation for Reports Base
_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS_DIR = os.path.join(_base, "reports")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(REPORTS_DIR, 'data', 'audit_results.db')}"

async def main():
    # 1. CLI Argument Handling
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Accessibility Auditor Single-Target CLI [v0.1.0]
Usage: python single_url.py <url>

Options:
  --help, -h    Show this help message
        """)
        return

    if len(sys.argv) < 2:
        auditor_logger.error("Usage: python single_url.py <url>")
        return

    url = sys.argv[1]
    auditor_logger.info(f"Auditor Single-Target Audit Console [v0.1.0] ONLINE for: {url}")

    # 1. Setup Infrastructure
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 2. DDD Component Lifecycle
    async with AsyncSession(engine) as db_session:
        repository = SqlAlchemyAuditRepository(db_session)
        service = AuditService(None, repository, reports_dir=REPORTS_DIR)
        
        try:
            result = await service.execute_audit(url)
            auditor_logger.info(f"Audit Session {result.id} COMPLETE. Status: {result.status.value}")

            # 3. Generate Stakeholder Report (including Agentic Advice)
            reports_out = os.path.join(REPORTS_DIR, "exports")
            reporter = AuditReporter(db_session)
            report_paths = await reporter.generate_summary_report(output_dir=reports_out)
            auditor_logger.info(f"Stakeholder Dashboard Generated: {report_paths['html']}")
            
            return result.id
        except Exception as e:
            auditor_logger.critical(f"FATAL: Audit protocol aborted for {url}: {e}")
            return None

if __name__ == "__main__":
    try:
        session_id = asyncio.run(main())
        
        # 4. Finalize PDF Production (Reliable sequence OUTSIDE asyncio loop)
        if session_id and len(sys.argv) >= 2:
            import glob
            from urllib.parse import urlparse
            url = sys.argv[1]
            
            _base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            reports_out = os.path.join(_base, "reports", "exports")
            
            # Match patterns
            findings_pattern = os.path.join(reports_out, f"agent_findings_{str(session_id)[:8]}_*.json")
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

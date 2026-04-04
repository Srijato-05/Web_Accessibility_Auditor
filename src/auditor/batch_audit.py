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

# Core Technical Imports
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor
from auditor.domain.crawler import LinkDiscoveryService
from auditor.domain.models import AuditTarget
from auditor.application.audit_service import AuditService
from auditor.application.crawl_service import CrawlService
from auditor.application.batch_service import BatchAuditManager
from auditor.shared.logging import auditor_logger

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def main():
    auditor_logger.info("Accessibility Auditor Batch CLI [v0.1.0] Initialized.")

    # 1. Environment Setup
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 3. CLI Argument Handling
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Accessibility Auditor Batch CLI [v0.1.0]
Usage: python batch_audit.py [options]

Options:
  --help, -h    Show this help message
  --add [url]   Add a new target domain to the audit queue
        """)
        return

    if len(sys.argv) >= 3 and sys.argv[1] == "--add":
        async with AsyncSession(engine) as db_session:
            batch_repo = SqlAlchemyTargetRepository(db_session)
            target_url = sys.argv[2]
            new_domain = AuditTarget(url=target_url)
            await batch_repo.add_domain(new_domain)
            auditor_logger.info(f"Target Added: {target_url}")
            return
        
    # 4. Batch Execution
    try:
        batch_orchestrator = BatchAuditManager(engine)
        await batch_orchestrator.run_batch_audit()
    except Exception as e:
        auditor_logger.critical(f"Critical Batch Process Failure: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")

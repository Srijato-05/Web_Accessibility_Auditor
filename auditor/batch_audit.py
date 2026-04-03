import asyncio
import sys
import os

# IDE PATH RECONCILIATION: Redundant path hinting for static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Core Technical Imports
from auditor.infrastructure.persistence_models import Base
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

DATABASE_URL = "sqlite+aiosqlite:///./audit_results.db"

async def main():
    auditor_logger.info("Accessibility Auditor Batch CLI [v0.1.0] Initialized.")

    # 1. Environment Setup
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Execution Logic
    async with async_session_factory() as db_session:
        # Audit Service Configuration
        audit_repo = SqlAlchemyAuditRepository(db_session)
        audit_service = AuditService(None, audit_repo)
        
        link_extractor = PlaywrightLinkExtractor()
        crawler_service = LinkDiscoveryService(link_extractor)
        crawl_service = CrawlService(
            audit_service=audit_service,
            crawler_service=crawler_service,
            max_depth=2,
            max_pages=20,
            concurrency=5
        )
        
        batch_orchestrator = BatchAuditManager(async_session_factory, crawl_service)
        
        if len(sys.argv) >= 3 and sys.argv[1] == "--add":
            batch_repo = SqlAlchemyTargetRepository(db_session)
            target_url = sys.argv[2]
            new_domain = AuditTarget(url=target_url)
            await batch_repo.add_domain(new_domain)
            auditor_logger.info(f"Target Added: {target_url}")
        
        # 4. Batch Execution
        try:
            await batch_orchestrator.run_batch_audit()
        except Exception as e:
            auditor_logger.critical(f"Critical Batch Process Failure: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")

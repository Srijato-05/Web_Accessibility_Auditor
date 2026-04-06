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
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor
from auditor.domain.crawler import LinkDiscoveryService
from auditor.application.audit_service import AuditService
from auditor.application.crawl_service import CrawlService
from auditor.shared.logging import auditor_logger

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def main():
    # 1. CLI Argument Handling
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Accessibility Auditor Domain Discovery CLI [v0.1.0]
Usage: python site_audit.py <url>

Options:
  --help, -h    Show this help message
        """)
        return

    if len(sys.argv) < 2:
        auditor_logger.error("Usage: python site_audit.py <url>")
        return

    url = sys.argv[1]
    auditor_logger.info(f"Auditor Domain Discovery Console [v0.1.0] ONLINE for: {url}")

    # 1. Setup Infrastructure
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 2. DDD Component Lifecycle
    async with AsyncSession(engine) as db_session:
        repository = SqlAlchemyAuditRepository(db_session)
        
        # Performance Service Layer
        audit_service = AuditService(None, repository)
        link_extractor = PlaywrightLinkExtractor()
        crawler_service = LinkDiscoveryService(link_extractor)
        
        crawl_orchestrator = CrawlService(
            audit_service=audit_service,
            crawler_service=crawler_service,
            max_depth=2,
            max_pages=20
        )
        
        try:
            auditor_logger.info(f"Targeting Domain Ecosystem: {url}")
            await crawl_orchestrator.run(url)
            auditor_logger.info(f"National Discovery Swarm DISMISSED.")
        except Exception as e:
            auditor_logger.critical(f"FATAL: Autonomous Discovery Failure at {url}: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Extreme Registry Imports
from auditor.infrastructure.persistence_models import Base
from auditor.infrastructure.sqlalchemy_repository import SqlAlchemyAuditRepository
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor
from auditor.domain.crawler import CrawlerService
from auditor.application.audit_service import AuditService
from auditor.application.crawl_service import SiteAuditManager
from auditor.shared.logging import auditor_logger

DATABASE_URL = "sqlite+aiosqlite:///./audit_results.db"

async def main():
    if len(sys.argv) < 2:
        auditor_logger.error("Usage: python -m auditor.crawl_cli <url>")
        return

    url = sys.argv[1]
    auditor_logger.info(f"Auditor Domain Discovery Console [v0.1.0] ONLINE for: {url}")

    # 1. Setup Infrastructure
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. DDD Component Lifecycle
    async with async_session_factory() as db_session:
        repository = SqlAlchemyAuditRepository(db_session)
        
        # Performance Service Layer
        audit_service = AuditService(None, repository)
        link_extractor = PlaywrightLinkExtractor()
        crawler_service = CrawlerService(link_extractor)
        
        crawl_orchestrator = SiteAuditManager(
            crawler_service, 
            audit_service,
            max_concurrent_audits=5,
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

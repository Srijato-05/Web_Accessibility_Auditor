import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Extreme Registry Imports
from auditor.infrastructure.persistence_models import Base
from auditor.infrastructure.sqlalchemy_repository import SqlAlchemyAuditRepository
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.application.audit_service import AuditService
from auditor.shared.logging import auditor_logger

DATABASE_URL = "sqlite+aiosqlite:///./audit_results.db"

async def main():
    if len(sys.argv) < 2:
        auditor_logger.error("Usage: python -m auditor.cli <url>")
        return

    url = sys.argv[1]
    auditor_logger.info(f"Auditor Single-Target Audit Console [v0.1.0] ONLINE for: {url}")

    # 1. Setup Infrastructure
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. DDD Component Lifecycle
    async with async_session_factory() as db_session:
        repository = SqlAlchemyAuditRepository(db_session)
        service = AuditService(None, repository)
        
        try:
            result = await service.execute_secure_audit(url)
            auditor_logger.info(f"Audit Session {result.id} COMPLETE. Status: {result.status.value}")
        except Exception as e:
            auditor_logger.critical(f"FATAL: Audit protocol aborted for {url}: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")

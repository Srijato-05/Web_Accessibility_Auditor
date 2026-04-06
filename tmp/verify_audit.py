import os
import sys
import asyncio
import logging

# IDE PATH RECONCILIATION
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from auditor.application.audit_service import AuditService
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.shared.logging import auditor_logger

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def verify_audit():
    engine = create_async_engine(DATABASE_URL)
    async with AsyncSession(engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        browser = PlaywrightEngine(uuid4())
        service = AuditService(browser, repo)
        
        await browser.start()
        try:
            print("--- INITIATING SYNCHRONOUS VERIFICATION MISSION ---")
            await service.execute_audit("https://example.com")
        finally:
            await browser.teardown()

if __name__ == "__main__":
    asyncio.run(verify_audit())

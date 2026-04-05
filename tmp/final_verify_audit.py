import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Path setup
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.application.audit_service import AuditService
from auditor.domain.audit_session import AuditSession

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"
TARGET_URL = "https://en.wikipedia.org/wiki/Web_accessibility"

async def run_targeted_audit():
    engine_db = create_async_engine(DATABASE_URL)
    
    async with AsyncSession(engine_db) as db_session:
        repository = SqlAlchemyAuditRepository(db_session)
        
        browser_engine = PlaywrightEngine(uuid4()) # Temporary session ID for fresh audit
        service = AuditService(browser_engine, repository)
        
        # 1. Run Audit
        print(f"Executing Forensic Audit for: {TARGET_URL}")
        session = await service.execute_audit(TARGET_URL)
        
        # 2. Generate and Save Remediation Plan
        plan = service._generate_remediation_plan(session.violations)
        output_path = f"reports/exports/remediation_FINAL_VERIFIED_{session.id}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(plan)
            
        print(f"Mission Complete! Violations Saved: {len(audit_results.violations)}")
        print(f"Final Remediation Patch-Set: {output_path}")

if __name__ == "__main__":
    asyncio.run(run_targeted_audit())

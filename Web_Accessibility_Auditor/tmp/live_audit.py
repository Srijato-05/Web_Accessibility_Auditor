import asyncio
import sys
import os

# IDE PATH RECONCILIATION
_root = os.path.abspath(os.path.join(os.getcwd()))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.application.audit_service import AuditService
from auditor.infrastructure.playwright_engine import PlaywrightEngine

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def live_audit():
    print("--- [ INITIATING LIVE FORENSIC AUDIT ] ---")
    url = "https://en.wikipedia.org/wiki/Web_accessibility"
    print(f"Target: {url}")
    
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        # We pass None for the engine because AuditService initializes PlaywrightEngine internally in execute_audit
        service = AuditService(None, repo)
        
        print("Engaging Browser Engine (Apex Stealth)...")
        session = await service.execute_audit(url)
        
        print(f"\nAudit Result: {session.status.value.upper()}")
        print(f"Violations Identified: {len(session.violations or [])}")
        
        if session.violations:
            print("\n--- [ TOP CRITICAL/SERIOUS VIOLATIONS ] ---")
            sorted_v = sorted(session.violations, key=lambda x: x.impact.value)
            for v in sorted_v[:5]:
                print(f"[{v.impact.name}] {v.rule_id}: {v.description}")
            
            # Show path to remediation
            report_path = f"reports/exports/remediation_{session.id}.md"
            print(f"\nRemediation Patch-Set generated at: {report_path}")
        else:
            print("No violations found or engine error.")

if __name__ == "__main__":
    asyncio.run(live_audit())

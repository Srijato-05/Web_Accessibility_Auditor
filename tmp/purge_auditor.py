import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

# IDE PATH RECONCILIATION: Ensuring import stability for external scripts
_curr = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_curr, "..", "src"))
if _root not in sys.path:
    sys.path.insert(0, _root)

from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.infrastructure.task_model import TaskModel

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def purge_system():
    """Surgically purges all audit data and task history."""
    engine = create_async_engine(DATABASE_URL)
    
    print("--- INITIATING TOTAL SYSTEM PURGE ---")
    async with AsyncSession(engine) as session:
        try:
            # 1. Clear Violations
            print("Purging Violations...")
            await session.run_sync(lambda s: s.query(ViolationModel).delete())
            
            # 2. Clear Sessions
            print("Purging Audit Sessions...")
            await session.run_sync(lambda s: s.query(AuditSessionModel).delete())
            
            # 3. Clear Tasks
            print("Purging Task Queue Ledger...")
            await session.run_sync(lambda s: s.query(TaskModel).delete())
            
            await session.commit()
            print("--- PURGE COMPLETE: System Reset to Genesis State ---")
        except Exception as e:
            print(f"Purge Failure: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(purge_system())

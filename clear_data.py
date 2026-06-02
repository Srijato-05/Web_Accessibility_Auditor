import os
import sys
import shutil
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Resolve sys.path so we can import from src
root_path = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(root_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Import persistence models to register them in SQLModel metadata
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel, TargetModel
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.domain.models import AuditTarget

async def clear_and_init():
    print("=========================================")
    print("  ACCESSIBILITY AUDITOR SYSTEM UTILITY")
    print("=========================================\n")

    # 1. Data Structure Clearing & Re-initialization
    print("[1/4] DATA LAYER SETUP")
    reports_dir = os.path.join(root_path, "reports")
    data_dir = os.path.join(reports_dir, "data")
    exports_dir = os.path.join(reports_dir, "exports")
    logs_dir = os.path.join(reports_dir, "logs")
    har_dir = os.path.join(reports_dir, "forensics", "har")

    # Clear directories
    for path in [data_dir, exports_dir, logs_dir, har_dir]:
        if os.path.exists(path):
            print(f" -> Clearing directory: {os.path.relpath(path, root_path)}")
            try:
                shutil.rmtree(path)
            except Exception as e:
                # Handle open/locked files by deleting contents individually or ignoring
                print(f" -> Warning while clearing {os.path.relpath(path, root_path)}: {e}")
        os.makedirs(path, exist_ok=True)
    print(" -> Directories successfully re-initialized.")

    # Re-create database schema
    print("\n[2/4] DATABASE SCHEMA & TABLE INITIALIZATION")
    database_url = "sqlite+aiosqlite:///./reports/data/audit_results.db"
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        print(" -> Creating SQLModel tables in audit_results.db...")
        await conn.run_sync(SQLModel.metadata.create_all)
        # Create task_queue table if it doesn't exist
        from auditor.infrastructure.task_model import task_metadata
        await conn.run_sync(task_metadata.create_all)
    print(" -> Database schema created/verified successfully.")

    # Truncate tables to ensure a clean slate even when database file is locked
    from sqlalchemy import text
    async with AsyncSession(engine) as db_session:
        print(" -> Truncating table records...")
        await db_session.execute(text("DELETE FROM violations"))
        await db_session.execute(text("DELETE FROM audit_sessions"))
        await db_session.execute(text("DELETE FROM targets"))
        await db_session.execute(text("DELETE FROM audit_task_queue"))
        await db_session.commit()
    print(" -> All table records successfully cleared.")

    # Seeding targets
    print("\n[3/4] SEED DATA REGISTRATION")
    from auditor.batch_seeding import DEFAULT_SECTOR_MATRIX
    async with AsyncSession(engine) as db_session:
        batch_repo = SqlAlchemyTargetRepository(db_session)
        added = 0
        for category, urls in DEFAULT_SECTOR_MATRIX.items():
            for url in urls:
                new_target = AuditTarget(url=url)
                await batch_repo.add_domain(new_target)
                added += 1
        print(f" -> Successfully seeded {added} default target hosts into ledger database.")

    # 4. Frontend & Backend/API Structure Verification
    print("\n[4/4] FRONTEND, BACKEND & API VERIFICATION")
    frontend_dir = os.path.join(root_path, "frontend")
    backend_dir = os.path.join(root_path, "src", "auditor")
    
    if os.path.exists(frontend_dir):
        print(" -> [FRONTEND] Verified frontend/ exists.")
    else:
        print(" -> [FRONTEND] WARNING: frontend/ directory not found.")
        
    if os.path.exists(backend_dir):
        print(" -> [BACKEND] Verified backend src/auditor/ exists.")
    else:
        print(" -> [BACKEND] WARNING: backend src/auditor/ not found.")
        
    print("\nSystem clean-up and structure initialization completed successfully.")

if __name__ == "__main__":
    asyncio.run(clear_and_init())

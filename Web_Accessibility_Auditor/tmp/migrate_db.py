import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, text

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("Dropping old 'violations' table for schema upgrade...")
        await conn.execute(text("DROP TABLE IF EXISTS violations"))
        
        print("Recreating tables with new schema...")
        # This will recreate all tables defined in persistence_models
        from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel, TargetModel
        await conn.run_sync(SQLModel.metadata.create_all)
        
    print("Migration COMPLETE. Database is now in 'Unique Violation' mode.")

if __name__ == "__main__":
    asyncio.run(migrate())

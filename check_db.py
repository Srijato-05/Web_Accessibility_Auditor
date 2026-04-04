import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def check():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        # Definitively use .exec() for SQLModel to avoid DeprecationWarnings
        result = await session.exec(select(AuditSessionModel).order_by(AuditSessionModel.created_at.desc()))
        last_session = result.first()
        if last_session:
            print(f"Status: {last_session.status}")
            print(f"Error: {last_session.error_message}")
        else:
            print("No sessions found.")

if __name__ == "__main__":
    asyncio.run(check())

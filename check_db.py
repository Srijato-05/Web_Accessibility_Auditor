import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from auditor.infrastructure.persistence_models import SessionModel, ViolationModel
from auditor.infrastructure.sqlalchemy_repository import SqlAlchemyAuditRepository
from sqlalchemy import select

DATABASE_URL = "sqlite+aiosqlite:///./audit_results.db"

async def check():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(SessionModel).order_by(SessionModel.created_at.desc()))
        last_session = result.scalars().first()
        if last_session:
            print(f"Status: {last_session.status}")
            print(f"Error: {last_session.error_message}")
        else:
            print("No sessions found.")

if __name__ == "__main__":
    asyncio.run(check())

import asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from auditor.domain.audit_session import AuditSession
from auditor.infrastructure.persistence_models import ViolationModel

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///f:/Projects/Web_Accessibility_Auditor/reports/data/audit_results.db")
    async with AsyncSession(engine) as session:
        # Check sessions
        res = await session.exec(select(AuditSession))
        sessions = res.all()
        print(f"Total sessions: {len(sessions)}")
        for s in sessions:
            print(f"Session {s.id}: status={s.status.value}, url={s.target_url}")
            
        # Check violations
        res_v = await session.exec(select(ViolationModel))
        violations = res_v.all()
        print(f"Total violations: {len(violations)}")
        for v in violations[:10]:
            print(f"Violation: id={v.id}, session_id={v.session_id}, rule={v.rule_id}")

if __name__ == "__main__":
    asyncio.run(main())

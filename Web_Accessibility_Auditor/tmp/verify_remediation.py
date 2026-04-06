import asyncio
import os
import sys
from datetime import datetime

# Path setup
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.application.audit_service import AuditService
from auditor.domain.violation import Violation, ImpactLevel
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"
SESSION_ID = "e08ff6ef-cb4b-43b8-b85b-f1f4e667d108"

async def verify_synthesis():
    engine = create_async_engine(DATABASE_URL)
    
    async with AsyncSession(engine) as db_session:
        # Fetch violations directly from database records to ensure we test existing data
        v_stmt = select(ViolationModel).where(ViolationModel.session_id == SESSION_ID)
        v_res = await db_session.execute(v_stmt)
        v_records = v_res.scalars().all()
        
        print(f"Loaded {len(v_records)} violations for session {SESSION_ID}")
        
        # Convert to domain objects for synthesis engine
        domain_violations = []
        for vr in v_records:
            # Reconstruct the Violation domain object
            domain_violations.append(Violation(
                rule_id=vr.id, # The rule_id/rule_id field
                session_id=vr.session_id,
                impact=vr.impact, # it is already an enum if we use SQLModel correctly or we map it
                description=vr.description,
                help_url=vr.help_url,
                selector=vr.selector,
                nodes=vr.nodes or [],
                tags=vr.tags or []
            ))

        # Initialize AuditService and generate plan
        service = AuditService(None, None)
        plan = service._generate_remediation_plan(domain_violations)
        
        # Export Plan
        output_path = f"reports/exports/remediation_VERIFIED_{SESSION_ID}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(plan)
            
        print(f"Verified Remediation Plan exported to: {output_path}")

if __name__ == "__main__":
    asyncio.run(verify_synthesis())

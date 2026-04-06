import asyncio
import os
import sys
from sqlalchemy.future import select
from sqlmodel import Session, create_engine
from auditor.infrastructure.persistence_models import AuditSessionModel

# IDE PATH RECONCILIATION
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if _root not in sys.path:
    sys.path.insert(0, _root)

db_path = r"f:\Projects\Web Accesibility Auditor\reports\data\audit_results.db"
sqlite_url = f"sqlite:///{db_path}"
engine = create_engine(sqlite_url)

with Session(engine) as session:
    stmt = select(AuditSessionModel).order_by(AuditSessionModel.started_at.desc()).limit(1)
    record = session.exec(stmt).first()
    if record:
        print(f"Session ID: {record.id}")
        print(f"Target: {record.target_url}")
        print(f"Status: {record.status}")
        print(f"Focus Path Data: {record.focus_path[:2] if record.focus_path else 'EMPTY'}")
        print(f"ARIA Events Data: {record.aria_events[:2] if record.aria_events else 'EMPTY'}")
        print(f"Violation Count: {len(record.violations) if record.violations else 0}")
    else:
        print("No sessions found.")

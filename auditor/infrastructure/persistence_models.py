import os
import sys

# PATH RECONCILIATION: Explicit search root hinting for IDE static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.models import AuditTarget, DomainStatus
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

Base = declarative_base()

class AuditSessionModel(Base):
    __tablename__ = "audit_sessions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    target_url = Column(String, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.CREATED)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(String)
    
    violations = relationship("ViolationModel", back_populates="session")

class ViolationModel(Base):
    __tablename__ = "violations"
    
    id = Column(String, primary_key=True)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("audit_sessions.id"), primary_key=True)
    impact = Column(String)
    description = Column(String)
    help_url = Column(String)
    selector = Column(String)
    nodes = Column(JSON)
    tags = Column(JSON)
    
    session = relationship("AuditSessionModel", back_populates="violations")

class TargetModel(Base):
    __tablename__ = "targets"
    id = Column(String(36), primary_key=True)
    url = Column(String(512), nullable=False)
    status = Column(Enum(DomainStatus), default=DomainStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    last_audit_at = Column(DateTime, nullable=True)
    frequency_hours = Column(JSON)

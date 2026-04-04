import os
import sys

# ENGINE PATH RECONCILIATION: Ensuring import stability for external scripts
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON, String, DateTime

from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.models import AuditTarget, DomainStatus

class AuditSessionModel(SQLModel, table=True):
    __tablename__ = "audit_sessions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    target_url: str = Field(index=True)
    status: SessionStatus = Field(default=SessionStatus.CREATED)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    violations: List["ViolationModel"] = Relationship(back_populates="session")

class ViolationModel(SQLModel, table=True):
    __tablename__ = "violations"
    
    id: str = Field(primary_key=True)
    session_id: UUID = Field(foreign_key="audit_sessions.id", primary_key=True)
    impact: str
    description: str
    help_url: str
    selector: Optional[str] = None
    nodes: Dict[str, Any] = Field(sa_column=Column(JSON))
    tags: List[str] = Field(sa_column=Column(JSON))
    
    session: Optional[AuditSessionModel] = Relationship(back_populates="violations")

class TargetModel(SQLModel, table=True):
    __tablename__ = "targets"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    url: str = Field(index=True)
    status: DomainStatus = Field(default=DomainStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    last_audit_at: Optional[datetime] = None
    frequency_hours: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))

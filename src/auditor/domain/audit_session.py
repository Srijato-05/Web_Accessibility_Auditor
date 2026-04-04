from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Any, Dict
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from auditor.domain.violation import Violation

class SessionStatus(Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AuditSession:
    """Aggregate Root for an Accessibility Audit Session."""
    target_url: str
    id: UUID = field(default_factory=uuid4)
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    violations: List[Violation] = field(default_factory=list)
    
    # Phase VII: Forensic Metadata
    focus_path: List[Dict[str, Any]] = field(default_factory=list)
    aria_events: List[Dict[str, Any]] = field(default_factory=list)

    def start(self):
        if self.status != SessionStatus.CREATED:
            raise ValueError(f"Cannot start session in status: {self.status}")
        now = datetime.now()
        self.status = SessionStatus.IN_PROGRESS
        self.started_at = now
        self.updated_at = now

    def complete(self):
        if self.status != SessionStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete session in status: {self.status}")
        now = datetime.now()
        self.status = SessionStatus.COMPLETED
        self.completed_at = now
        self.updated_at = now

    def fail(self, error: str):
        self.status = SessionStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.now()

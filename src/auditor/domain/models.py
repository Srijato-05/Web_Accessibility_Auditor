from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional, Dict, Any

class DomainStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CRAWLING = "crawling"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class AuditTarget:
    """Entity representing a domain under autonomous surveillance."""
    url: str
    id: UUID = field(default_factory=uuid4)
    status: DomainStatus = DomainStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_audit_at: Optional[datetime] = None
    frequency_hours: int = 24 # DEFAULT: Re-audit once a day
    priority: int = 3  # Priority level (1=highest, 5=lowest)
    retry_count: int = 0
    last_error: Optional[str] = None
    scan_profile: Dict[str, Any] = field(default_factory=dict)

    def mark_crawling(self):
        self.status = DomainStatus.CRAWLING
        self.last_error = None

    def mark_active(self):
        self.status = DomainStatus.ACTIVE
        self.last_audit_at = datetime.now()
        self.retry_count = 0
        self.last_error = None

    def mark_failed(self, reason: str):
        self.status = DomainStatus.FAILED
        self.retry_count += 1
        self.last_error = reason

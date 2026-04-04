from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from auditor.domain.audit_session import AuditSession
from auditor.domain.violation import Violation

class IBrowserEngine(ABC):
    """Interface for the browser automation engine."""
    @abstractmethod
    async def scan_url(self, url: str) -> List[Violation]:
        pass

class IAuditRepository(ABC):
    """Interface for persisting audit data."""
    @abstractmethod
    async def save_session(self, session: AuditSession) -> None:
        pass

    @abstractmethod
    async def get_session(self, session_id: UUID) -> AuditSession:
        pass

    @abstractmethod
    async def save_violations(self, violations: List[Violation]) -> None:
        pass
    @abstractmethod
    async def list_recent_sessions(self, limit: int) -> List[AuditSession]:
        pass

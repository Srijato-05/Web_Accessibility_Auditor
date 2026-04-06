from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from uuid import UUID
from auditor.domain.audit_session import AuditSession
from auditor.domain.violation import Violation

if TYPE_CHECKING:
    from auditor.domain.agent_finding import AgentFinding
    from auditor.infrastructure.data_extractor import PageData


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


class IAccessibilityAgent(ABC):
    """Interface for disability-specific accessibility agents."""

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique identifier for this agent (e.g. 'visual', 'motor')."""
        pass

    @abstractmethod
    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Analyze extracted page data and return structured findings."""
        pass

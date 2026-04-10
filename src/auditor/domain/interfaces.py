import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from abc import ABC, abstractmethod
from typing import List, Protocol, runtime_checkable
from uuid import UUID
from auditor.domain.audit_session import AuditSession # type: ignore
from auditor.domain.violation import Violation # type: ignore

# --- [ NEW AGENT INFRASTRUCTURE ] ---
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from auditor.infrastructure.data_extractor import PageData # type: ignore
    from auditor.domain.agent_finding import AgentFinding # type: ignore

class IBrowserEngine(ABC):
    """Interface for the browser automation engine."""
    @abstractmethod
    async def scan_url(self, url: str) -> List[Violation]:
        return []

@runtime_checkable
class IAccessibilityAgent(Protocol):
    """Interface for specialized accessibility analysis agents."""
    @property
    def agent_name(self) -> str:
        ...

    async def analyze(self, page_data: "PageData") -> List["AgentFinding"]:
        ...

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
        return []

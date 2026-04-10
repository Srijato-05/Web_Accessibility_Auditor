import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from abc import ABC, abstractmethod
from typing import List
from auditor.domain.models import AuditTarget # type: ignore

class ITargetRepository(ABC):
    """Port for managing the registration and tracking of monitored domains."""
    
    @abstractmethod
    async def add_domain(self, domain: AuditTarget) -> None:
        pass

    @abstractmethod
    async def get_active_domains(self) -> List[AuditTarget]:
        return []

    @abstractmethod
    async def update_domain(self, domain: AuditTarget) -> None:
        pass

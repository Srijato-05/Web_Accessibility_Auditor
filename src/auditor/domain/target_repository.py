from abc import ABC, abstractmethod
from typing import List
from .models import AuditTarget

class ITargetRepository(ABC):
    """Port for managing the registration and tracking of monitored domains."""
    
    @abstractmethod
    async def add_domain(self, domain: AuditTarget) -> None:
        pass

    @abstractmethod
    async def get_active_domains(self) -> List[AuditTarget]:
        pass

    @abstractmethod
    async def update_domain(self, domain: AuditTarget) -> None:
        pass

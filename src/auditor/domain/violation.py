from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

class ImpactLevel(Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"

@dataclass(frozen=True)
class Violation:
    """Value Object / Entity representing a specific accessibility violation."""
    rule_id: str  # axe-core rule id
    impact: ImpactLevel
    description: str
    help_url: str
    selector: str
    nodes: List[Dict[str, Any]]
    tags: List[str]
    session_id: UUID

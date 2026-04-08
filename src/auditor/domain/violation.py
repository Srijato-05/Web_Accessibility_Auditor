from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

class ImpactLevel(Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"

@dataclass
class Violation:
    """Value Object / Entity representing a specific accessibility violation."""
    rule_id: str  # axe-core rule id
    impact: ImpactLevel
    description: str
    help_url: str = ""
    selector: str = ""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    session_id: Optional[UUID] = None

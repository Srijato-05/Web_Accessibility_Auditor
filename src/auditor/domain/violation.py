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
    
    # Advanced Forensics (Phase XII)
    agent: str = "axe"                   # axe, visual, motor, cognitive, neural
    compliance_level: Optional[str] = None # Below A, A, AA, AAA
    category: Optional[str] = None        # Perceivable, Operable, etc.
    severity_matrix: Optional[str] = None  # e.g., "Critical (Business Risk)"
    url: Optional[str] = None             # Source URL for crawler missions

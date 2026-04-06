"""
DOMAIN MODEL: AGENT FINDING
============================

Structured output from accessibility agents. Each finding represents a single
WCAG violation detected by a specialized agent using deterministic rules.

Findings are NOT persisted to the database. They are returned as structured
JSON for reporting and downstream consumption only.
"""

from dataclasses import dataclass
from typing import Any, Dict
from uuid import UUID


@dataclass(frozen=True)
class AgentFinding:
    """Structured output from an accessibility agent."""

    agent: str
    violation_type: str
    guideline: str
    element: str
    selector: str
    issue: str
    impact: str
    fix: str
    confidence: float
    source: str
    wcag_criterion: str
    session_id: UUID

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the structured JSON output format."""
        return {
            "agent": self.agent,
            "violation": self.violation_type,
            "guideline": self.guideline,
            "element": self.element,
            "selector": self.selector,
            "issue": self.issue,
            "impact": self.impact,
            "fix": self.fix,
            "confidence": self.confidence,
            "source": self.source,
            "wcag_criterion": self.wcag_criterion,
            "session_id": str(self.session_id),
        }

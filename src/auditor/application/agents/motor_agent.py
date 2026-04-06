"""
MOTOR AGENT
============
Analyzes targets and keyboard patterns for physical accessibility issues.
WCAG Focus: 2.1.1 Keyboard, 2.5.5 Target Size.
"""

from typing import List
from auditor.domain.agent_finding import AgentFinding
from auditor.infrastructure.data_extractor import PageData
from auditor.domain.interfaces import IAccessibilityAgent
from auditor.application.agents.rules.motor_rules import is_target_too_small
from auditor.shared.logging import auditor_logger


class MotorAgent(IAccessibilityAgent):
    """
    Accessibility agent for motor disabilities.
    Detects physical hurdles like small interactive targets.
    """

    def __init__(self) -> None:
        self.logger = auditor_logger.getChild("Agent.Motor")

    @property
    def agent_name(self) -> str:
        return "motor"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Performs Motor accessibility analysis using deterministic rules."""
        self.logger.info(f"Motor Agent analyzing: {page_data.url}")
        findings = []

        # Check ALL Links for Target Size (WCAG G44)
        for i, link in enumerate(page_data.links):
            if i < 5:
                self.logger.info(f"DEBUG: Link {i} bbox: {link.bounding_box}")
            if is_target_too_small(link.bounding_box):
                findings.append(AgentFinding(
                    agent="motor",
                    violation_type="target_size",
                    guideline="G44",
                    element=link.html,
                    selector=link.selector,
                    issue="Clickable target (link) is too small (less than 44x44px).",
                    impact="Users with motor disabilities (e.g. tremors, limited dexterity) will find this difficult to click/tap accurately.",
                    fix="Increase the padding or dimensions (width/height) to at least 44px.",
                    confidence=0.90,
                    source="rule",
                    wcag_criterion="2.5.5",
                    session_id=str(page_data.session_id)
                ))

        # Check Form Elements (Inputs/Buttons) for Target Size
        for form in page_data.form_elements:
            if is_target_too_small(form.bounding_box):
                findings.append(AgentFinding(
                    agent="motor",
                    violation_type="target_size",
                    guideline="G44",
                    element=form.html,
                    selector=form.selector,
                    issue="Interactive input/button is too small (less than 44x44px).",
                    impact="Users with motor impairments may accidentally click outside this field or target.",
                    fix="Ensure the height and width of the interactive area are at least 44px.",
                    confidence=0.90,
                    source="rule",
                    wcag_criterion="2.5.5",
                    session_id=str(page_data.session_id)
                ))

        return findings

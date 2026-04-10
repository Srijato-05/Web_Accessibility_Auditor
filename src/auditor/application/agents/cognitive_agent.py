"""
COGNITIVE AGENT
================
Analyzes the clarity and predictability of the interface.
WCAG Focus: 3.3.2 Labels, 2.4.4 Link Purpose.
"""

import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List
from auditor.domain.agent_finding import AgentFinding # type: ignore
from auditor.infrastructure.data_extractor import PageData # type: ignore
from auditor.domain.interfaces import IAccessibilityAgent # type: ignore
from auditor.application.agents.rules.cognitive_rules import is_ambiguous_link, is_missing_label_logic # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore


class CognitiveAgent(IAccessibilityAgent):
    """
    Accessibility agent for cognitive disabilities.
    Detects barriers like ambiguous links and missing form labels.
    """

    def __init__(self) -> None:
        self.logger = auditor_logger.getChild("Agent.Cognitive")

    @property
    def agent_name(self) -> str:
        return "cognitive"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Performs Cognitive accessibility analysis using deterministic rules."""
        self.logger.info(f"Cognitive Agent analyzing: {page_data.url}")
        findings = []

        # Check Links for Ambiguous Text (WCAG G91)
        for i, link in enumerate(page_data.links):
            if i < 5:
                self.logger.info(f"DEBUG: Link {i} text: '{link.text}'")
            if is_ambiguous_link(link.text):
                findings.append(AgentFinding(
                    agent="cognitive",
                    violation_type="predictability",
                    guideline="G91",
                    element=link.html,
                    selector=link.selector,
                    issue=f"Link text is generic ('{link.text}') and lacks context.",
                    impact="Users with cognitive disabilities may find it hard to predict where this link leads.",
                    fix=f"Use descriptive link text instead of just '{link.text}'.",
                    confidence=0.85,
                    source="rule",
                    wcag_criterion="2.4.4",
                    session_id=str(page_data.session_id)
                ))

        # Check Form Elements for Missing Labels (WCAG G131)
        for form in page_data.form_elements:
            if is_missing_label_logic(form.attributes, form.text):
                findings.append(AgentFinding(
                    agent="cognitive",
                    violation_type="guidance",
                    guideline="G131",
                    element=form.html,
                    selector=form.selector,
                    issue="Form input is missing a visible label or clear programmatic description.",
                    impact="Users with cognitive impairments or memory issues may forget the purpose of this field.",
                    fix="Add a <label> element or an aria-label/title describing the input's purpose.",
                    confidence=0.95,
                    source="rule",
                    wcag_criterion="3.3.2",
                    session_id=str(page_data.session_id)
                ))

        return findings

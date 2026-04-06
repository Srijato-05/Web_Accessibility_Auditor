"""
AGENT OUTPUT VALIDATORS
========================

Schema validation for AgentFinding outputs. Ensures every finding has
all required fields, valid ranges, and known agent names before being
returned to the caller.
"""

from typing import List, Optional
from auditor.domain.agent_finding import AgentFinding
from auditor.shared.logging import auditor_logger

logger = auditor_logger.getChild("AgentValidator")

VALID_AGENTS = {"visual", "motor", "cognitive", "neural"}
VALID_SOURCES = {"rule", "ml"}


def validate_finding(finding: AgentFinding) -> Optional[str]:
    """
    Validate a single AgentFinding.
    Returns None if valid, or an error message string if invalid.
    """
    if finding.agent not in VALID_AGENTS:
        return f"Unknown agent: '{finding.agent}'"

    if finding.source not in VALID_SOURCES:
        return f"Unknown source: '{finding.source}'"

    if not 0.0 <= finding.confidence <= 1.0:
        return f"Confidence out of range: {finding.confidence}"

    if not finding.guideline:
        return "Missing guideline"

    if not finding.issue:
        return "Missing issue description"

    if not finding.selector:
        return "Missing selector"

    if not finding.impact:
        return "Missing impact description"

    return None


def validate_batch(findings: List[AgentFinding]) -> List[AgentFinding]:
    """
    Validate a batch of findings. Returns only valid findings.
    Invalid findings are logged.
    """
    valid = []
    for f in findings:
        error = validate_finding(f)
        if error is None:
            valid.append(f)
        else:
            logger.warning(f"Validation failed for {f.agent}/{f.guideline}: {error}")
            
    return valid

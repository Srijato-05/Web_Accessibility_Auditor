import os
import sys

# IDE PATH RECONCILIATION: Ensuring import stability for external scripts
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List, Optional, Dict
from auditor.domain.violation import ImpactLevel # type: ignore

class ComplianceMapper:
    """
    Forensic engine to map raw engine tags to high-level compliance frameworks.
    """

    @staticmethod
    def get_compliance_level(tags: List[str], impact: ImpactLevel) -> str:
        """
        Derives WCAG compliance level (Below A, A, AA, AAA) from tags and impact.
        'Below A' represents critical mission-blocking failures of Level A criteria.
        """
        val = impact.value if hasattr(impact, 'value') else str(impact).lower()
        
        is_level_a = any("wcag2a" in t or "wcag21a" in t for t in tags)
        
        if is_level_a and val == "critical":
            return "Below A"
            
        if any("wcag2aaa" in t or "wcag21aaa" in t for t in tags):
            return "AAA"
        if any("wcag2aa" in t or "wcag21aa" in t or "wcag22aa" in t for t in tags):
            return "AA"
        if is_level_a:
            return "A"
            
        return "Non-Standard"

    @staticmethod
    def get_category(tags: List[str]) -> str:
        """Maps axe-core categories to WCAG principles (POUR)."""
        # Perceivable
        if any(t in tags for t in ["cat.color", "cat.contrast", "cat.text-alternatives", "cat.sensory-and-visual-cues", "cat.time-and-media"]):
            return "Perceivable"
        # Operable
        if any(t in tags for t in ["cat.keyboard", "cat.labels", "cat.navigation", "cat.structure", "cat.language"]):
            return "Operable"
        # Understandable
        if any(t in tags for t in ["cat.name-role-value", "cat.forms"]):
            return "Understandable"
        # Robust
        if any(t in tags for t in ["cat.aria", "cat.parsing"]):
            return "Robust"
            
        return "General Accessibility"

    @staticmethod
    def get_severity_matrix(impact: ImpactLevel) -> str:
        """Transforms impact levels into a multi-dimensional severity matrix descriptor."""
        val = impact.value if hasattr(impact, 'value') else str(impact).lower()
        
        mapping = {
            "critical": "Critical (High-Friction / Legal Risk)",
            "serious": "Serious (Significant Barrier)",
            "moderate": "Moderate (Inconvenience)",
            "minor": "Minor (Best Practice)"
        }
        return mapping.get(val, "Unclassified")

    @classmethod
    def enhance_violation(cls, violation_data: Dict):
        """Injects extended forensics into a raw violation data dictionary."""
        tags = violation_data.get("tags", [])
        impact_raw = violation_data.get("impact", "minor")
        
        # Determine ImpactLevel enum if possible
        try:
            impact_enum = ImpactLevel(impact_raw)
        except:
            impact_enum = ImpactLevel.MINOR

        violation_data["compliance_level"] = cls.get_compliance_level(tags, impact_enum)
        violation_data["category"] = cls.get_category(tags)
        violation_data["severity_matrix"] = cls.get_severity_matrix(impact_enum)
        
        return violation_data

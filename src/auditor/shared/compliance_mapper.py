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
    def get_category(tags: List[str], rule_id: str = "", agent: str = "") -> str:
        """Maps axe-core categories to WCAG principles (POUR)."""
        tags_lower = [str(t).lower() for t in tags]
        rule_id_lower = str(rule_id).lower()
        agent_lower = str(agent).lower()

        # 1. Check Agent Type first if it is a specific simulated agent
        if agent_lower == "visual":
            return "Perceivable"
        elif agent_lower == "motor":
            return "Operable"
        elif agent_lower == "cognitive":
            return "Understandable"
        elif agent_lower == "neural":
            return "Robust"

        # 2. Check custom heuristic rules specifically
        if "heuristic-semantic" in rule_id_lower:
            return "Understandable"
        elif "heuristic-live-reg" in rule_id_lower:
            return "Robust"
        elif "heuristic-form-grp" in rule_id_lower:
            return "Understandable"
        elif "heuristic-svg-acc" in rule_id_lower:
            return "Perceivable"
        elif "heuristic-overlap" in rule_id_lower:
            return "Perceivable"
        elif "heuristic-aria-rel" in rule_id_lower:
            return "Robust"
        elif "heuristic-target" in rule_id_lower:
            return "Operable"
        elif "heuristic-alt" in rule_id_lower:
            return "Perceivable"
        elif "heuristic-skip" in rule_id_lower:
            return "Operable"
        elif "heuristic-head" in rule_id_lower:
            return "Perceivable"
        elif "heuristic-lang" in rule_id_lower:
            return "Understandable"
        elif "heuristic-focus-trap" in rule_id_lower:
            return "Operable"

        # 3. Check tags for key indicators
        if any("color" in t or "contrast" in t or "text-alt" in t or "sensory" in t or "visual" in t for t in tags_lower):
            return "Perceivable"
        if any("keyboard" in t or "nav" in t or "focus" in t or "target" in t or "motor" in t or "pointer" in t or "input-modalities" in t for t in tags_lower):
            return "Operable"
        if any("forms" in t or "label" in t or "predict" in t or "understand" in t or "cognitive" in t or "language" in t for t in tags_lower):
            return "Understandable"
        if any("aria" in t or "parsing" in t or "neural" in t or "compatible" in t for t in tags_lower):
            return "Robust"

        # 4. Check WCAG numbers in tags (e.g. wcag143 -> 1.4.3 -> Perceivable)
        for t in tags_lower:
            if t.startswith("wcag") or "wcag-" in t:
                if t in ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag21aaa", "wcag22a", "wcag22aa", "wcag22aaa"]:
                    continue
                num_part = "".join(c for c in t if c.isdigit() or c == ".")
                if num_part:
                    if num_part.startswith("1"):
                        return "Perceivable"
                    elif num_part.startswith("2"):
                        return "Operable"
                    elif num_part.startswith("3"):
                        return "Understandable"
                    elif num_part.startswith("4"):
                        return "Robust"

        # 5. Check Rule ID substrings
        if any(x in rule_id_lower for x in ["color", "contrast", "alt", "text", "sensory", "visual", "image", "heading", "title", "media", "audio", "video"]):
            return "Perceivable"
        if any(x in rule_id_lower for x in ["keyboard", "tab", "focus", "target", "nav", "motor", "pointer", "size", "link", "bypass", "skip", "scroll"]):
            return "Operable"
        if any(x in rule_id_lower for x in ["label", "form", "predict", "cognitive", "lang", "input", "error", "valid"]):
            return "Understandable"
        if any(x in rule_id_lower for x in ["aria", "parsing", "neural", "role", "value", "id", "duplicate"]):
            return "Robust"

        # 6. Axe Category Prefixes fallback
        if any(t in tags_lower for t in ["cat.color", "cat.contrast", "cat.text-alternatives", "cat.sensory-and-visual-cues", "cat.time-and-media", "cat.semantics"]):
            return "Perceivable"
        if any(t in tags_lower for t in ["cat.keyboard", "cat.labels", "cat.navigation", "cat.structure", "cat.language", "cat.title"]):
            return "Operable"
        if any(t in tags_lower for t in ["cat.forms"]):
            return "Understandable"
        if any(t in tags_lower for t in ["cat.aria", "cat.parsing", "cat.name-role-value"]):
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
        rule_id = violation_data.get("rule_id", "")
        agent = violation_data.get("agent", "")
        
        # Determine ImpactLevel enum if possible
        try:
            impact_enum = ImpactLevel(impact_raw)
        except:
            impact_enum = ImpactLevel.MINOR

        violation_data["compliance_level"] = cls.get_compliance_level(tags, impact_enum)
        violation_data["category"] = cls.get_category(tags, rule_id, agent)
        violation_data["severity_matrix"] = cls.get_severity_matrix(impact_enum)
        
        return violation_data

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
    # Dynamic POUR Principle Mappings
    WCAG_PRINCIPLES = {
        "1": "Perceivable",
        "2": "Operable",
        "3": "Understandable",
        "4": "Robust"
    }

    # Custom Heuristic Rule Prefix/Substring Mappings
    HEURISTIC_RULES = {
        "heuristic-semantic": "Understandable",
        "heuristic-live-reg": "Robust",
        "heuristic-form-grp": "Understandable",
        "heuristic-svg-acc": "Perceivable",
        "heuristic-overlap": "Perceivable",
        "heuristic-aria-rel": "Robust",
        "heuristic-target": "Operable",
        "heuristic-alt": "Perceivable",
        "heuristic-skip": "Operable",
        "heuristic-head": "Perceivable",
        "heuristic-lang": "Understandable",
        "heuristic-focus-trap": "Operable"
    }

    # Keyword patterns for Rule IDs and Tags
    RULE_SUBSTRINGS = {
        "Perceivable": ["color", "contrast", "alt", "text", "sensory", "visual", "image", "heading", "title", "media", "audio", "video"],
        "Operable": ["keyboard", "tab", "focus", "target", "nav", "motor", "pointer", "size", "link", "bypass", "skip", "scroll"],
        "Understandable": ["label", "form", "predict", "cognitive", "lang", "input", "error", "valid"],
        "Robust": ["aria", "parsing", "neural", "role", "value", "id", "duplicate"]
    }

    # Axe category tag groupings
    # Axe category tag groupings
    AXE_CATEGORIES = {
        "Perceivable": ["cat.color", "cat.contrast", "cat.text-alternatives", "cat.sensory-and-visual-cues", "cat.time-and-media", "cat.semantics"],
        "Operable": ["cat.keyboard", "cat.navigation", "cat.title", "cat.structure"],
        "Understandable": ["cat.forms", "cat.language", "cat.labels"],
        "Robust": ["cat.aria", "cat.parsing", "cat.name-role-value"]
    }

    # Agent fallbacks
    AGENT_CATEGORIES = {
        "visual": "Perceivable",
        "motor": "Operable",
        "cognitive": "Understandable",
        "neural": "Robust"
    }

    # Severity Matrix descriptions
    SEVERITY_DESCRIPTIONS = {
        "critical": "Critical (High-Friction / Legal Risk)",
        "serious": "Serious (Significant Barrier)",
        "moderate": "Moderate (Inconvenience)",
        "minor": "Minor (Best Practice)"
    }

    # WCAG criteria to compliance level mappings
    WCAG_CRITERIA_LEVELS = {
        # Level A
        "1.1.1": "A", "1.2.1": "A", "1.2.2": "A", "1.2.3": "A", "1.3.1": "A", "1.3.2": "A", "1.3.3": "A",
        "1.4.1": "A", "1.4.2": "A", "2.1.1": "A", "2.1.2": "A", "2.1.4": "A", "2.2.1": "A", "2.2.2": "A",
        "2.3.1": "A", "2.4.1": "A", "2.4.2": "A", "2.4.3": "A", "2.4.4": "A", "2.5.1": "A", "2.5.2": "A",
        "2.5.3": "A", "2.5.4": "A", "3.1.1": "A", "3.2.1": "A", "3.2.2": "A", "3.3.1": "A", "3.3.2": "A",
        "4.1.1": "A", "4.1.2": "A",
        # Level AA
        "1.2.4": "AA", "1.2.5": "AA", "1.3.4": "AA", "1.3.5": "AA", "1.4.3": "AA", "1.4.4": "AA", "1.4.5": "AA",
        "1.4.10": "AA", "1.4.11": "AA", "1.4.12": "AA", "1.4.13": "AA", "2.4.5": "AA", "2.4.6": "AA", "2.4.7": "AA",
        "2.4.11": "AA", "2.4.12": "AA", "2.5.7": "AA", "2.5.8": "AA", "3.1.2": "AA", "3.2.3": "AA", "3.2.4": "AA",
        "3.3.3": "AA", "3.3.4": "AA", "3.3.7": "AA", "3.3.8": "AA", "4.1.3": "AA",
        # Level AAA
        "1.2.6": "AAA", "1.2.7": "AAA", "1.2.8": "AAA", "1.2.9": "AAA", "1.3.6": "AAA", "1.4.6": "AAA", "1.4.7": "AAA",
        "1.4.8": "AAA", "1.4.9": "AAA", "2.1.3": "AAA", "2.2.3": "AAA", "2.2.4": "AAA", "2.2.5": "AAA", "2.2.6": "AAA",
        "2.3.2": "AAA", "2.3.3": "AAA", "2.4.8": "AAA", "2.4.9": "AAA", "2.4.10": "AAA", "2.4.13": "AAA", "2.5.5": "AAA",
        "2.5.6": "AAA", "3.1.3": "AAA", "3.1.4": "AAA", "3.1.5": "AAA", "3.1.6": "AAA", "3.2.5": "AAA", "3.2.6": "AAA",
        "3.3.5": "AAA", "3.3.6": "AAA", "3.3.9": "AAA"
    }

    @classmethod
    def get_compliance_level(cls, tags: List[str], impact: ImpactLevel) -> str:
        """
        Derives WCAG compliance level (Below A, A, AA, AAA) from tags and impact.
        'Below A' represents critical mission-blocking failures of Level A criteria.
        """
        tags_lower = [str(t).lower() for t in tags]
        val = impact.value if hasattr(impact, 'value') else str(impact).lower()
        
        # 1. Parse WCAG criterion from tags if present (e.g. "1.3.5" or "wcag-1.3.5")
        for t in tags_lower:
            clean_tag = t.replace("wcag", "").replace("-", "").strip()
            # If it's a numeric string with dots or digits, e.g. "1.3.5" or "135"
            if clean_tag and clean_tag[0].isdigit():
                clean_tag_digits = "".join(c for c in clean_tag if c.isdigit() or c == ".")
                if clean_tag_digits in cls.WCAG_CRITERIA_LEVELS:
                    lvl = cls.WCAG_CRITERIA_LEVELS[clean_tag_digits]
                    if lvl == "A" and val == "critical":
                        return "Below A"
                    return lvl
                
                # Check for 3-digit normalized format (e.g., "135" -> "1.3.5")
                normalized = "".join(c for c in clean_tag if c.isdigit())
                if len(normalized) == 3:
                    dotted = f"{normalized[0]}.{normalized[1]}.{normalized[2]}"
                    if dotted in cls.WCAG_CRITERIA_LEVELS:
                        lvl = cls.WCAG_CRITERIA_LEVELS[dotted]
                        if lvl == "A" and val == "critical":
                            return "Below A"
                        return lvl

        # 2. Fallback to standard suffix checking
        is_level_a = any("wcag2a" in t or "wcag21a" in t for t in tags_lower)
        if is_level_a and val == "critical":
            return "Below A"
            
        if any("wcag2aaa" in t or "wcag21aaa" in t for t in tags_lower):
            return "AAA"
        if any("wcag2aa" in t or "wcag21aa" in t or "wcag22aa" in t for t in tags_lower):
            return "AA"
        if is_level_a:
            return "A"
            
        return "Non-Standard"

    @classmethod
    def get_category(cls, tags: List[str], rule_id: str = "", agent: str = "") -> str:
        """Maps axe-core categories to WCAG principles (POUR) dynamically using configuration mappings."""
        tags_lower = [str(t).lower() for t in tags]
        rule_id_lower = str(rule_id).lower()
        agent_lower = str(agent).lower()

        # 1. Check custom heuristic rules specifically
        for pattern, principle in cls.HEURISTIC_RULES.items():
            if pattern in rule_id_lower:
                return principle

        # 2. Axe Category Prefixes exact match fallback (higher precedence than substring match)
        for principle, categories in cls.AXE_CATEGORIES.items():
            if any(cat in tags_lower for cat in categories):
                return principle

        # 3. Check WCAG numbers in tags (e.g. wcag143 -> 1.4.3 -> Perceivable, or 2.5.5 -> Operable)
        for t in tags_lower:
            if t in ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag21aaa", "wcag22a", "wcag22aa", "wcag22aaa"]:
                continue
            
            # Extract clean criterion representation (remove wcag prefix)
            clean_tag = t.replace("wcag", "").replace("-", "").strip()
            if clean_tag and clean_tag[0].isdigit():
                # Filter to only numbers and dots
                clean_tag_digits = "".join(c for c in clean_tag if c.isdigit() or c == ".")
                if clean_tag_digits:
                    first_digit = clean_tag_digits[0]
                    if first_digit in cls.WCAG_PRINCIPLES:
                        return cls.WCAG_PRINCIPLES[first_digit]

        # 4. Check tags for key indicators based on substrings
        for principle, substrings in cls.RULE_SUBSTRINGS.items():
            if any(sub in t for t in tags_lower for sub in substrings):
                return principle

        # 5. Check Rule ID substrings
        for principle, substrings in cls.RULE_SUBSTRINGS.items():
            if any(sub in rule_id_lower for sub in substrings):
                return principle

        # 6. Fallback to Agent Type name if nothing else classified the issue
        if agent_lower in cls.AGENT_CATEGORIES:
            return cls.AGENT_CATEGORIES[agent_lower]
            
        return "General Accessibility"


    @classmethod
    def get_severity_matrix(cls, impact: ImpactLevel) -> str:
        """Transforms impact levels into a multi-dimensional severity matrix descriptor."""
        val = impact.value if hasattr(impact, 'value') else str(impact).lower()
        return cls.SEVERITY_DESCRIPTIONS.get(val, "Unclassified")

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

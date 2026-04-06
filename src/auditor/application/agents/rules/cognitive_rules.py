"""
COGNITIVE RULES ENGINE
=======================
Deterministic WCAG rules for clarity, predictability, and guidance.
Focus: Labels (3.3.2) and Link Purpose (2.4.4).
"""

from typing import Dict, Set

# Common ambiguous link text that provides no context
GENERIC_LINK_PATTERNS: Set[str] = {
    "click here", "read more", "more", "details", 
    "info", "here", "link", "search", "go", "submit",
    "learn more", "get started", "button", "view more",
    "discover more", "see all", "view all", "click",
}


def is_ambiguous_link(text: str) -> bool:
    """
    WCAG 2.4.4 Link Purpose (In Context).
    Flags links that don't explain where they go (e.g., "Click here").
    """
    clean_text = text.lower().strip()
    return clean_text in GENERIC_LINK_PATTERNS


def is_missing_label_logic(attributes: Dict[str, str], sibling_text: str) -> bool:
    """
    WCAG 3.3.2 Labels or Instructions.
    Checks if a form input has no visible or programmatic label.
    """
    has_aria_label = bool(attributes.get("ariaLabel", "").strip())
    has_title = bool(attributes.get("title", "").strip())
    has_placeholder = bool(attributes.get("placeholder", "").strip())
    has_visible_text = bool(sibling_text.strip())

    # If it has none of these, it's a cognitive barrier
    return not (has_aria_label or has_title or has_placeholder or has_visible_text)

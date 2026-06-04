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


import re

# HTML entities and unicode arrow patterns for cleanup
ARROW_PATTERNS = re.compile(r'&[a-z0-9#]+;|[→›»>…\-\.\(\)\[\]\{\}]')


def is_ambiguous_link(text: str) -> bool:
    """
    WCAG 2.4.4 Link Purpose (In Context).
    Flags links that don't explain where they go (e.g., "Click here", "Read more...").
    """
    if not text:
        return False
    # Clean standard punctuation, arrows, and brackets
    t_clean = ARROW_PATTERNS.sub(' ', text.lower())
    # Strip non-alphanumeric
    t_clean = re.sub(r'[^a-z0-9\s]', '', t_clean)
    # Strip trailing numbers/footnotes (e.g. "learn more 3")
    t_clean = re.sub(r'\s*\d+\s*$', '', t_clean)
    # Normalize duplicate whitespace
    t_clean = " ".join(t_clean.split())
    
    return t_clean in GENERIC_LINK_PATTERNS


def is_missing_label_logic(attributes: Dict[str, str], sibling_text: str) -> bool:
    """
    WCAG 3.3.2 Labels or Instructions.
    Checks if a form input has no visible or programmatic label.
    """
    has_aria_label = bool(attributes.get("ariaLabel", "").strip())
    has_aria_labelledby = bool(attributes.get("ariaLabelledby", "").strip())
    has_title = bool(attributes.get("title", "").strip())
    has_placeholder = bool(attributes.get("placeholder", "").strip())
    has_visible_text = bool(sibling_text.strip())

    # If it has none of these, it's a cognitive barrier
    return not (has_aria_label or has_aria_labelledby or has_title or has_placeholder or has_visible_text)


def is_missing_autocomplete(attributes: Dict[str, str]) -> bool:
    """
    WCAG 1.3.5 Identify Input Purpose (Level AA).
    Checks if personal data input fields lack an autocomplete attribute,
    which is a cognitive barrier.
    """
    input_type = attributes.get("type", "").lower()
    input_name = attributes.get("name", "").lower()
    input_id = attributes.get("id", "").lower()
    
    # We target common fields that collect personal information
    personal_keywords = [
        "email", "password", "username", "login", "phone", "tel", "address", 
        "street", "zip", "postal", "country", "card", "cc-", "fname", "lname", 
        "first-name", "last-name", "birth", "dob"
    ]
    
    is_personal = (
        input_type in ["email", "password", "tel"] or
        any(k in input_name for k in personal_keywords) or
        any(k in input_id for k in personal_keywords)
    )
    
    if is_personal:
        # Check if autocomplete is defined and non-empty
        autocomplete = attributes.get("autocomplete", "").strip()
        return not autocomplete
        
    return False


def is_justified_text(styles: Dict[str, str]) -> bool:
    """
    WCAG 1.4.8 Visual Presentation (Level AAA).
    Checks if text-align is set to 'justify', which can create reading hurdles 
    for users with cognitive/reading disabilities (e.g. dyslexia).
    """
    align = styles.get("textAlign", "").lower()
    return align == "justify"

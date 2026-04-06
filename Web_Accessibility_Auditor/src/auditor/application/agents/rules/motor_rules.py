"""
MOTOR RULES ENGINE
===================
Deterministic WCAG rules for detecting physical accessibility barriers.
Focus: Target Size (2.5.5) and Keyboard Accessibility (2.1.1).
"""

from typing import Dict


def is_target_too_small(bbox: Dict[str, float]) -> bool:
    """
    WCAG 2.5.5 Target Size (Enhanced) / 2.5.8 Target Size (Minimum).
    Checks if an interactive element is smaller than 44x44px.
    """
    width = bbox.get("width", 0)
    height = bbox.get("height", 0)
    # Only check if the element is actually visible (width/height > 0)
    return width > 0 and (width < 44 or height < 44)


def is_keyboard_trap_candidate(attributes: Dict[str, str]) -> bool:
    """
    WCAG 2.1.2 No Keyboard Trap.
    Detects if an element has attributes that might interfere with keyboard flow.
    """
    # Simple check for negative tabindex on interactive elements
    tabindex = attributes.get("tabindex", "")
    if tabindex:
        try:
            return int(tabindex) < 0
        except ValueError:
            return False
    return False

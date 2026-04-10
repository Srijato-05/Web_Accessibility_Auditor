"""
COLOR RULES ENGINE
===================

Deterministic WCAG rule functions for "Use of Color" (1.4.1) detection.
Each function takes element data and returns True if a violation is detected.

These are PURE FUNCTIONS — no I/O, no side effects, no ML.
"""

import os
import sys

# IDE PATH RECONCILIATION: Ensure internal utilities are resolvable
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import Dict, Optional, Tuple, cast
from auditor.application.agents.utils.contrast import (
    parse_rgb,
    contrast_ratio,
    meets_link_distinction,
    is_similar_color,
) # type: ignore


# Colors commonly used for error/success/warning states
STATUS_COLORS = {
    "error": [(255, 0, 0), (220, 53, 69), (239, 68, 68), (200, 0, 0)],
    "success": [(0, 128, 0), (40, 167, 69), (34, 197, 94), (0, 200, 0)],
    "warning": [(255, 165, 0), (255, 193, 7), (234, 179, 8)],
}

# CSS properties that indicate visual differentiation beyond color
VISUAL_CUE_PROPERTIES = {
    "textDecoration": ["underline", "line-through", "overline"],
    "fontWeight": ["bold", "700", "800", "900"],
    "borderBottomWidth": [],
    "outlineWidth": [],
}


def _get_rgb(styles: Dict[str, str], key: str) -> Optional[Tuple[int, int, int]]:
    """Safely extract and parse an RGB color from computed styles."""
    raw = styles.get(key, "")
    if not raw:
        return None
    return parse_rgb(raw)


def has_visual_cue_beyond_color(styles: Dict[str, str]) -> bool:
    """
    Check if an element has any visual differentiation beyond just color.

    Looks for: underline, bold, border-bottom, outline.
    """
    text_dec = styles.get("textDecoration", "").lower()
    if "underline" in text_dec or "line-through" in text_dec:
        return True

    font_weight = styles.get("fontWeight", "")
    if font_weight in ("bold", "700", "800", "900"):
        return True

    for border_key in ("borderBottomWidth", "borderBottomStyle"):
        val = styles.get(border_key, "").lower()
        if val and val not in ("0px", "none", ""):
            return True

    outline = styles.get("outlineWidth", "").lower()
    if outline and outline not in ("0px", ""):
        return True

    return False


def is_link_color_only(
    link_styles: Dict[str, str],
    parent_styles: Dict[str, str],
) -> bool:
    """
    G183: True if a link is distinguished from surrounding text ONLY by color.

    Violation when:
      - Link has no underline, border, or other visual cue
      - Link color differs from parent text color
      - Contrast ratio between link color and parent text color is < 3:1
    """
    if has_visual_cue_beyond_color(link_styles):
        return False

    link_color = _get_rgb(link_styles, "color")
    parent_color = _get_rgb(parent_styles, "color")

    if link_color is None or parent_color is None:
        return False

    if is_similar_color(link_color, parent_color):
        return False

    ratio = contrast_ratio(link_color, parent_color)
    if meets_link_distinction(ratio):
        return False

    return True


def classify_status_color(
    color: Tuple[int, int, int],
) -> Optional[str]:
    """
    Classify an RGB color as 'error', 'success', 'warning', or None.

    Uses proximity matching against known status color palettes.
    """
    for status, palette in STATUS_COLORS.items():
        for ref in palette:
            if is_similar_color(color, ref, threshold=60.0):
                return status
    return None


def is_form_error_color_only(
    element_styles: Dict[str, str],
    has_error_text: bool,
    has_aria_invalid: bool,
) -> bool:
    """
    G205: True if form error state relies only on color with no text cue.

    Violation when:
      - Element border or background uses a status color (red/green)
      - No visible error/success text message exists nearby
      - No aria-invalid attribute is set
    """
    if has_error_text or has_aria_invalid:
        return False

    for prop in ("borderColor", "borderBottomColor", "backgroundColor", "color"):
        color = _get_rgb(element_styles, prop)
        if color and classify_status_color(color) is not None:
            return True

    return False


def is_text_color_only_meaning(
    element_styles: Dict[str, str],
    parent_styles: Dict[str, str],
) -> bool:
    """
    G14/G182: True if text uses color to convey meaning without additional cues.

    Violation when:
      - Text color differs significantly from surrounding text
      - No additional visual cue (bold, icon, border) exists
    """
    if has_visual_cue_beyond_color(element_styles):
        return False

    el_color = _get_rgb(element_styles, "color")
    parent_color = _get_rgb(parent_styles, "color")

    if el_color is None or parent_color is None:
        return False

    if is_similar_color(el_color, parent_color):
        return False

    if el_color is not None and classify_status_color(el_color) is not None:
        return True

    return False


def is_image_color_only(
    has_alt: bool,
    has_aria_label: bool,
    has_figcaption: bool,
    has_title: bool,
    element_tag: str,
) -> bool:
    """
    G111: True if an image/chart likely relies only on color to convey info.

    Violation when:
      - Image or SVG has no text alternative (alt, aria-label, figcaption, title)
      - Rule-based heuristic: SVGs and canvas elements are more likely to be data charts

    Note: This is the rule-based check only. ML analysis of the actual image
    content (detecting color regions vs patterns) is a separate optional step.
    """
    has_text_alternative = has_alt or has_aria_label or has_figcaption or has_title

    if has_text_alternative:
        return False

    if element_tag.lower() in ("svg", "canvas"):
        return True

    return False

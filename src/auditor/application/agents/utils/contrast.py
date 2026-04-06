"""
WCAG CONTRAST UTILITIES
========================

Pure mathematical functions for WCAG 2.1 contrast ratio calculations.
No external dependencies — just the WCAG luminance and contrast formulas.

Reference: https://www.w3.org/WAI/WCAG21/Techniques/general/G17
"""

import re
import math
from typing import Tuple, Optional


def parse_rgb(css_color: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse a CSS color string into (R, G, B) tuple.

    Supports:
      - rgb(r, g, b)
      - rgba(r, g, b, a)
      - #RRGGBB
      - #RGB

    Returns None if the format is unrecognized.
    """
    if not css_color or not isinstance(css_color, str):
        return None

    css_color = css_color.strip().lower()

    rgb_match = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css_color
    )
    if rgb_match:
        return (
            int(rgb_match.group(1)),
            int(rgb_match.group(2)),
            int(rgb_match.group(3)),
        )

    hex_match = re.match(r"#([0-9a-f]{6})$", css_color)
    if hex_match:
        h = hex_match.group(1)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    hex3_match = re.match(r"#([0-9a-f]{3})$", css_color)
    if hex3_match:
        h = hex3_match.group(1)
        return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16))

    return None


def _linearize(channel: int) -> float:
    """Convert an 8-bit sRGB channel value to linear light."""
    s = channel / 255.0
    if s <= 0.04045:
        return s / 12.92
    return math.pow((s + 0.055) / 1.055, 2.4)


def relative_luminance(r: int, g: int, b: int) -> float:
    """
    Compute WCAG 2.1 relative luminance.

    Formula: L = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
    Reference: https://www.w3.org/WAI/GL/wiki/Relative_luminance
    """
    return (
        0.2126 * _linearize(r)
        + 0.7152 * _linearize(g)
        + 0.0722 * _linearize(b)
    )


def contrast_ratio(
    color1: Tuple[int, int, int], color2: Tuple[int, int, int]
) -> float:
    """
    Compute WCAG contrast ratio between two RGB colors.

    Returns a value between 1.0 (identical) and 21.0 (black vs white).
    """
    l1 = relative_luminance(*color1)
    l2 = relative_luminance(*color2)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


def meets_aa_normal(ratio: float) -> bool:
    """WCAG AA for normal text: contrast ratio >= 4.5:1."""
    return ratio >= 4.5


def meets_aa_large(ratio: float) -> bool:
    """WCAG AA for large text (18pt+ or 14pt bold): contrast ratio >= 3.0:1."""
    return ratio >= 3.0


def meets_link_distinction(ratio: float) -> bool:
    """G183: Links must have >= 3:1 contrast ratio with surrounding text."""
    return ratio >= 3.0


def color_distance(
    c1: Tuple[int, int, int], c2: Tuple[int, int, int]
) -> float:
    """Euclidean distance in RGB space. Useful for quick similarity checks."""
    return math.sqrt(
        (c1[0] - c2[0]) ** 2
        + (c1[1] - c2[1]) ** 2
        + (c1[2] - c2[2]) ** 2
    )


def is_similar_color(
    c1: Tuple[int, int, int], c2: Tuple[int, int, int], threshold: float = 30.0
) -> bool:
    """True if two colors are visually similar (close in RGB space)."""
    return color_distance(c1, c2) < threshold

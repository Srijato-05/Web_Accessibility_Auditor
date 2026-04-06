"""
VISUAL AGENT — Fully Implemented
==================================

Targets: Visual disabilities (color blindness, low vision)
WCAG Focus: 1.4.1 Use of Color

Implements detection for five WCAG techniques:
  G183 — Links identified only by color
  G14  — Color-only information without text
  G182 — Text color meaning without visual cues
  G205 — Form states relying only on color
  G111 — Images/charts using only color
"""

from typing import List
from uuid import UUID

from auditor.domain.interfaces import IAccessibilityAgent
from auditor.domain.agent_finding import AgentFinding
from auditor.infrastructure.data_extractor import PageData, ElementData
from auditor.application.agents.rules.color_rules import (
    is_link_color_only,
    is_form_error_color_only,
    is_text_color_only_meaning,
    is_image_color_only,
    classify_status_color,
    _get_rgb,
)
from auditor.shared.logging import auditor_logger


class VisualAgent(IAccessibilityAgent):
    """
    Accessibility agent for visual disabilities.

    Detects WCAG 1.4.1 "Use of Color" violations using deterministic rules.
    ML is NOT used for detection — only rule-based checks.
    """

    def __init__(self) -> None:
        self.logger = auditor_logger.getChild("Agent.Visual")

    @property
    def agent_name(self) -> str:
        return "visual"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Run all visual accessibility checks against the extracted page data."""
        self.logger.info(f"Visual Agent analyzing: {page_data.url}")
        findings: List[AgentFinding] = []

        findings.extend(self._check_links_g183(page_data))
        findings.extend(self._check_form_states_g205(page_data))
        findings.extend(self._check_text_cues_g14_g182(page_data))
        findings.extend(self._check_image_color_g111(page_data))

        self.logger.info(f"Visual Agent complete: {len(findings)} findings")
        return findings

    # ------------------------------------------------------------------
    # G183: Links must not be identified by color alone
    # ------------------------------------------------------------------

    def _check_links_g183(self, page_data: PageData) -> List[AgentFinding]:
        """
        G183: Links that differ from surrounding text ONLY by color
        must have >= 3:1 contrast ratio AND additional visual cues.
        """
        findings: List[AgentFinding] = []

        for link in page_data.links:
            if not link.text.strip():
                continue

            if link.computed_styles.get("display", "") == "none":
                continue

            if is_link_color_only(link.computed_styles, link.parent_styles):
                findings.append(AgentFinding(
                    agent=self.agent_name,
                    violation_type="use_of_color",
                    guideline="G183",
                    element=link.html,
                    selector=link.selector,
                    issue=(
                        "Link is identified only by color. No underline, border, "
                        "or other visual indicator distinguishes it from surrounding text."
                    ),
                    impact="Colorblind users cannot distinguish this link from normal text",
                    fix=(
                        "Add text-decoration: underline, a border-bottom, "
                        "or another non-color visual cue to this link."
                    ),
                    confidence=0.92,
                    source="rule",
                    wcag_criterion="1.4.1",
                    session_id=page_data.session_id,
                ))

        self.logger.debug(f"G183 links check: {len(findings)} violations")
        return findings

    # ------------------------------------------------------------------
    # G205: Form error/success must not rely only on color
    # ------------------------------------------------------------------

    def _check_form_states_g205(self, page_data: PageData) -> List[AgentFinding]:
        """
        G205: Form validation states (error borders, success colors)
        must include a text message, not just a color change.
        """
        findings: List[AgentFinding] = []

        ERROR_CLASS_KEYWORDS = {"error", "invalid", "danger", "fail"}
        SUCCESS_CLASS_KEYWORDS = {"success", "valid", "ok", "pass"}

        for form_el in page_data.form_elements:
            has_aria_invalid = form_el.attributes.get("ariaInvalid", "") == "true"

            sibling_text = form_el.text.lower().strip()
            has_error_text = any(
                word in sibling_text
                for word in ("error", "invalid", "required", "please", "must", "wrong", "fail")
            )

            class_name = form_el.attributes.get("className", "").lower()
            has_status_class = any(
                kw in class_name
                for kw in ERROR_CLASS_KEYWORDS | SUCCESS_CLASS_KEYWORDS
            )

            is_color_only = is_form_error_color_only(
                form_el.computed_styles,
                has_error_text,
                has_aria_invalid,
            )

            if is_color_only or (has_status_class and not has_error_text and not has_aria_invalid):
                status = None
                for prop in ("borderColor", "borderBottomColor", "color"):
                    color = _get_rgb(form_el.computed_styles, prop)
                    if color:
                        status = classify_status_color(color)
                        if status:
                            break

                state_label = status or "status"
                findings.append(AgentFinding(
                    agent=self.agent_name,
                    violation_type="use_of_color",
                    guideline="G205",
                    element=form_el.html,
                    selector=form_el.selector,
                    issue=(
                        f"Form field indicates '{state_label}' state using color alone. "
                        f"No visible text message accompanies the color change."
                    ),
                    impact=(
                        "Users with color vision deficiencies cannot perceive "
                        "the error/success state of this form field"
                    ),
                    fix=(
                        "Add a visible text label (e.g., 'This field is required') "
                        "alongside the color indicator, and set aria-invalid='true' for errors."
                    ),
                    confidence=0.88,
                    source="rule",
                    wcag_criterion="1.4.1",
                    session_id=page_data.session_id,
                ))

        self.logger.debug(f"G205 form states check: {len(findings)} violations")
        return findings

    # ------------------------------------------------------------------
    # G14 / G182: Text color meaning without additional visual cues
    # ------------------------------------------------------------------

    def _check_text_cues_g14_g182(self, page_data: PageData) -> List[AgentFinding]:
        """
        G14/G182: Text that uses color to convey meaning (e.g., red for required,
        green for complete) must have additional visual cues like icons or bold text.
        """
        findings: List[AgentFinding] = []

        STATUS_CLASS_HINTS = {
            "danger", "error", "warning", "success", "alert",
            "text-danger", "text-success", "text-warning", "text-error",
            "status", "required", "mandatory",
        }

        for el in page_data.text_elements:
            if not el.text.strip():
                continue

            if el.computed_styles.get("display", "") == "none":
                continue

            class_name = el.attributes.get("className", "").lower()
            has_status_class = any(kw in class_name for kw in STATUS_CLASS_HINTS)

            is_color_meaning = is_text_color_only_meaning(
                el.computed_styles, el.parent_styles
            )

            if is_color_meaning or (has_status_class and not _has_icon_or_pattern(el)):
                guideline = "G14" if not has_status_class else "G182"
                findings.append(AgentFinding(
                    agent=self.agent_name,
                    violation_type="use_of_color",
                    guideline=guideline,
                    element=el.html,
                    selector=el.selector,
                    issue=(
                        "Text uses color difference to convey meaning "
                        "without an additional visual cue (icon, bold, pattern)."
                    ),
                    impact=(
                        "Users who cannot perceive color differences will "
                        "miss the information this color is intended to communicate"
                    ),
                    fix=(
                        "Add an icon (✓, ✗, ⚠), bold styling, or descriptive text "
                        "prefix alongside the color indicator."
                    ),
                    confidence=0.85,
                    source="rule",
                    wcag_criterion="1.4.1",
                    session_id=page_data.session_id,
                ))

        self.logger.debug(f"G14/G182 text cues check: {len(findings)} violations")
        return findings

    # ------------------------------------------------------------------
    # G111: Images/charts must not rely only on color
    # ------------------------------------------------------------------

    def _check_image_color_g111(self, page_data: PageData) -> List[AgentFinding]:
        """
        G111: Charts, graphs, and informational images must use patterns
        or text labels in addition to color.
        """
        findings: List[AgentFinding] = []

        for img in page_data.images:
            if img.attributes.get("ariaHidden", "") == "true":
                continue

            box = img.bounding_box
            if box.get("width", 0) < 20 or box.get("height", 0) < 20:
                continue

            has_alt = bool(img.attributes.get("alt", "").strip())
            has_aria_label = bool(img.attributes.get("ariaLabel", "").strip())
            has_figcaption = img.attributes.get("hasFigcaption", "") == "true"
            has_title = bool(img.attributes.get("title", "").strip())

            if is_image_color_only(
                has_alt, has_aria_label, has_figcaption, has_title, img.tag
            ):
                findings.append(AgentFinding(
                    agent=self.agent_name,
                    violation_type="use_of_color",
                    guideline="G111",
                    element=img.html,
                    selector=img.selector,
                    issue=(
                        f"{'SVG/Canvas' if img.tag in ('svg', 'canvas') else 'Image'} "
                        f"element may convey information using color alone "
                        f"without text labels or patterns."
                    ),
                    impact=(
                        "Colorblind users cannot distinguish meaning from "
                        "color-coded regions in charts or informational graphics"
                    ),
                    fix=(
                        "Add descriptive alt text, aria-label, or a figcaption. "
                        "For charts, use patterns/textures in addition to colors."
                    ),
                    confidence=0.78 if img.tag in ("svg", "canvas") else 0.65,
                    source="rule",
                    wcag_criterion="1.4.1",
                    session_id=page_data.session_id,
                ))

        self.logger.debug(f"G111 image color check: {len(findings)} violations")
        return findings


def _has_icon_or_pattern(el: ElementData) -> bool:
    """Heuristic: check if an element's HTML contains icon-like content."""
    html = el.html.lower()
    icon_indicators = [
        "<svg", "<i ", "<i>", "fa-", "icon", "material-icons",
        "glyphicon", "bi-", "feather-", "✓", "✗", "⚠", "❌", "✅",
        "&#x", "&#10003", "&#10007",
    ]
    return any(indicator in html for indicator in icon_indicators)

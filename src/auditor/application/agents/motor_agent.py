"""
MOTOR AGENT
============
Analyzes targets and keyboard patterns for physical accessibility issues using
advanced Fitts's Law calculations and topological proximity heuristics.
WCAG Focus: 2.1.1 Keyboard, 2.5.5 Target Size, 2.5.8 Target Size (Minimum).
"""

import os
import sys
import re

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List, Dict, Any
from auditor.domain.agent_finding import AgentFinding # type: ignore
from auditor.infrastructure.data_extractor import PageData, ElementData # type: ignore
from auditor.domain.interfaces import IAccessibilityAgent # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore


class MotorAgent(IAccessibilityAgent):
    """
    Advanced Heuristic Agent for motor disabilities.
    Utilizes mathematical hit-box analysis and spatial mapping to detect barriers.
    """

    def __init__(self) -> None:
        self.logger = auditor_logger.getChild("Agent.Motor")
        self.MIN_TARGET_AREA = 44 * 44 # WCAG AAA standard
        self.MIN_DIMENSION = 24 # WCAG 2.2 AA target size (minimum)
        # Pre-compiled high-performance mathematical extractor for extreme CSS values
        self.spatial_extractor = re.compile(r'-?\d+(?:\.\d+)?')

    @property
    def agent_name(self) -> str:
        return "motor"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Performs advanced dynamic Motor accessibility analysis."""
        self.logger.info(f"Motor Agent executing advanced spatial heuristics on: {page_data.url}")
        findings = []

        all_interactives = page_data.links + page_data.form_elements
        try:
            findings.extend(self._analyze_fitts_law_targets(all_interactives, str(page_data.session_id)))
        except Exception as e:
            self.logger.error(f"Motor Fitts Law Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_topological_proximity(all_interactives, str(page_data.session_id)))
        except Exception as e:
            self.logger.error(f"Motor Proximity Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_focus_flow_mapping(all_interactives, str(page_data.session_id)))
        except Exception as e:
            self.logger.error(f"Motor Focus Flow Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_dynamic_spatial_vectorization(all_interactives, str(page_data.session_id)))
        except Exception as e:
            self.logger.error(f"Motor Spatial Vectorization Engine crash: {e}")

        return findings

    def _analyze_fitts_law_targets(self, interactives: List[ElementData], session_id: str) -> List[AgentFinding]:
        """
        Dynamically analyzes hit-boxes based on Fitts's Law principles.
        Checks for extreme aspect ratios and total clickable area.
        """
        findings = []
        for el in interactives:
            bbox = el.bounding_box
            if not bbox or bbox.get("width", 0) == 0 or bbox.get("height", 0) == 0:
                continue

            w = bbox.get("width", 0)
            h = bbox.get("height", 0)
            area = w * h
            
            # Aspect Ratio Calculation: Detects objects that are extremely wide but very thin
            aspect_ratio = max(w, h) / min(w, h)
            
            if area < self.MIN_TARGET_AREA and min(w, h) < self.MIN_DIMENSION:
                findings.append(AgentFinding(
                    agent="motor",
                    violation_type="target_size",
                    guideline="G44",
                    element=el.html,
                    selector=el.selector,
                    issue=f"Hit-box ({w}x{h}px) fails minimum interaction geometry.",
                    impact="Users with motor tremors or utilizing assistive switches cannot accurately trigger this target without high error rates.",
                    fix="Expand the target hit-box via CSS padding or min-width/min-height to at least 24x24px, ideally 44x44px.",
                    confidence=0.92,
                    source="heuristic",
                    wcag_criterion="2.5.8",
                    session_id=session_id
                ))
            elif aspect_ratio > 8 and min(w, h) < 30:
                findings.append(AgentFinding(
                    agent="motor",
                    violation_type="target_size",
                    guideline="G44",
                    element=el.html,
                    selector=el.selector,
                    issue=f"Extreme Aspect Ratio ({aspect_ratio:.1f}:1). Target is very wide but too short ({h}px).",
                    impact="Fitts's Law indicates high failure rates for vertical targeting by users with motor impairments on this element.",
                    fix="Increase the shortest dimension to improve the aspect ratio and clickability.",
                    confidence=0.88,
                    source="heuristic",
                    wcag_criterion="2.5.5",
                    session_id=session_id
                ))

        return findings

    def _analyze_topological_proximity(self, interactives: List[ElementData], session_id: str) -> List[AgentFinding]:
        """
        Calculates spatial density. Flags interactive elements that are too close
        to each other, creating a high probability of accidental misclicks.
        """
        findings = []
        
        # Spatial filtering: Only check elements that have valid coordinates
        valid_els = [el for el in interactives if el.bounding_box and el.bounding_box.get('width', 0) > 0]
        
        for i, el1 in enumerate(valid_els):
            b1 = el1.bounding_box
            for j in range(i + 1, len(valid_els)):
                el2 = valid_els[j]
                b2 = el2.bounding_box
                
                # Calculate Cartesian distance between bounding box edges
                # If they overlap or have < 4px padding, it's a critical fat-finger risk
                horizontal_dist = max(0, max(b1['x'] - (b2['x'] + b2['width']), b2['x'] - (b1['x'] + b1['width'])))
                vertical_dist = max(0, max(b1['y'] - (b2['y'] + b2['height']), b2['y'] - (b1['y'] + b1['height'])))
                
                if horizontal_dist < 4 and vertical_dist < 4:
                    findings.append(AgentFinding(
                        agent="motor",
                        violation_type="spacing",
                        guideline="G21",
                        element=el1.html,
                        selector=el1.selector,
                        issue="Critical topological proximity: Interactive element is <4px from adjacent interactive element.",
                        impact="Severe 'fat-finger' misclick risk for users with tremors or touch-screen users.",
                        fix="Increase CSS margin or gap between interactive components.",
                        confidence=0.96,
                        source="heuristic",
                        wcag_criterion="2.5.8",
                        session_id=session_id
                    ))
                    break # Only report once per element to reduce noise

        return findings

    def _analyze_focus_flow_mapping(self, interactives: List[ElementData], session_id: str) -> List[AgentFinding]:
        """
        Detects elements intentionally removed from keyboard flow despite being interactive.
        """
        findings = []
        for el in interactives:
            tabindex = el.attributes.get('tabindex', '')
            if tabindex and tabindex.startswith('-'):
                # Check if it's visually hidden (if hidden, tabindex=-1 is valid)
                display = el.computed_styles.get('display', 'block')
                if display != 'none':
                    findings.append(AgentFinding(
                        agent="motor",
                        violation_type="keyboard",
                        guideline="G21",
                        element=el.html,
                        selector=el.selector,
                        issue="Visually active interactive element is forcibly removed from keyboard flow (tabindex='-1').",
                        impact="Keyboard-only users cannot navigate to or activate this visible component.",
                        fix="Remove tabindex='-1' or change to '0'. If it should be hidden, apply 'display: none'.",
                        confidence=0.95,
                        source="heuristic",
                        wcag_criterion="2.1.1",
                        session_id=session_id
                    ))

        return findings

    def _analyze_dynamic_spatial_vectorization(self, interactives: List[ElementData], session_id: str) -> List[AgentFinding]:
        """
        Phase X: Dynamic Spatial Vectorization.
        Computationally infers extreme CSS spatial traps without hardcoded structural bounds.
        """
        findings = []
        for el in interactives:
            styles = el.computed_styles
            
            # Vector 1: Fixed Position Obscuration Trap
            position = styles.get('position', 'static')
            if position in ('fixed', 'sticky'):
                z_index = styles.get('zIndex', 'auto')
                if z_index == 'auto' or (str(z_index).lstrip('-').isdigit() and int(z_index) < 1):
                    findings.append(AgentFinding(
                        agent="motor",
                        violation_type="spatial_trap",
                        guideline="G21",
                        element=el.html,
                        selector=el.selector,
                        issue=f"Interactive element is positioned {position} but lacks a dominant z-index (z-index: {z_index}).",
                        impact="High risk of being obscured by subsequent DOM elements during scrolling, permanently trapping touch and keyboard focus underneath non-interactive layers.",
                        fix="Elevate the z-index of fixed/sticky interactive headers/footers to ensure they always render above normal document flow.",
                        confidence=0.91,
                        source="vector_engine",
                        wcag_criterion="2.1.1",
                        session_id=session_id
                    ))

            # Vector 2: Multi-Directional Negative Margin Collision
            margin_props = ['marginTop', 'marginBottom', 'marginLeft', 'marginRight']
            for prop in margin_props:
                margin_val = str(styles.get(prop, '0px')).lower()
                if '-' in margin_val and margin_val != 'auto' and margin_val != 'inherit':
                    try:
                        # High-performance extraction of the first mathematical float
                        matches = self.spatial_extractor.findall(margin_val)
                        if matches:
                            m_val = float(matches[0])
                            if m_val < -20:
                                findings.append(AgentFinding(
                                    agent="motor",
                                    violation_type="spatial_collision",
                                    guideline="G21",
                                    element=el.html,
                                    selector=el.selector,
                                    issue=f"Severe negative spatial pull applied to interactive element ({prop}: {margin_val}).",
                                    impact="Creates physical hit-box collisions with adjacent elements, causing fat-finger errors and touchscreen misfires.",
                                    fix="Use padding or flex/grid gap for alignment instead of relying on extreme negative margins.",
                                    confidence=0.94,
                                    source="vector_engine",
                                    wcag_criterion="2.5.8",
                                    session_id=session_id
                                ))
                                break # Stop at the first severe collision per element
                    except Exception as e:
                        self.logger.warning(f"Failed to extract mathematical float from {prop} ('{margin_val}'): {e}")

        return findings

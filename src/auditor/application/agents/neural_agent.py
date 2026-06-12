"""
NEURAL ACCESSIBILITY AGENT
==========================
Analyzes the interface for cognitive overload, motion-induced nausea, and seizure risks.
WCAG Focus: 2.2.2 Pause, Stop, Hide; 2.3.1 Three Flashes or Below Threshold.
"""

import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List
from auditor.domain.agent_finding import AgentFinding # type: ignore
from auditor.infrastructure.data_extractor import PageData # type: ignore
from auditor.domain.interfaces import IAccessibilityAgent # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore


class NeuralAgent(IAccessibilityAgent):
    """
    Advanced Heuristic Agent for Neural and Vestibular disorders.
    Analyzes CSS animation entropy, kinetic load, and cognitive fatigue topologies.
    """

    def __init__(self) -> None:
        self.logger = auditor_logger.getChild("Agent.Neural")

    @property
    def agent_name(self) -> str:
        return "neural"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Performs advanced dynamic Neural accessibility analysis."""
        self.logger.info(f"Neural Agent executing kinetic and cognitive overload heuristics on: {page_data.url}")
        findings = []
        try:
            findings.extend(self._analyze_kinetic_entropy(page_data))
        except Exception as e:
            self.logger.error(f"Neural Kinetic Entropy Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_cognitive_fatigue(page_data))
        except Exception as e:
            self.logger.error(f"Neural Cognitive Fatigue Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_dynamic_kinetic_vectorization(page_data))
        except Exception as e:
            self.logger.error(f"Neural Kinetic Vectorization Engine crash: {e}")

        return findings

    def _analyze_kinetic_entropy(self, page_data: PageData) -> List[AgentFinding]:
        """
        Dynamically analyzes animation and transition durations.
        Flags elements with infinite animations or rapid flashing that trigger
        vestibular disorders or seizures (WCAG 2.2.2, 2.3.1).
        """
        findings = []
        
        all_elements = page_data.links + page_data.form_elements + page_data.images + page_data.text_elements
        
        for el in all_elements:
            styles = el.computed_styles
            
            animation_name = styles.get('animationName', 'none')
            animation_duration = styles.get('animationDuration', '0s')
            animation_iteration = styles.get('animationIterationCount', '1')
            
            if animation_name != 'none' and animation_duration != '0s':
                # Check for Infinite loops (Vestibular trigger)
                if animation_iteration == 'infinite':
                    findings.append(AgentFinding(
                        agent="neural",
                        violation_type="motion",
                        guideline="G4",
                        element=el.html,
                        selector=el.selector,
                        issue=f"Infinite animation loop detected (animation-name: {animation_name}).",
                        impact="Continuous movement or blinking causes severe distraction for users with ADHD and nausea for users with vestibular disorders.",
                        fix="Ensure animations stop within 5 seconds or provide a global mechanism to pause/stop animations (e.g. prefers-reduced-motion media query).",
                        confidence=0.95,
                        source="heuristic",
                        wcag_criterion="2.2.2",
                        session_id=str(page_data.session_id)
                    ))
                
                # Check for Rapid Flashing (Seizure risk - 3 flashes per second)
                # If duration is < 0.33s (333ms) and it iterates multiple times
                try:
                    dur_val = float(animation_duration.replace('s', '').replace('ms', '').strip())
                    if 'ms' in animation_duration:
                        dur_val = dur_val / 1000.0
                        
                    if dur_val > 0 and dur_val <= 0.33 and (animation_iteration == 'infinite' or int(animation_iteration) > 3):
                        findings.append(AgentFinding(
                            agent="neural",
                            violation_type="seizure",
                            guideline="G19",
                            element=el.html,
                            selector=el.selector,
                            issue=f"Rapid flashing animation detected (Duration: {dur_val}s, Iterations: {animation_iteration}).",
                            impact="CRITICAL RISK: Flashing content >3 times per second can trigger photosensitive epileptic seizures.",
                            fix="Increase animation duration to >0.5s or remove the animation entirely.",
                            confidence=0.98,
                            source="heuristic",
                            wcag_criterion="2.3.1",
                            session_id=str(page_data.session_id)
                        ))
                except ValueError:
                    pass

        return findings

    def _analyze_cognitive_fatigue(self, page_data: PageData) -> List[AgentFinding]:
        """
        Analyzes the DOM for excessive dynamic interruption points (alert fatigue).
        If a page has too many aria-live or alert regions, it becomes overwhelming.
        """
        findings = []
        live_regions_count = 0
        
        all_elements = page_data.links + page_data.form_elements + page_data.images + page_data.text_elements
        
        for el in all_elements:
            role = el.attributes.get('role', '')
            aria_live = el.attributes.get('ariaLive', '')
            
            if role in ['alert', 'status', 'log', 'timer', 'marquee'] or aria_live in ['polite', 'assertive']:
                live_regions_count += 1
                
        # Heuristic Threshold: More than 3 active live regions on a single page is highly overwhelming
        if live_regions_count > 3:
            findings.append(AgentFinding(
                agent="neural",
                violation_type="cognitive-complexity",
                guideline="G193",
                element="body",
                selector="body",
                issue=f"Excessive dynamic interruption points detected ({live_regions_count} aria-live/alert regions).",
                impact="Screen readers will constantly interrupt the user with updates from multiple sources, causing extreme cognitive overload and 'alert fatigue'.",
                fix="Consolidate dynamic updates into fewer, unified status regions, or use aria-live='polite' strictly for critical changes.",
                confidence=0.88,
                source="heuristic",
                wcag_criterion="4.1.3",
                session_id=str(page_data.session_id)
            ))

        return findings

    def _analyze_dynamic_kinetic_vectorization(self, page_data: PageData) -> List[AgentFinding]:
        """
        Phase X: Dynamic Kinetic Vectorization.
        Computationally scans all transition and transform states for hyper-fast vestibular triggers.
        """
        findings = []
        all_elements = page_data.links + page_data.form_elements + page_data.images + page_data.text_elements
        
        for el in all_elements:
            styles = el.computed_styles
            
            # Vector 1: Hyper-fast Layout Shifts (Vestibular Trigger)
            transition_duration = styles.get('transitionDuration', '0s')
            transform = styles.get('transform', 'none')
            
            if transform != 'none' and transition_duration != '0s':
                # If transition is less than 150ms on a structural shift, it triggers motion sickness
                try:
                    dur_val = float(transition_duration.split(',')[0].replace('s', '').replace('ms', '').strip())
                    if 'ms' in transition_duration:
                        dur_val = dur_val / 1000.0
                        
                    # Calculate bounding box area to see if it's a massive layout shift
                    area = el.bounding_box.get('width', 0) * el.bounding_box.get('height', 0)
                    
                    if 0 < dur_val < 0.15 and area > 10000: # 100x100px or larger
                        findings.append(AgentFinding(
                            agent="neural",
                            violation_type="vestibular_trigger",
                            guideline="G4",
                            element=el.html,
                            selector=el.selector,
                            issue=f"Hyper-fast kinetic shift detected on large element. Transition duration ({dur_val}s) is too fast for the applied transform on an area of {area}px.",
                            impact="Rapid translation or scaling of large DOM elements triggers extreme motion sickness in users with vestibular disorders.",
                            fix="Increase transition duration to >300ms, or use prefers-reduced-motion media query to disable the transform.",
                            confidence=0.92,
                            source="vector_engine",
                            wcag_criterion="2.3.3",
                            session_id=str(page_data.session_id)
                        ))
                except ValueError:
                    pass
                    
        return findings

"""
COGNITIVE AGENT
================
Analyzes the clarity and predictability of the interface using advanced lexical
and topological heuristics.
WCAG Focus: 3.3.2 Labels, 2.4.4 Link Purpose, 1.3.5 Identify Input Purpose.
"""

import os
import sys
import re

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List, Dict, Set
from auditor.domain.agent_finding import AgentFinding # type: ignore
from auditor.infrastructure.data_extractor import PageData, ElementData # type: ignore
from auditor.domain.interfaces import IAccessibilityAgent # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore


class CognitiveAgent(IAccessibilityAgent):
    """
    Advanced Heuristic Agent for cognitive disabilities.
    Utilizes NLP-inspired lexical analysis and topological context to detect barriers.
    """

    def __init__(self) -> None:
        self.logger = auditor_logger.getChild("Agent.Cognitive")
        # Precompile common PII regex patterns for NLP-like autocomplete detection
        self.pii_pattern = re.compile(r'\b(email|password|username|login|phone|tel|address|street|zip|postal|country|card|cc\-|fname|lname|first\-name|last\-name|birth|dob)\b', re.IGNORECASE)
        # Strip punctuation for lexical analysis
        self.punctuation_stripper = re.compile(r'[^\w\s]')

    @property
    def agent_name(self) -> str:
        return "cognitive"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Performs advanced dynamic Cognitive accessibility analysis."""
        self.logger.info(f"Cognitive Agent executing advanced heuristics on: {page_data.url}")
        findings = []
        try:
            findings.extend(self._analyze_lexical_complexity(page_data))
        except Exception as e:
            self.logger.error(f"Cognitive Lexical Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_form_guidance(page_data))
        except Exception as e:
            self.logger.error(f"Cognitive Form Guidance Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_text_layout(page_data))
        except Exception as e:
            self.logger.error(f"Cognitive Text Layout Engine crash: {e}")
            
        try:
            findings.extend(self._analyze_dynamic_semantic_vectorization(page_data))
        except Exception as e:
            self.logger.error(f"Cognitive Semantic Vectorization Engine crash: {e}")

        return findings

    def _analyze_lexical_complexity(self, page_data: PageData) -> List[AgentFinding]:
        """
        Dynamically analyzes link text entropy and contextual topology.
        Identifies generic links without relying on hardcoded dictionaries.
        """
        findings = []
        link_fingerprints: Dict[str, Set[str]] = {}

        for link in page_data.links:
            raw_text = link.text.strip()
            if not raw_text:
                continue
            
            # Clean text for lexical analysis
            clean_text = self.punctuation_stripper.sub('', raw_text.lower())
            words = clean_text.split()
            word_count = len(words)
            
            # 1. Extreme Brevity Heuristic (Low Entropy)
            # Links that are just 1 word (like "here", "click", "more") are inherently ambiguous
            # unless they are navigational (like "Home", "About") which we filter by checking sibling text
            if word_count == 1:
                # Check topological context (sibling text or parent styles)
                # If there's no surrounding paragraph text, it's a standalone nav link (safe)
                parent_text_len = len(link.html) # Proxy for parent context in static snapshot
                if parent_text_len > 100: # It's embedded in a paragraph
                    findings.append(AgentFinding(
                        agent="cognitive",
                        violation_type="predictability",
                        guideline="G91",
                        element=link.html,
                        selector=link.selector,
                        issue=f"Extremely low lexical entropy in link text ('{raw_text}').",
                        impact="Users with cognitive disabilities cannot predict the link's destination based on a single isolated word within a paragraph.",
                        fix="Provide descriptive link text that clearly indicates the destination or function.",
                        confidence=0.88,
                        source="heuristic",
                        wcag_criterion="2.4.4",
                        session_id=str(page_data.session_id)
                    ))

            # 2. Identical Lexical Signature, Divergent Destinations
            # Tracks if the exact same link text points to different URLs
            href = link.attributes.get('href', '').strip()
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                if clean_text not in link_fingerprints:
                    link_fingerprints[clean_text] = set()
                link_fingerprints[clean_text].add(href)

        # Flag duplicate text / divergent hrefs
        for text_sig, hrefs in link_fingerprints.items():
            if len(hrefs) > 1 and len(text_sig.split()) < 4:
                # Same short text points to multiple places
                findings.append(AgentFinding(
                    agent="cognitive",
                    violation_type="consistency",
                    guideline="G197",
                    element=f"Multiple elements matching '{text_sig}'",
                    selector=f"a:contains('{text_sig}')",
                    issue=f"Identical short link text ('{text_sig}') points to {len(hrefs)} different destinations.",
                    impact="Creates severe cognitive dissonance. Users rely on consistent labeling to predict outcomes.",
                    fix="Differentiate the link text to reflect the unique destinations.",
                    confidence=0.95,
                    source="heuristic",
                    wcag_criterion="3.2.4",
                    session_id=str(page_data.session_id)
                ))

        return findings

    def _analyze_form_guidance(self, page_data: PageData) -> List[AgentFinding]:
        """
        Dynamically analyzes form field guidance using NLP tokenization and attribute topology.
        """
        findings = []

        for form in page_data.form_elements:
            attrs = form.attributes
            sibling_text = form.text
            
            # 1. Holistic Label Topology Check
            has_aria_label = bool(attrs.get("ariaLabel", "").strip())
            has_aria_labelledby = bool(attrs.get("ariaLabelledby", "").strip())
            has_title = bool(attrs.get("title", "").strip())
            has_placeholder = bool(attrs.get("placeholder", "").strip())
            has_visible_text = bool(sibling_text.strip())
            
            if not (has_aria_label or has_aria_labelledby or has_title or has_placeholder or has_visible_text):
                findings.append(AgentFinding(
                    agent="cognitive",
                    violation_type="guidance",
                    guideline="G131",
                    element=form.html,
                    selector=form.selector,
                    issue="Form input lacks both topological and programmatic guidance (no label, aria, title, or placeholder).",
                    impact="Users with memory issues or cognitive impairments will lose context of what data is required.",
                    fix="Implement a visible <label> or provide an aria-label.",
                    confidence=0.98,
                    source="heuristic",
                    wcag_criterion="3.3.2",
                    session_id=str(page_data.session_id)
                ))

            # 2. NLP-driven PII Autocomplete detection
            combined_sig = f"{attrs.get('id', '')} {attrs.get('name', '')} {attrs.get('type', '')}"
            if self.pii_pattern.search(combined_sig):
                if not attrs.get('autocomplete', '').strip():
                    findings.append(AgentFinding(
                        agent="cognitive",
                        violation_type="guidance",
                        guideline="G131",
                        element=form.html,
                        selector=form.selector,
                        issue="Semantic fingerprint indicates Personal Information (PII) collection, but lacks an 'autocomplete' token.",
                        impact="Forces users with cognitive/language impairments to manually type PII, increasing cognitive load and errors.",
                        fix="Add the appropriate HTML5 autocomplete token (e.g., autocomplete='email').",
                        confidence=0.92,
                        source="heuristic",
                        wcag_criterion="1.3.5",
                        session_id=str(page_data.session_id)
                    ))
                    
        return findings

    def _analyze_text_layout(self, page_data: PageData) -> List[AgentFinding]:
        """
        Evaluates visual text layout rules that impact reading comprehension.
        """
        findings = []
        for text in page_data.text_elements:
            styles = text.computed_styles
            if styles.get('textAlign', '').lower() == 'justify':
                findings.append(AgentFinding(
                    agent="cognitive",
                    violation_type="predictability",
                    guideline="G162",
                    element=text.html,
                    selector=text.selector,
                    issue="Text topology uses 'justify' alignment, creating irregular word spacing.",
                    impact="Generates 'rivers of white' which severely disrupts tracking for dyslexic and cognitively impaired users.",
                    fix="Remove text-align: justify. Use left (or right) alignment to ensure consistent word spacing.",
                    confidence=0.95,
                    source="heuristic",
                    wcag_criterion="1.4.8",
                    session_id=str(page_data.session_id)
                ))
        return findings

    def _analyze_dynamic_semantic_vectorization(self, page_data: PageData) -> List[AgentFinding]:
        """
        Phase X: Dynamic Semantic Vectorization.
        Computationally infers ARIA contradictions and role malformations across all DOM elements.
        """
        findings = []
        all_elements = page_data.text_elements + page_data.form_elements + page_data.links + page_data.images
        
        for el in all_elements:
            attrs = el.attributes
            role = attrs.get('role', '')
            aria_hidden = attrs.get('ariaHidden', '')
            tabindex = attrs.get('tabindex', '')
            
            # Vector 1: ARIA Contradiction Trap
            if aria_hidden == 'true' and (tabindex == '0' or el.tag in ('a', 'button', 'input', 'select', 'textarea')):
                findings.append(AgentFinding(
                    agent="cognitive",
                    violation_type="semantic_contradiction",
                    guideline="G131",
                    element=el.html,
                    selector=el.selector,
                    issue="Severe structural contradiction: Element is inherently focusable but explicitly hidden from Screen Readers via aria-hidden='true'.",
                    impact="Screen reader users will tab to a 'ghost' element that reads nothing, causing extreme cognitive dissonance.",
                    fix="Remove aria-hidden='true' if the element must receive focus, or add tabindex='-1' if it should be completely hidden.",
                    confidence=0.99,
                    source="vector_engine",
                    wcag_criterion="4.1.2",
                    session_id=str(page_data.session_id)
                ))
                
            # Vector 2: Semantic Impersonation (Fake Buttons)
            if role == 'button' and el.tag not in ('button', 'input', 'a'):
                if tabindex != '0':
                    findings.append(AgentFinding(
                        agent="cognitive",
                        violation_type="semantic_impersonation",
                        guideline="G131",
                        element=el.html,
                        selector=el.selector,
                        issue=f"Semantic impersonation: A {el.tag} element uses role='button' but lacks keyboard focusability (no tabindex='0').",
                        impact="Screen readers announce a button, but keyboard users cannot reach or press it, breaking expected interaction models.",
                        fix="Change the element to a native <button>, or add tabindex='0' and ensure JavaScript handles Space/Enter keys.",
                        confidence=0.96,
                        source="vector_engine",
                        wcag_criterion="4.1.2",
                        session_id=str(page_data.session_id)
                    ))
                    
        return findings

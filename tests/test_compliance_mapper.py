import pytest
from auditor.shared.compliance_mapper import ComplianceMapper
from auditor.domain.violation import ImpactLevel

def test_get_compliance_level():
    # Below A: level A tag + critical impact
    assert ComplianceMapper.get_compliance_level(["wcag2a", "some-tag"], ImpactLevel.CRITICAL) == "Below A"
    
    # AAA: AAA tag
    assert ComplianceMapper.get_compliance_level(["wcag2aaa"], ImpactLevel.MINOR) == "AAA"
    
    # AA: AA tag
    assert ComplianceMapper.get_compliance_level(["wcag2aa"], ImpactLevel.MODERATE) == "AA"
    
    # A: A tag but not critical
    assert ComplianceMapper.get_compliance_level(["wcag2a"], ImpactLevel.SERIOUS) == "A"
    
    # Non-Standard fallback
    assert ComplianceMapper.get_compliance_level(["random-tag"], ImpactLevel.MINOR) == "Non-Standard"

def test_get_category_by_tags():
    # Perceivable tags
    assert ComplianceMapper.get_category(["cat.color"]) == "Perceivable"
    assert ComplianceMapper.get_category(["contrast"]) == "Perceivable"
    
    # Operable tags
    assert ComplianceMapper.get_category(["keyboard"]) == "Operable"
    assert ComplianceMapper.get_category(["focus-visible"]) == "Operable"
    
    # Understandable tags
    assert ComplianceMapper.get_category(["cognitive"]) == "Understandable"
    assert ComplianceMapper.get_category(["forms"]) == "Understandable"
    
    # Robust tags
    assert ComplianceMapper.get_category(["aria"]) == "Robust"
    assert ComplianceMapper.get_category(["parsing"]) == "Robust"

def test_get_category_by_wcag_number():
    # wcag1xx -> Perceivable
    assert ComplianceMapper.get_category(["wcag143"]) == "Perceivable"
    
    # wcag2xx -> Operable
    assert ComplianceMapper.get_category(["wcag211"]) == "Operable"
    
    # wcag3xx -> Understandable
    assert ComplianceMapper.get_category(["wcag311"]) == "Understandable"
    
    # wcag4xx -> Robust
    assert ComplianceMapper.get_category(["wcag411"]) == "Robust"

    # WCAG Criterion (e.g. 2.5.5 or wcag2.5.5) -> Operable
    assert ComplianceMapper.get_category(["wcag2.5.5"]) == "Operable"
    assert ComplianceMapper.get_category(["2.5.5"]) == "Operable"

    # WCAG technique (e.g. wcagG44) -> Should fall through to agent or other logic, not Robust
    # It falls through to motor agent -> Operable, but on tags alone (no agent/rule_id) it should fall through to General Accessibility
    assert ComplianceMapper.get_category(["wcagG44"]) == "General Accessibility"

def test_get_category_by_rule_id():
    assert ComplianceMapper.get_category([], rule_id="color-contrast") == "Perceivable"
    assert ComplianceMapper.get_category([], rule_id="keyboard-focus") == "Operable"
    assert ComplianceMapper.get_category([], rule_id="label-form") == "Understandable"
    assert ComplianceMapper.get_category([], rule_id="aria-allowed-attr") == "Robust"

def test_get_category_by_agent():
    assert ComplianceMapper.get_category([], agent="visual") == "Perceivable"
    assert ComplianceMapper.get_category([], agent="motor") == "Operable"
    assert ComplianceMapper.get_category([], agent="cognitive") == "Understandable"
    assert ComplianceMapper.get_category([], agent="neural") == "Robust"

def test_get_severity_matrix():
    assert ComplianceMapper.get_severity_matrix(ImpactLevel.CRITICAL) == "Critical (High-Friction / Legal Risk)"
    assert ComplianceMapper.get_severity_matrix(ImpactLevel.SERIOUS) == "Serious (Significant Barrier)"
    assert ComplianceMapper.get_severity_matrix(ImpactLevel.MODERATE) == "Moderate (Inconvenience)"
    assert ComplianceMapper.get_severity_matrix(ImpactLevel.MINOR) == "Minor (Best Practice)"
    assert ComplianceMapper.get_severity_matrix("unknown") == "Unclassified"

def test_enhance_violation():
    raw = {
        "tags": ["wcag2aa"],
        "impact": "serious",
        "rule_id": "color-contrast",
        "agent": "visual"
    }
    enhanced = ComplianceMapper.enhance_violation(raw)
    assert enhanced["compliance_level"] == "AA"
    assert enhanced["category"] == "Perceivable"
    assert enhanced["severity_matrix"] == "Serious (Significant Barrier)"

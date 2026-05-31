import pathlib
from unittest.mock import patch
from auditor.shared.paths import get_project_root
from auditor.shared.compliance_mapper import ComplianceMapper
from auditor.domain.violation import ImpactLevel

def test_get_project_root_fallback():
    with patch.object(pathlib.Path, "exists", return_value=False):
        root = get_project_root()
        assert isinstance(root, pathlib.Path)

def test_compliance_mapper_level():
    # AAA level
    lvl = ComplianceMapper.get_compliance_level(["wcag2aaa"], ImpactLevel.MINOR)
    assert lvl == "AAA"
    
    # AA level
    lvl = ComplianceMapper.get_compliance_level(["wcag2aa"], ImpactLevel.MINOR)
    assert lvl == "AA"
    
    # A level
    lvl = ComplianceMapper.get_compliance_level(["wcag2a"], ImpactLevel.MINOR)
    assert lvl == "A"
    
    # Non-standard
    lvl = ComplianceMapper.get_compliance_level(["other"], ImpactLevel.MINOR)
    assert lvl == "Non-Standard"
    
    # Below A level
    lvl = ComplianceMapper.get_compliance_level(["wcag2a"], ImpactLevel.CRITICAL)
    assert lvl == "Below A"

def test_compliance_mapper_categories():
    # Perceivable
    cat = ComplianceMapper.get_category(["cat.color"])
    assert cat == "Perceivable"
    
    # Operable
    cat = ComplianceMapper.get_category(["cat.keyboard"])
    assert cat == "Operable"
    
    # Understandable
    cat = ComplianceMapper.get_category(["cat.forms"])
    assert cat == "Understandable"
    
    # Robust
    cat = ComplianceMapper.get_category(["cat.aria"])
    assert cat == "Robust"
    
    # General
    cat = ComplianceMapper.get_category(["other"])
    assert cat == "General Accessibility"

def test_compliance_mapper_enhance_violation():
    v = {
        "tags": ["wcag2aaa", "cat.forms"],
        "impact": "serious"
    }
    enhanced = ComplianceMapper.enhance_violation(v)
    assert enhanced["compliance_level"] == "AAA"
    assert enhanced["category"] == "Understandable"
    assert "Significant Barrier" in enhanced["severity_matrix"]

def test_compliance_mapper_enhance_violation_invalid_impact():
    v = {
        "tags": ["wcag2a", "cat.aria"],
        "impact": "invalid_value"
    }
    enhanced = ComplianceMapper.enhance_violation(v)
    assert enhanced["compliance_level"] == "A"
    assert enhanced["category"] == "Robust"
    assert "Best Practice" in enhanced["severity_matrix"]

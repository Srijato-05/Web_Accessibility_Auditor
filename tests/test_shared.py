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
    cat_sem = ComplianceMapper.get_category(["cat.semantics"])
    assert cat_sem == "Perceivable"
    
    # Operable
    cat = ComplianceMapper.get_category(["cat.keyboard"])
    assert cat == "Operable"
    cat_title = ComplianceMapper.get_category(["CAT.TITLE"])
    assert cat_title == "Operable"
    
    # Understandable
    cat = ComplianceMapper.get_category(["cat.forms"])
    assert cat == "Understandable"
    cat_lang = ComplianceMapper.get_category(["cat.language"])
    assert cat_lang == "Understandable"
    
    # Robust
    cat = ComplianceMapper.get_category(["cat.aria"])
    assert cat == "Robust"
    cat_nrv = ComplianceMapper.get_category(["cat.name-role-value"])
    assert cat_nrv == "Robust"
    
    # Rule ID matching fallback
    cat_rule = ComplianceMapper.get_category([], rule_id="duplicate-id-active")
    assert cat_rule == "Robust"
    
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

def test_stealth_profile_generator():
    from auditor.shared.stealth_profiles import StealthProfileGenerator
    profiles = StealthProfileGenerator.get_all_profiles()
    assert len(profiles) == 4
    
    # Random profile validation
    rand_profile = StealthProfileGenerator.get_random_profile()
    assert "name" in rand_profile
    assert "userAgent" in rand_profile
    assert "viewport" in rand_profile
    assert "width" in rand_profile["viewport"]
    assert "height" in rand_profile["viewport"]


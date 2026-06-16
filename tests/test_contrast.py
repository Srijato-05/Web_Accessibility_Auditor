import pytest
from auditor.application.agents.utils.contrast import (
    parse_rgb,
    relative_luminance,
    contrast_ratio,
    meets_aa_normal,
    meets_aa_large,
    meets_link_distinction,
    color_distance,
    is_similar_color,
)

def test_parse_rgb():
    # Valid RGB formats
    assert parse_rgb("rgb(255, 0, 0)") == (255, 0, 0)
    assert parse_rgb("rgba(120, 240, 50, 0.5)") == (120, 240, 50)
    assert parse_rgb("#ff0000") == (255, 0, 0)
    assert parse_rgb("#F00") == (255, 0, 0)
    
    # Whitespace and case-insensitivity
    assert parse_rgb("  RGB( 10,  20, 30 ) ") == (10, 20, 30)
    
    # Invalid formats
    assert parse_rgb(None) is None
    assert parse_rgb("") is None
    assert parse_rgb("invalid") is None
    assert parse_rgb("#gg0000") is None
    assert parse_rgb("#1234") is None

def test_relative_luminance_and_contrast():
    # Relative luminance
    white_lum = relative_luminance(255, 255, 255)
    black_lum = relative_luminance(0, 0, 0)
    assert white_lum == pytest.approx(1.0)
    assert black_lum == pytest.approx(0.0)
    
    # Test low sRGB value to trigger s <= 0.04045 branch
    low_lum = relative_luminance(10, 10, 10)
    assert low_lum < 0.01
    
    # Contrast ratio
    assert contrast_ratio((255, 255, 255), (0, 0, 0)) == pytest.approx(21.0)
    assert contrast_ratio((255, 255, 255), (255, 255, 255)) == pytest.approx(1.0)

def test_wcag_thresholds():
    assert meets_aa_normal(4.5) is True
    assert meets_aa_normal(4.4) is False
    assert meets_aa_large(3.0) is True
    assert meets_aa_large(2.9) is False
    assert meets_link_distinction(3.0) is True
    assert meets_link_distinction(2.9) is False

def test_color_similarity():
    c1 = (255, 0, 0)
    c2 = (250, 5, 5)
    c3 = (0, 0, 255)
    assert color_distance(c1, c2) < 10
    assert is_similar_color(c1, c2, threshold=15.0) is True
    assert is_similar_color(c1, c3, threshold=15.0) is False


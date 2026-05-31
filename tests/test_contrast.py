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
from auditor.application.agents.rules.color_rules import (
    has_visual_cue_beyond_color,
    is_link_color_only,
    classify_status_color,
    is_form_error_color_only,
    is_text_color_only_meaning,
    is_image_color_only,
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

def test_has_visual_cue_beyond_color():
    # Underline decoration
    assert has_visual_cue_beyond_color({"textDecoration": "underline"}) is True
    # Bold weight
    assert has_visual_cue_beyond_color({"fontWeight": "bold"}) is True
    assert has_visual_cue_beyond_color({"fontWeight": "700"}) is True
    # Border
    assert has_visual_cue_beyond_color({"borderBottomWidth": "2px", "borderBottomStyle": "solid"}) is True
    assert has_visual_cue_beyond_color({"borderBottomWidth": "0px"}) is False
    # Outline
    assert has_visual_cue_beyond_color({"outlineWidth": "1px"}) is True
    assert has_visual_cue_beyond_color({"outlineWidth": ""}) is False

def test_is_link_color_only():
    link_styles_underlined = {"textDecoration": "underline", "color": "#ff0000"}
    parent_styles = {"color": "#000000"}
    
    # Link has visual cue (underline) - not color only
    assert is_link_color_only(link_styles_underlined, parent_styles) is False
    
    # Link has similar color to parent
    link_styles_similar = {"textDecoration": "none", "color": "#050505"}
    assert is_link_color_only(link_styles_similar, parent_styles) is False
    
    # Link has high contrast to parent (>= 3:1) - meets link distinction
    link_styles_good = {"textDecoration": "none", "color": "#ffffff"}
    assert is_link_color_only(link_styles_good, parent_styles) is False
    
    # Link has bad contrast to parent (< 3:1) and no visual cues
    link_styles_bad = {"textDecoration": "none", "color": "#333333"}
    assert is_link_color_only(link_styles_bad, parent_styles) is True

def test_classify_status_color():
    assert classify_status_color((255, 0, 0)) == "error"
    assert classify_status_color((40, 167, 69)) == "success"
    assert classify_status_color((255, 165, 0)) == "warning"
    assert classify_status_color((0, 0, 255)) is None

def test_is_form_error_color_only():
    # If error text or aria-invalid is present, it's not color-only
    assert is_form_error_color_only({}, True, False) is False
    assert is_form_error_color_only({}, False, True) is False
    
    # Red border with no error text or aria-invalid
    assert is_form_error_color_only({"borderColor": "rgb(255, 0, 0)"}, False, False) is True
    # Non-status color border
    assert is_form_error_color_only({"borderColor": "rgb(0, 0, 255)"}, False, False) is False

def test_is_text_color_only_meaning():
    # Visual cues exist
    assert is_text_color_only_meaning({"fontWeight": "bold", "color": "#ff0000"}, {"color": "#000000"}) is False
    # Identical colors
    assert is_text_color_only_meaning({"color": "#000000"}, {"color": "#000000"}) is False
    # Distinct error color with no other cue
    assert is_text_color_only_meaning({"color": "rgb(255, 0, 0)"}, {"color": "#000000"}) is True

def test_is_image_color_only():
    # Text alternative is present
    assert is_image_color_only(True, False, False, False, "img") is False
    assert is_image_color_only(False, True, False, False, "svg") is False
    
    # No text alternative, but regular img tag
    assert is_image_color_only(False, False, False, False, "img") is False
    # SVG or Canvas with no text alternative (likely charts)
    assert is_image_color_only(False, False, False, False, "svg") is True
    assert is_image_color_only(False, False, False, False, "canvas") is True

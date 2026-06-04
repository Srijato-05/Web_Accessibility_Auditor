import pytest
from auditor.application.agents.rules.cognitive_rules import is_ambiguous_link, is_missing_label_logic

def test_is_ambiguous_link():
    # Standard matches
    assert is_ambiguous_link("click here") is True
    assert is_ambiguous_link("read more") is True
    
    # Normalization matches (punctuation, HTML entities, arrows, spacing)
    assert is_ambiguous_link("read more...") is True
    assert is_ambiguous_link("click here &rarr;") is True
    assert is_ambiguous_link("learn more [3]") is True
    assert is_ambiguous_link("details (1)") is True
    
    # Non-matching descriptive links
    assert is_ambiguous_link("read more about privacy settings") is False
    assert is_ambiguous_link("get started with your premium account") is False

def test_is_missing_label_logic():
    # Input has visible label/text
    assert is_missing_label_logic({}, "Username:") is False
    
    # Input has programmatic attributes
    assert is_missing_label_logic({"ariaLabel": "Enter email"}, "") is False
    assert is_missing_label_logic({"ariaLabelledby": "label-id"}, "") is False
    assert is_missing_label_logic({"title": "Search Query"}, "") is False
    assert is_missing_label_logic({"placeholder": "Password"}, "") is False
    
    # Input has absolutely no labels
    assert is_missing_label_logic({}, "") is True

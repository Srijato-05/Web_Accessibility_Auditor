import pytest
import os
import json
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch
from auditor.infrastructure.pdf_reporter import generate_html_from_json, convert_json_to_pdf

def test_generate_html_from_json():
    data = {
        "session_id": "test-session-id",
        "target_url": "https://test.com",
        "violations": [
            {
                "rule_id": "image-alt",
                "compliance_level": "A",
                "category": "Perceivable",
                "description": "Alt missing",
                "impact": "critical",
                "selector": "img",
                "fix": "Add alt",
                "agent": "axe",
                "url": "https://test.com"
            }
        ],
        "matrix": {
            "axe": {"Perceivable": 1, "Operable": 0, "Understandable": 0, "Robust": 0}
        }
    }
    
    html = generate_html_from_json(data)
    
    assert "Accessibility Report" in html
    assert "https://test.com" in html
    assert "Alt missing" in html
    assert "Axe" in html
    assert "Perceivable" in html

    # Test Fallbacks
    data_fallback = {
        "session_id": "test-session-id",
        "target_url": "https://test.com",
        "violations": [
            {
                "rule_id": "image-alt",
                "compliance_level": "A",
                "category": "perceivable",
                "description": "Alt missing",
                "impact": "critical",
                "selector": "img",
                "fix": "Add alt",
                "agent": "axe",
                "url": "https://test.com"
            },
            {
                "rule_id": "aria-allowed-attr",
                "compliance_level": "AA",
                "category": "robust",
                "description": "Aria allowed attr",
                "impact": "serious",
                "selector": "div",
                "fix": "Fix aria",
                "agent": "cognitive",
                "url": "https://test.com"
            }
        ]
    }
    html_fallback = generate_html_from_json(data_fallback)
    assert "Accessibility Report" in html_fallback

@patch("auditor.infrastructure.pdf_reporter.sync_playwright")
def test_convert_json_to_pdf(mock_sync_playwright):
    # Setup Playwright mock chain
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    
    data = {
        "session_id": "test-session-id",
        "violations": []
    }
    
    # Save to temp JSON
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        json_path = f.name
        
    pdf_path = json_path.replace(".json", ".pdf")
    
    try:
        convert_json_to_pdf(json_path, pdf_path)
        
        # Verify Playwright operations triggered
        mock_p.chromium.launch.assert_called_once()
        mock_page.goto.assert_called_once()
        mock_page.emulate_media.assert_called_once_with(media="print")
        mock_page.pdf.assert_called_once()
    finally:
        os.remove(json_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_generate_html_extra_branches():
    # 1. Invalid date generated_at
    data = {
        "session_id": "session-123",
        "generated_at": "invalid-date",
        "findings": [
            {
                "agent": "axe",
                "rule_id": "image-alt",
                "category": "perceivable",
                "compliance_level": "Below A",
                "tags": ["cat.alt-text"]
            },
            {
                "agent": "visual",
                "rule_id": "color-contrast",
                "category": "operable",
                "compliance_level": "AA",
                "description": "Contrast too low. Fix Recommended: Increase contrast color value."
            },
            {
                "agent": "motor",
                "rule_id": "keyboard-trap",
                "category": "understandable",
                "compliance_level": "AAA",
                "nodes": [{"fix": "Add escape key action"}]
            },
            {
                "agent": "cognitive",
                "rule_id": "complex-lang",
                "category": "robust",
                "compliance_level": "A",
                "nodes": [{"failure_summary": "Simplify sentence structure"}]
            },
            {
                "agent": "neural",
                "rule_id": "layout-shift",
                "category": "unknown-category",
                "compliance_level": "A"
            }
        ]
    }
    
    html = generate_html_from_json(data)
    assert "Accessibility Report" in html
    assert "Below A" in html
    assert "Increase contrast color value" in html
    assert "Add escape key action" in html
    assert "Simplify sentence structure" in html
    assert "invalid-date" in html
    
    # 2. Matrix parsing category logic
    data_with_matrix = {
        "matrix": {
            "axe": {
                "perceivable-issues": 1,
                "operable-issues": 2,
                "understandable-issues": 3,
                "robust-issues": 4,
                "general-issues": 5
            }
        }
    }
    html_matrix = generate_html_from_json(data_with_matrix)
    assert "Accessibility Report" in html_matrix

@patch("auditor.infrastructure.pdf_reporter.sync_playwright")
def test_convert_json_to_pdf_exception(mock_sync_playwright):
    # Setup Playwright mock chain to raise exception
    mock_p = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.side_effect = RuntimeError("Playwright launch crash")
    
    data = {"session_id": "test", "violations": []}
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(data, f)
        json_path = f.name
        
    try:
        with pytest.raises(RuntimeError):
            convert_json_to_pdf(json_path, "out.pdf")
    finally:
        os.remove(json_path)

def test_pdf_reporter_main():
    import auditor.infrastructure.pdf_reporter as pr
    
    # Missing file path
    with patch("sys.argv", ["pdf_reporter.py", "non_existent_json.json"]), \
         patch("builtins.print") as mock_print, \
         pytest.raises(SystemExit) as exc:
        
        with patch("os.path.exists", return_value=False):
            json_path = "non_existent_json.json"
            if not os.path.exists(json_path):
                print(f"Error: File '{json_path}' not found.")
                exit(1)
    
    assert exc.value.code == 1
    mock_print.assert_called_with("Error: File 'non_existent_json.json' not found.")
    
    # Valid execution CLI main code logic block
    with patch("sys.argv", ["pdf_reporter.py", "valid.json"]), \
         patch("os.path.exists", return_value=True), \
         patch("auditor.infrastructure.pdf_reporter.convert_json_to_pdf") as mock_convert:
        
        json_path = "valid.json"
        output_pdf = None
        if not output_pdf:
            output_pdf = os.path.splitext(json_path)[0] + ".pdf"
        pr.convert_json_to_pdf(json_path, output_pdf)
        mock_convert.assert_called_with("valid.json", "valid.pdf")

@patch("auditor.infrastructure.pdf_reporter.sync_playwright")
def test_convert_json_to_pdf_chunking(mock_sync_playwright):
    # Setup Playwright mock chain
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Create pypdf mocks
    mock_writer = MagicMock()
    
    # Generate >150 findings (e.g. 155 findings)
    findings = [
        {
            "rule_id": "image-alt",
            "compliance_level": "A",
            "category": "Perceivable",
            "description": "Alt missing",
            "impact": "critical",
            "selector": "img",
            "fix": "Add alt",
            "agent": "axe",
            "url": "https://test.com"
        }
        for _ in range(155)
    ]
    
    data = {
        "session_id": "test-session-id",
        "violations": findings
    }
    
    # Save to temp JSON
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        json_path = f.name
        
    pdf_path = json_path.replace(".json", ".pdf")
    
    with patch("pypdf.PdfWriter", return_value=mock_writer), \
         patch("auditor.infrastructure.pdf_reporter.CHUNK_THRESHOLD", 150), \
         patch("auditor.infrastructure.pdf_reporter.CHUNK_SIZE", 150):
        try:
            convert_json_to_pdf(json_path, pdf_path)
            
            # Verify pypdf and Playwright were called
            mock_writer.append.assert_called()
            mock_writer.write.assert_called_with(pdf_path)
            mock_writer.close.assert_called()
            mock_p.chromium.launch.assert_called_once()
        finally:
            os.remove(json_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

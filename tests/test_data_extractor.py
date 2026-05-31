import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.infrastructure.data_extractor import _parse_element, extract_page_data, PageData, ElementData

def test_parse_element_mapping():
    raw = {
        "tag": "a",
        "selector": "a.test",
        "html": "<a>Link</a>",
        "text": "Link",
        "computedStyles": {"color": "rgb(0, 0, 0)"},
        "attributes": {"href": "https://test.com"},
        "boundingBox": {"x": 10.0, "y": 20.0, "width": 100.0, "height": 30.0},
        "parentStyles": {"color": "rgb(255, 255, 255)"}
    }
    
    element = _parse_element(raw)
    
    assert isinstance(element, ElementData)
    assert element.tag == "a"
    assert element.selector == "a.test"
    assert element.text == "Link"
    assert element.computed_styles["color"] == "rgb(0, 0, 0)"
    assert element.attributes["href"] == "https://test.com"
    assert element.bounding_box["x"] == 10.0
    assert element.parent_styles["color"] == "rgb(255, 255, 255)"

@pytest.mark.asyncio
async def test_extract_page_data_success():
    mock_page = AsyncMock()
    mock_page.url = "https://test-extract.com"
    
    # Setup page evaluate script response data
    mock_page.evaluate.side_effect = [
        [{"tag": "a", "selector": "a", "html": "", "text": "Link"}], # links
        [{"tag": "p", "selector": "p", "html": "", "text": "Paragraph"}], # text_elements
        [{"tag": "input", "selector": "input", "html": "", "text": ""}], # form_elements
        [{"tag": "img", "selector": "img", "html": "", "text": ""}] # images
    ]
    mock_page.screenshot = AsyncMock(return_value=b"png_data")
    
    session_id = uuid.uuid4()
    
    page_data = await extract_page_data(mock_page, session_id, capture_screenshot=True)
    
    assert isinstance(page_data, PageData)
    assert page_data.url == "https://test-extract.com"
    assert page_data.session_id == session_id
    assert len(page_data.links) == 1
    assert len(page_data.text_elements) == 1
    assert len(page_data.form_elements) == 1
    assert len(page_data.images) == 1
    assert page_data.screenshot == b"png_data"
    
    assert mock_page.evaluate.call_count == 4
    mock_page.screenshot.assert_called_once_with(full_page=True, type="png")

@pytest.mark.asyncio
async def test_extract_page_data_hydration_retry():
    mock_page = AsyncMock()
    mock_page.url = "https://test-extract.com"
    
    # First call: evaluate returns [] (links) -> triggers retry!
    # Second call: evaluate returns 1 link
    # Next calls: text, form, images
    mock_page.evaluate.side_effect = [
        [], # First attempt links
        [{"tag": "a", "selector": "a", "html": "", "text": "Link"}], # Second attempt links
        [{"tag": "p", "selector": "p", "html": "", "text": "Paragraph"}],
        [{"tag": "input", "selector": "input", "html": "", "text": ""}],
        [{"tag": "img", "selector": "img", "html": "", "text": ""}]
    ]
    
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        page_data = await extract_page_data(mock_page, uuid.uuid4(), capture_screenshot=False)
        assert len(page_data.links) == 1
        mock_sleep.assert_called_once_with(3.0)

@pytest.mark.asyncio
async def test_extract_page_data_screenshot_failure():
    mock_page = AsyncMock()
    mock_page.url = "https://test-extract.com"
    mock_page.evaluate.return_value = []
    # Screenshot throws exception
    mock_page.screenshot.side_effect = Exception("Screenshot engine offline")
    
    page_data = await extract_page_data(mock_page, uuid.uuid4(), capture_screenshot=True)
    assert page_data.screenshot is None

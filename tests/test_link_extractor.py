import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor

@pytest.mark.asyncio
async def test_link_extractor_lifecycle():
    extractor = PlaywrightLinkExtractor()
    
    mock_browser = AsyncMock()
    mock_mgr = AsyncMock()
    mock_mgr.chromium.launch.return_value = mock_browser
    
    mock_playwright = MagicMock()
    mock_playwright.return_value.start = AsyncMock(return_value=mock_mgr)
    
    with patch("auditor.infrastructure.link_extractor.async_playwright", mock_playwright):
        await extractor.start()
        assert extractor.browser == mock_browser
        
        await extractor.teardown()
        assert extractor.browser is None
        assert extractor.playwright_mgr is None
        mock_browser.close.assert_called_once()
        mock_mgr.stop.assert_called_once()

@pytest.mark.asyncio
async def test_link_extractor_extract_links_success():
    extractor = PlaywrightLinkExtractor()
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.eval_on_selector_all.return_value = ["https://test.com/1", "https://test.com/2", "https://test.com/1"]
    
    extractor.browser = mock_browser
    
    links = await extractor.extract_links("https://test.com")
    
    # Verify unique links mapping
    assert len(links) == 2
    assert "https://test.com/1" in links
    assert "https://test.com/2" in links
    
    # Verify stealth settings
    mock_browser.new_context.assert_called_once()
    mock_context.add_init_script.assert_called_once()
    mock_page.goto.assert_called_once_with("https://test.com", wait_until="networkidle", timeout=60000)

@pytest.mark.asyncio
async def test_link_extractor_extract_links_failure():
    extractor = PlaywrightLinkExtractor()
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.side_effect = Exception("Page navigation timeout")
    
    extractor.browser = mock_browser
    
    links = await extractor.extract_links("https://test.com")
    assert links == []

@pytest.mark.asyncio
async def test_link_extractor_auto_start():
    extractor = PlaywrightLinkExtractor()
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.eval_on_selector_all.return_value = ["https://url1"]
    
    with patch.object(extractor, "start", AsyncMock()) as mock_start:
        # We manually set browser to mock_browser inside/after start call
        async def side_effect():
            extractor.browser = mock_browser
        mock_start.side_effect = side_effect
        
        links = await extractor.extract_links("https://test.com")
        mock_start.assert_called_once()
        assert links == ["https://url1"]

@pytest.mark.asyncio
async def test_link_extractor_teardown_exceptions():
    extractor = PlaywrightLinkExtractor()
    
    mock_browser = AsyncMock()
    mock_browser.close.side_effect = Exception("Failed browser close")
    mock_mgr = AsyncMock()
    mock_mgr.stop.side_effect = Exception("Failed manager stop")
    
    extractor.browser = mock_browser
    extractor.playwright_mgr = mock_mgr
    
    # Should not raise exception
    await extractor.teardown()
    assert extractor.browser is None
    assert extractor.playwright_mgr is None

@pytest.mark.asyncio
async def test_link_extractor_critical_session_error():
    extractor = PlaywrightLinkExtractor()
    mock_browser = AsyncMock()
    # Force context creation failure
    mock_browser.new_context.side_effect = Exception("Failed context setup")
    extractor.browser = mock_browser
    
    links = await extractor.extract_links("https://test.com")
    assert links == []

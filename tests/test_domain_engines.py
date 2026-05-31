import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.domain.robots_engine import RobotsAdherenceEngine
from auditor.domain.sitemap_discovery import SitemapDiscoveryEngine

@pytest.mark.asyncio
async def test_robots_adherence_engine_success():
    engine = RobotsAdherenceEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_resp = MagicMock(status=200)
    
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.return_value = mock_resp
    
    # Mock robots.txt body text
    mock_page.evaluate.return_value = "User-agent: *\nDisallow: /private/\nSitemap: https://test.com/sitemap.xml"
    
    with patch("auditor.domain.robots_engine.async_playwright", return_value=mock_p):
        await engine.initialize("https://test.com")
        
        assert engine._is_ready is True
        assert engine.get_sitemaps() == ["https://test.com/sitemap.xml"]
        assert engine.is_allowed("https://test.com/private/secret") is False
        assert engine.is_allowed("https://test.com/public/home") is True

@pytest.mark.asyncio
async def test_robots_adherence_engine_not_ready():
    engine = RobotsAdherenceEngine()
    assert engine.is_allowed("https://test.com/any") is True
    assert engine.get_sitemaps() == []

@pytest.mark.asyncio
async def test_robots_adherence_engine_unreachable():
    engine = RobotsAdherenceEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_resp = MagicMock(status=404)
    
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.return_value = mock_resp
    
    with patch("auditor.domain.robots_engine.async_playwright", return_value=mock_p):
        await engine.initialize("https://test.com")
        assert engine._is_ready is True
        assert engine.is_allowed("https://test.com/private") is True

@pytest.mark.asyncio
async def test_robots_adherence_engine_exception():
    engine = RobotsAdherenceEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_p.chromium.launch = AsyncMock(side_effect=Exception("Playwright crash"))
    
    with patch("auditor.domain.robots_engine.async_playwright", return_value=mock_p):
        await engine.initialize("https://test.com")
        assert engine._is_ready is True
        assert engine.is_allowed("https://test.com/any") is True

@pytest.mark.asyncio
async def test_robots_adherence_engine_can_fetch_exception():
    engine = RobotsAdherenceEngine()
    engine._is_ready = True
    engine.parser = MagicMock()
    engine.parser.can_fetch = MagicMock(side_effect=Exception("parse error"))
    assert engine.is_allowed("https://test.com/any") is True


@pytest.mark.asyncio
async def test_sitemap_discovery_engine_success():
    engine = SitemapDiscoveryEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_resp = MagicMock(status=200)
    
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.return_value = mock_resp
    
    # 1. First call to sitemap index
    xml_index = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://test.com/sub-sitemap.xml</loc>
      </sitemap>
    </sitemapindex>
    """
    
    # 2. Second call to sub-sitemap
    xml_sub = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://test.com/page-1</loc>
      </url>
    </urlset>
    """
    
    mock_page.content = AsyncMock(side_effect=[xml_index, xml_sub])
    
    with patch("auditor.domain.sitemap_discovery.async_playwright", return_value=mock_p):
        urls = await engine.discover_urls("https://test.com/sitemap.xml")
        
        assert len(urls) == 1
        assert "https://test.com/page-1" in urls

@pytest.mark.asyncio
async def test_sitemap_discovery_engine_unreachable():
    engine = SitemapDiscoveryEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_resp = MagicMock(status=500)
    
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto.return_value = mock_resp
    
    with patch("auditor.domain.sitemap_discovery.async_playwright", return_value=mock_p):
        urls = await engine.discover_urls("https://test.com/sitemap.xml")
        assert len(urls) == 0

@pytest.mark.asyncio
async def test_sitemap_discovery_engine_goto_exception():
    engine = SitemapDiscoveryEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto = AsyncMock(side_effect=Exception("Navigation timeout"))
    
    with patch("auditor.domain.sitemap_discovery.async_playwright", return_value=mock_p):
        urls = await engine.discover_urls("https://test.com/sitemap.xml")
        assert len(urls) == 0

@pytest.mark.asyncio
async def test_sitemap_discovery_engine_critical_failure():
    engine = SitemapDiscoveryEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_p.chromium.launch = AsyncMock(side_effect=Exception("Launch failed"))
    
    with patch("auditor.domain.sitemap_discovery.async_playwright", return_value=mock_p):
        urls = await engine.discover_urls("https://test.com/sitemap.xml")
        assert len(urls) == 0

@pytest.mark.asyncio
async def test_sitemap_discovery_engine_nested_loop_and_missing_loc():
    engine = SitemapDiscoveryEngine()
    
    mock_p = AsyncMock()
    mock_p.__aenter__.return_value = mock_p
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = MagicMock()
    mock_resp = MagicMock(status=200)
    
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto = AsyncMock(return_value=mock_resp)
    
    # First response index with loop and second response with missing loc
    xml_loop = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://test.com/sitemap.xml</loc>
      </sitemap>
    </sitemapindex>
    """
    
    xml_missing_loc = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <!-- Missing loc element -->
      </url>
    </urlset>
    """
    
    mock_page.content = AsyncMock(side_effect=[xml_loop, xml_missing_loc])
    
    with patch("auditor.domain.sitemap_discovery.async_playwright", return_value=mock_p):
        urls = await engine.discover_urls("https://test.com/sitemap.xml")
        assert len(urls) == 0

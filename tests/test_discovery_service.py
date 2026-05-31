import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.application.discovery_service import DiscoveryService

@pytest.mark.asyncio
async def test_discovery_session_sitemap_success():
    mock_queue = AsyncMock()
    mock_crawler = AsyncMock()
    mock_repo = AsyncMock()
    
    service = DiscoveryService(mock_queue, mock_crawler, mock_repo)
    
    # Mock engines
    service.robots_engine = MagicMock()
    service.robots_engine.initialize = AsyncMock()
    service.robots_engine.get_sitemaps.return_value = ["https://site.com/sitemap.xml"]
    service.robots_engine.is_allowed.side_effect = lambda url: "blocked" not in url
    
    service.sitemap_engine = AsyncMock()
    service.sitemap_engine.discover_urls.return_value = ["https://site.com/page1", "https://site.com/page-blocked"]
    
    res = await service.run_discovery_session("https://site.com")
    
    assert res["dispatched"] == 1
    assert res["discovered"] == 2
    
    # Assert queued targets
    mock_repo.add_domain.assert_called_once()
    mock_queue.push_task.assert_called_once_with("single_url_audit", {"url": "https://site.com/page1"})

@pytest.mark.asyncio
async def test_discovery_session_crawler_fallback():
    mock_queue = AsyncMock()
    mock_crawler = AsyncMock()
    mock_repo = AsyncMock()
    
    service = DiscoveryService(mock_queue, mock_crawler, mock_repo)
    
    service.robots_engine = MagicMock()
    service.robots_engine.initialize = AsyncMock()
    service.robots_engine.get_sitemaps.return_value = []
    service.robots_engine.is_allowed.return_value = True
    
    service.sitemap_engine = AsyncMock()
    service.sitemap_engine.discover_urls.return_value = []
    
    mock_crawler.extract_links.return_value = ["https://site.com/fallback1"]
    
    res = await service.run_discovery_session("https://site.com")
    
    # Should use the fallback links crawler
    assert res["dispatched"] == 1
    assert res["discovered"] == 1
    mock_crawler.extract_links.assert_called_once_with("https://site.com")
    mock_queue.push_task.assert_called_once_with("single_url_audit", {"url": "https://site.com/fallback1"})


@pytest.mark.asyncio
async def test_discovery_session_duplicate_target_exception():
    mock_queue = AsyncMock()
    mock_crawler = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.add_domain.side_effect = Exception("Target already exists")
    
    service = DiscoveryService(mock_queue, mock_crawler, mock_repo)
    
    service.robots_engine = MagicMock()
    service.robots_engine.initialize = AsyncMock()
    service.robots_engine.get_sitemaps.return_value = ["https://site.com/sitemap.xml"]
    service.robots_engine.is_allowed.return_value = True
    
    service.sitemap_engine = AsyncMock()
    service.sitemap_engine.discover_urls.return_value = ["https://site.com/page1"]
    
    res = await service.run_discovery_session("https://site.com")
    assert res["dispatched"] == 1


@pytest.mark.asyncio
async def test_discovery_session_crawler_fallback_empty():
    mock_queue = AsyncMock()
    mock_crawler = AsyncMock()
    mock_crawler.extract_links.return_value = []
    mock_repo = AsyncMock()
    
    service = DiscoveryService(mock_queue, mock_crawler, mock_repo)
    
    service.robots_engine = MagicMock()
    service.robots_engine.initialize = AsyncMock()
    service.robots_engine.get_sitemaps.return_value = []
    service.robots_engine.is_allowed.return_value = True
    
    service.sitemap_engine = AsyncMock()
    service.sitemap_engine.discover_urls.return_value = []
    
    res = await service.run_discovery_session("https://site.com")
    assert res["dispatched"] == 0


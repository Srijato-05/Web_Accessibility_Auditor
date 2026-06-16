import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.site_audit import main

@pytest.fixture
def mock_db_engine():
    engine = MagicMock()
    mock_conn = AsyncMock()
    mock_begin_ctx = AsyncMock()
    mock_begin_ctx.__aenter__.return_value = mock_conn
    engine.begin.return_value = mock_begin_ctx
    engine.dispose = AsyncMock()
    return engine

@pytest.mark.asyncio
async def test_site_audit_cli_help(mock_db_engine):
    with patch("sys.argv", ["site_audit.py", "--help"]), \
         patch("auditor.site_audit.create_async_engine", return_value=mock_db_engine), \
         patch("builtins.print") as mock_print:
        await main()
        mock_print.assert_called()

@pytest.mark.asyncio
async def test_site_audit_cli_invalid_args(mock_db_engine):
    with patch("sys.argv", ["site_audit.py"]), \
         patch("auditor.site_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.site_audit.auditor_logger") as mock_logger:
        await main()
        mock_logger.error.assert_called_with("Usage: python site_audit.py <url>")

@pytest.mark.asyncio
async def test_site_audit_cli_success(mock_db_engine):
    mock_crawl = AsyncMock()
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["site_audit.py", "http://example.com"]), \
         patch("auditor.site_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.site_audit.AsyncSession", return_value=mock_ctx), \
         patch("auditor.site_audit.PlaywrightLinkExtractor"), \
         patch("auditor.site_audit.LinkDiscoveryService"), \
         patch("auditor.site_audit.CrawlService.run", mock_crawl):
         
        await main()
        mock_crawl.assert_called_once_with("http://example.com")

@pytest.mark.asyncio
async def test_site_audit_cli_execute_exception(mock_db_engine):
    mock_crawl = AsyncMock(side_effect=Exception("Crawl failed"))
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["site_audit.py", "http://example.com"]), \
         patch("auditor.site_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.site_audit.AsyncSession", return_value=mock_ctx), \
         patch("auditor.site_audit.PlaywrightLinkExtractor"), \
         patch("auditor.site_audit.LinkDiscoveryService"), \
         patch("auditor.site_audit.CrawlService.run", mock_crawl), \
         patch("auditor.site_audit.auditor_logger") as mock_logger:
         
        await main()
        mock_logger.critical.assert_called()

@pytest.mark.asyncio
async def test_site_audit_cli_db_exception(mock_db_engine):
    mock_db_engine.begin.side_effect = Exception("Connection refused")
    
    with patch("sys.argv", ["site_audit.py", "http://example.com"]), \
         patch("auditor.site_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.site_audit.auditor_logger") as mock_logger:
         
        await main()
        mock_logger.error.assert_called()

def test_site_audit_script_entrypoint():
    with patch("asyncio.run") as mock_run, \
         patch("sys.argv", ["site_audit.py", "http://example.com"]):
         
        with open("src/auditor/site_audit.py") as f:
            code = f.read()
        global_dict = {
            "__name__": "__main__",
            "__file__": "src/auditor/site_audit.py",
            "sys": sys,
            "os": os
        }
        try:
            exec(code, global_dict)
        except SystemExit:
            pass
        
        mock_run.assert_called_once()

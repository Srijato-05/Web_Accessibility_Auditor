import pytest
import sys
import os
import uuid
import glob
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.single_url import main

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
async def test_single_url_cli_help(mock_db_engine):
    with patch("sys.argv", ["single_url.py", "--help"]), \
         patch("auditor.single_url.create_async_engine", return_value=mock_db_engine), \
         patch("builtins.print") as mock_print:
        await main()
        mock_print.assert_called()

@pytest.mark.asyncio
async def test_single_url_cli_invalid_args(mock_db_engine):
    with patch("sys.argv", ["single_url.py"]), \
         patch("auditor.single_url.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.single_url.auditor_logger") as mock_logger:
        await main()
        mock_logger.error.assert_called_with("Usage: python single_url.py <url>")

@pytest.mark.asyncio
async def test_single_url_cli_success(mock_db_engine):
    mock_result = MagicMock()
    mock_result.id = uuid.uuid4()
    mock_result.status.value = "completed"
    
    mock_service = AsyncMock()
    mock_service.execute_audit.return_value = mock_result
    
    mock_reporter = AsyncMock()
    mock_reporter.generate_summary_report.return_value = {"html": "/exports/report.html"}
    
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["single_url.py", "http://example.com", "--no-neural"]), \
         patch("auditor.single_url.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.single_url.AsyncSession", return_value=mock_ctx), \
         patch("auditor.single_url.AuditService", return_value=mock_service), \
         patch("auditor.single_url.AuditReporter", return_value=mock_reporter):
         
        res_id = await main()
        assert res_id == mock_result.id
        mock_service.execute_audit.assert_called_once_with("http://example.com", skip_neural=True)

@pytest.mark.asyncio
async def test_single_url_cli_execute_exception(mock_db_engine):
    mock_service = AsyncMock()
    mock_service.execute_audit.side_effect = Exception("Audit failed")
    
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["single_url.py", "http://example.com"]), \
         patch("auditor.single_url.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.single_url.AsyncSession", return_value=mock_ctx), \
         patch("auditor.single_url.AuditService", return_value=mock_service), \
         patch("auditor.single_url.auditor_logger") as mock_logger:
         
        res_id = await main()
        assert res_id is None
        mock_logger.critical.assert_called()

@pytest.mark.asyncio
async def test_single_url_cli_db_exception(mock_db_engine):
    mock_db_engine.begin.side_effect = Exception("Connection refused")
    
    with patch("sys.argv", ["single_url.py", "http://example.com"]), \
         patch("auditor.single_url.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.single_url.auditor_logger") as mock_logger:
         
        res_id = await main()
        assert res_id is None
        mock_logger.error.assert_called()

def test_single_url_script_entrypoint():
    with patch("asyncio.run", return_value=uuid.uuid4()) as mock_run, \
         patch("sys.argv", ["single_url.py", "http://example.com"]), \
         patch("glob.glob", return_value=["/exports/report.json"]) as mock_glob, \
         patch("os.path.getctime", return_value=123.0), \
         patch("auditor.infrastructure.pdf_reporter.convert_json_to_pdf") as mock_convert, \
         patch("time.sleep") as mock_sleep:
         
        with open("src/auditor/single_url.py") as f:
            code = f.read()
        global_dict = {
            "__name__": "__main__",
            "__file__": "src/auditor/single_url.py",
            "sys": sys,
            "os": os
        }
        try:
            exec(code, global_dict)
        except SystemExit:
            pass
        
        mock_run.assert_called_once()
        mock_glob.assert_called()
        mock_convert.assert_called_with("/exports/report.json", "/exports/report.pdf")

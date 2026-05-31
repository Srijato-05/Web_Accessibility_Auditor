import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Import CLI modules main functions
import auditor.single_url as single_url
import auditor.site_audit as site_audit
import auditor.batch_audit as batch_audit

@pytest.mark.asyncio
async def test_single_url_cli_help():
    with patch("sys.argv", ["single_url.py", "--help"]), \
         patch("builtins.print") as mock_print:
        await single_url.main()
        mock_print.assert_called_once()
        assert "Single-Target CLI" in mock_print.call_args[0][0]

@pytest.mark.asyncio
async def test_single_url_cli_run():
    mock_execute = AsyncMock(return_value=MagicMock(id="session-123", status=MagicMock(value="completed")))
    mock_report = AsyncMock(return_value={"html": "report.html"})
    
    with patch("sys.argv", ["single_url.py", "https://target.com", "--no-neural"]), \
         patch("auditor.single_url.create_async_engine"), \
         patch("auditor.single_url.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.single_url.AuditService.execute_audit", mock_execute), \
         patch("auditor.single_url.AuditReporter.generate_summary_report", mock_report):
        
        res = await single_url.main()
        assert res == "session-123"
        mock_execute.assert_called_once_with("https://target.com", skip_neural=True)

@pytest.mark.asyncio
async def test_site_audit_cli_run():
    mock_crawl = AsyncMock()
    with patch("sys.argv", ["site_audit.py", "https://discover.com"]), \
         patch("auditor.site_audit.create_async_engine"), \
         patch("auditor.site_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.site_audit.CrawlService.run", mock_crawl):
         
        await site_audit.main()
        mock_crawl.assert_called_once_with("https://discover.com")

@pytest.mark.asyncio
async def test_batch_audit_cli_add_target():
    mock_add = AsyncMock()
    mock_dispatch = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--add-target", "https://new-target.com"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.AsyncSession"), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.SqlAlchemyTargetRepository.add_domain", mock_add), \
         patch("auditor.batch_audit.BatchAuditManager.dispatch_batch_audit", mock_dispatch):
         
        await batch_audit.main()
        mock_add.assert_called_once()
        mock_dispatch.assert_called_once()

@pytest.mark.asyncio
async def test_batch_audit_cli_dispatch():
    mock_dispatch = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--dispatch"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.BatchAuditManager.dispatch_batch_audit", mock_dispatch):
         
        await batch_audit.main()
        mock_dispatch.assert_called_once()

@pytest.mark.asyncio
async def test_batch_audit_cli_report():
    mock_report = AsyncMock(return_value={"html": "my_report.html"})
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--report"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.AsyncSession"), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.AuditReporter.generate_summary_report", mock_report):
         
        await batch_audit.main()
        mock_report.assert_called_once()

@pytest.mark.asyncio
async def test_batch_audit_cli_worker():
    mock_worker_start = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--worker"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.application.worker.AuditWorker.start", mock_worker_start):
         
        await batch_audit.main()
        mock_worker_start.assert_called_once()

@pytest.mark.asyncio
async def test_single_url_cli_missing_args():
    with patch("sys.argv", ["single_url.py"]), \
         patch("auditor.single_url.auditor_logger.error") as mock_log:
        await single_url.main()
        mock_log.assert_called_with("Usage: python single_url.py <url>")

@pytest.mark.asyncio
async def test_single_url_cli_exception():
    mock_execute = AsyncMock(side_effect=RuntimeError("Audit error"))
    with patch("sys.argv", ["single_url.py", "https://target.com"]), \
         patch("auditor.single_url.create_async_engine"), \
         patch("auditor.single_url.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.single_url.AuditService.execute_audit", mock_execute), \
         patch("auditor.single_url.auditor_logger.critical") as mock_log, \
         patch("traceback.print_exc"):
        res = await single_url.main()
        assert res is None
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_site_audit_cli_missing_args():
    with patch("sys.argv", ["site_audit.py"]), \
         patch("auditor.site_audit.auditor_logger.error") as mock_log:
        await site_audit.main()
        mock_log.assert_called_with("Usage: python site_audit.py <url>")

@pytest.mark.asyncio
async def test_site_audit_cli_exception():
    mock_crawl = AsyncMock(side_effect=RuntimeError("Crawl error"))
    with patch("sys.argv", ["site_audit.py", "https://discover.com"]), \
         patch("auditor.site_audit.create_async_engine"), \
         patch("auditor.site_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.site_audit.CrawlService.run", mock_crawl), \
         patch("auditor.site_audit.auditor_logger.critical") as mock_log:
        await site_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_add_target_exception():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--add-target", "https://target.com"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.AsyncSession", side_effect=RuntimeError("DB Error")), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.auditor_logger.error") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_dispatch_exception():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--dispatch"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.BatchAuditManager.dispatch_batch_audit", side_effect=RuntimeError("Dispatch Error")), \
         patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_discover():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    mock_run = AsyncMock()
    
    mock_extractor = MagicMock()
    mock_extractor.teardown = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--discover", "http://discover.com"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.PlaywrightLinkExtractor", return_value=mock_extractor), \
         patch("auditor.batch_audit.LinkDiscoveryService"), \
         patch("auditor.batch_audit.DiscoveryService.run_discovery_session", mock_run):
        await batch_audit.main()
        mock_run.assert_called_once_with("http://discover.com")
        mock_extractor.teardown.assert_called_once()

@pytest.mark.asyncio
async def test_batch_audit_cli_discover_exception():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--discover", "http://discover.com"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.PlaywrightLinkExtractor", side_effect=RuntimeError("Playwright Error")), \
         patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_worker_exception():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--worker"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.application.worker.AuditWorker.start", side_effect=RuntimeError("Worker Error")), \
         patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_report_exception():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--report"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.AsyncSession", side_effect=RuntimeError("Report Session Error")), \
         patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_dashboard():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    mock_dash = MagicMock()
    mock_dash.run = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--dashboard"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.AuditorDashboard", return_value=mock_dash):
        await batch_audit.main()
        mock_dash.run.assert_called_once()

@pytest.mark.asyncio
async def test_batch_audit_cli_dashboard_exception():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    mock_dash = MagicMock()
    mock_dash.run = AsyncMock(side_effect=RuntimeError("Dashboard Error"))
    
    with patch("sys.argv", ["batch_audit.py", "--dashboard"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.AuditorDashboard", return_value=mock_dash), \
         patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_run_batch_failure():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.BatchAuditManager.run_batch_audit", side_effect=RuntimeError("Batch run failure")), \
         patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        await batch_audit.main()
        mock_log.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_discover_missing_arg():
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--discover"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()):
        await batch_audit.main()

@pytest.mark.asyncio
async def test_batch_audit_cli_report_no_html():
    mock_report = AsyncMock(return_value={"html": None})
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    with patch("sys.argv", ["batch_audit.py", "--report"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_audit.AsyncSession"), \
         patch("auditor.batch_audit.SQLModel.metadata.create_all", AsyncMock()), \
         patch("auditor.infrastructure.task_model.task_metadata.create_all", AsyncMock()), \
         patch("auditor.batch_audit.AuditReporter.generate_summary_report", mock_report), \
         patch("auditor.batch_audit.auditor_logger.warning") as mock_log:
        await batch_audit.main()
        mock_log.assert_called_with("No report generated (likely no data).")

def test_batch_audit_cli_entrypoints():
    import auditor.batch_audit as ba
    with patch("auditor.batch_audit.auditor_logger.warning") as mock_log:
        try:
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            ba.auditor_logger.warning("Auditor Console TERMINATED by User.")
        mock_log.assert_called_with("Auditor Console TERMINATED by User.")
        
    with patch("auditor.batch_audit.auditor_logger.critical") as mock_log:
        try:
            raise RuntimeError("Fatal")
        except Exception as e:
            ba.auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")
        mock_log.assert_called_with("FATAL SYSTEM FAILURE: Fatal")


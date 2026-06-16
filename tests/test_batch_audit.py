import pytest
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.batch_audit import main

# Bypass sqlite pragma setup which uses listens_for
patch("sqlalchemy.event.listens_for", lambda *args, **kwargs: lambda f: f).start()
patch("auditor.presentation.api.cleanup_orphaned_targets", AsyncMock()).start()

@pytest.fixture
def mock_db_engine():
    engine = MagicMock()
    mock_conn = AsyncMock()
    mock_begin_ctx = AsyncMock()
    mock_begin_ctx.__aenter__.return_value = mock_conn
    engine.begin.return_value = mock_begin_ctx
    engine.dispose = AsyncMock()
    engine.sync_engine = MagicMock()
    return engine

@pytest.mark.asyncio
async def test_batch_audit_cli_help(mock_db_engine):
    with patch("sys.argv", ["batch_audit.py", "--help"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("builtins.print") as mock_print:
        await main()
        mock_print.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_status(mock_db_engine):
    mock_domain = MagicMock()
    mock_domain.url = "http://site.com"
    mock_domain.priority = 3
    mock_domain.retry_count = 0
    mock_domain.last_audit_at = None
    mock_domain.status.value = "active"
    mock_domain.last_error = "Some error"
    mock_domain.scan_profile = {"checkpoint": {"visited_urls": [1], "pending_queue": [2]}}
    
    mock_repo = AsyncMock()
    mock_repo.get_all_domains.return_value = [mock_domain]
    
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["batch_audit.py", "--status"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.batch_audit.AsyncSession", return_value=mock_ctx), \
         patch("builtins.print") as mock_print:
        await main()
        mock_print.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_prune(mock_db_engine):
    from auditor.domain.models import DomainStatus
    mock_domain = MagicMock()
    mock_domain.url = "http://site.com"
    mock_domain.status = DomainStatus.FAILED
    
    mock_repo = AsyncMock()
    mock_repo.get_all_domains.return_value = [mock_domain]
    
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["batch_audit.py", "--prune"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.batch_audit.AsyncSession", return_value=mock_ctx), \
         patch("auditor.batch_audit.auditor_logger") as mock_logger:
        await main()
        mock_logger.info.assert_called()

@pytest.mark.asyncio
async def test_batch_audit_cli_add_target(mock_db_engine):
    mock_repo = AsyncMock()
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    mock_orchestrator = AsyncMock()
    mock_orchestrator.dispatch_batch_audit = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--add-target", "http://new.com", "--priority", "1"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.batch_audit.AsyncSession", return_value=mock_ctx), \
         patch("auditor.batch_audit.BatchAuditManager", return_value=mock_orchestrator), \
         patch("auditor.batch_audit.auditor_logger") as mock_logger:
        await main()
        assert mock_repo.add_domain.called
        assert mock_orchestrator.dispatch_batch_audit.called

@pytest.mark.asyncio
async def test_batch_audit_cli_dispatch(mock_db_engine):
    mock_orchestrator = AsyncMock()
    mock_orchestrator.dispatch_batch_audit = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--dispatch"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.BatchAuditManager", return_value=mock_orchestrator):
        await main()
        assert mock_orchestrator.dispatch_batch_audit.called

@pytest.mark.asyncio
async def test_batch_audit_cli_discover(mock_db_engine):
    mock_discovery = AsyncMock()
    mock_discovery.run_discovery_session = AsyncMock()
    
    mock_extractor = MagicMock()
    mock_extractor.teardown = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--discover", "http://discover.com"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.PlaywrightLinkExtractor", return_value=mock_extractor), \
         patch("auditor.batch_audit.DiscoveryService", return_value=mock_discovery), \
         patch("auditor.batch_audit.AsyncSession"):
        await main()
        assert mock_discovery.run_discovery_session.called

@pytest.mark.asyncio
async def test_batch_audit_cli_worker(mock_db_engine):
    mock_worker = AsyncMock()
    mock_worker.start = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--worker"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.application.worker.AuditWorker", return_value=mock_worker):
        await main()
        assert mock_worker.start.called

@pytest.mark.asyncio
async def test_batch_audit_cli_report(mock_db_engine):
    mock_reporter = AsyncMock()
    mock_reporter.generate_summary_report.return_value = {"html": "/exports/report.html"}
    
    with patch("sys.argv", ["batch_audit.py", "--report"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.AuditReporter", return_value=mock_reporter), \
         patch("auditor.batch_audit.AsyncSession"), \
         patch("auditor.batch_audit.auditor_logger") as mock_logger:
        await main()
        assert mock_logger.info.called

@pytest.mark.asyncio
async def test_batch_audit_cli_dashboard(mock_db_engine):
    mock_dash = AsyncMock()
    mock_dash.run = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--dashboard"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.AuditorDashboard", return_value=mock_dash):
        await main()
        assert mock_dash.run.called

@pytest.mark.asyncio
async def test_batch_audit_cli_run(mock_db_engine):
    mock_orchestrator = AsyncMock()
    mock_orchestrator.run_batch_audit = AsyncMock()
    
    with patch("sys.argv", ["batch_audit.py", "--run"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.BatchAuditManager", return_value=mock_orchestrator):
        await main()
        assert mock_orchestrator.run_batch_audit.called

@pytest.mark.asyncio
async def test_batch_audit_cli_exception(mock_db_engine):
    with patch("sys.argv", ["batch_audit.py", "--run"]), \
         patch("auditor.batch_audit.create_async_engine", return_value=mock_db_engine), \
         patch("auditor.batch_audit.BatchAuditManager", side_effect=Exception("Critical error")), \
         patch("auditor.batch_audit.auditor_logger") as mock_logger:
        await main()
        assert mock_logger.critical.called

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.application.worker import AuditWorker
import sqlalchemy.event

# Globally bypass SQLite pragma listening in tests since engine is mocked
patch("sqlalchemy.event.listens_for", lambda *args, **kwargs: lambda f: f).start()

@pytest.mark.asyncio
async def test_worker_overload_and_backpressure():
    worker = AuditWorker("TEST-WORKER")
    
    # Mock system overloaded - True
    with patch("psutil.cpu_percent", return_value=90.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem.return_value.percent = 50.0
        overloaded, cpu, mem = worker._is_system_overloaded()
        assert overloaded is True
        assert cpu == 90.0
        
    # Mock system overloaded - False
    with patch("psutil.cpu_percent", return_value=10.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem.return_value.percent = 10.0
        overloaded, cpu, mem = worker._is_system_overloaded()
        assert overloaded is False
        
    # Mock exception in psutil
    with patch("psutil.cpu_percent", side_effect=Exception("CPU error")):
        overloaded, cpu, mem = worker._is_system_overloaded()
        assert overloaded is False
        assert cpu == 0.0

@pytest.mark.asyncio
async def test_worker_start_and_shutdown():
    mock_queue = MagicMock()
    mock_queue.connect = AsyncMock()
    mock_queue.reset_abandoned_tasks = AsyncMock()
    mock_queue.disconnect = AsyncMock()
    
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    
    worker = AuditWorker("TEST-WORKER", engine=mock_engine, queue=mock_queue)
    
    # Mock active loop that immediately exits on next check or CancelledError
    mock_queue.pop_task = AsyncMock(side_effect=asyncio.CancelledError())
    
    with patch.object(worker, "_is_system_overloaded", return_value=(False, 0.0, 0.0)):
        await worker.start()
    
    mock_queue.connect.assert_called_once()
    mock_queue.reset_abandoned_tasks.assert_called_once()
    mock_queue.disconnect.assert_called_once()
    mock_engine.dispose.assert_called_once()

@pytest.mark.asyncio
async def test_worker_process_tasks():
    mock_queue = MagicMock()
    mock_queue.connect = AsyncMock()
    mock_queue.reset_abandoned_tasks = AsyncMock()
    mock_queue.disconnect = AsyncMock()
    mock_queue.complete_task = AsyncMock()
    mock_queue.fail_task = AsyncMock()
    
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    
    worker = AuditWorker("TEST-WORKER", engine=mock_engine, queue=mock_queue)
    
    # Invalid task (missing url)
    invalid_task = {"id": "1", "type": "single_url_audit", "data": {}}
    await worker._process_task(invalid_task)
    # logger error is called, queue.fail_task is not called since we exit early (or log error)
    
    # Unknown task type
    unknown_task = {"id": "2", "type": "unknown_type", "data": {"url": "http://test.com"}}
    await worker._process_task(unknown_task)
    mock_queue.fail_task.assert_called_once_with("2", "Unknown task type: unknown_type")
    mock_queue.fail_task.reset_mock()
    
    # Single URL audit success
    single_task = {"id": "3", "type": "single_url_audit", "data": {"url": "http://test.com"}}
    with patch.object(worker, "_run_single_audit", AsyncMock()) as mock_single:
        await worker._process_task(single_task)
        mock_single.assert_called_once_with("http://test.com")
        mock_queue.complete_task.assert_called_once_with("3")
        mock_queue.complete_task.reset_mock()
        
    # Single URL audit failure (raises exception)
    with patch.object(worker, "_run_single_audit", AsyncMock(side_effect=ValueError("Audit failed"))):
        await worker._process_task(single_task)
        mock_queue.fail_task.assert_called_once_with("3", "Audit failed")
        mock_queue.fail_task.reset_mock()

@pytest.mark.asyncio
async def test_worker_run_site_audit_success():
    worker = AuditWorker("TEST-WORKER")
    
    mock_browser = MagicMock()
    mock_browser.start = AsyncMock()
    mock_browser.teardown = AsyncMock()
    
    mock_crawler = MagicMock()
    mock_crawler.teardown = AsyncMock()
    
    mock_run = AsyncMock()
    
    mock_session = AsyncMock()
    mock_exec_result = MagicMock()
    mock_target = MagicMock(id="123", url="http://site.com", status="active", scan_profile=None)
    # mock_target needs a dictionary for frequency_hours
    mock_target.frequency_hours = {"hours": 24}
    mock_exec_result.first.return_value = mock_target
    mock_session.exec.return_value = mock_exec_result
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("auditor.application.worker.AsyncSession", return_value=mock_ctx), \
         patch("auditor.application.worker.PlaywrightEngine", return_value=mock_browser), \
         patch("auditor.application.worker.PlaywrightLinkExtractor", return_value=mock_crawler), \
         patch("auditor.application.worker.CrawlService.run", mock_run):
        
        await worker._run_site_audit("http://site.com")
        
        mock_browser.start.assert_called_once()
        mock_run.assert_called_once_with("http://site.com")
        mock_browser.teardown.assert_called_once()
        mock_crawler.teardown.assert_called_once()

@pytest.mark.asyncio
async def test_worker_run_single_audit_timeout():
    worker = AuditWorker("TEST-WORKER")
    
    mock_browser = MagicMock()
    mock_browser.teardown = AsyncMock()
    
    mock_service = MagicMock()
    # Mock execute_audit with an asyncio timeout
    mock_service.execute_audit = AsyncMock(side_effect=asyncio.TimeoutError())
    
    with patch("auditor.application.worker.AsyncSession"), \
         patch("auditor.application.worker.PlaywrightEngine", return_value=mock_browser), \
         patch("auditor.application.worker.AuditService", return_value=mock_service):
         
        await worker._run_single_audit("http://site.com")
        mock_browser.teardown.assert_called_once()

@pytest.mark.asyncio
async def test_worker_start_overloaded():
    mock_engine = AsyncMock()
    worker = AuditWorker("TEST-WORKER", engine=mock_engine)
    
    # First check: overloaded = True -> sleeps
    # Second check: raise CancelledError to break loop
    call_count = 0
    def mock_overloaded():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return True, 90.0, 90.0
        raise asyncio.CancelledError()
        
    with patch.object(worker, "_is_system_overloaded", side_effect=mock_overloaded), \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep, \
         patch.object(worker.queue, "connect", AsyncMock()), \
         patch.object(worker.queue, "reset_abandoned_tasks", AsyncMock()), \
         patch.object(worker.queue, "disconnect", AsyncMock()), \
         patch.object(worker.engine, "dispose", AsyncMock()):
         
        await worker.start()
        mock_sleep.assert_called_with(5)

@pytest.mark.asyncio
async def test_worker_start_empty_pop():
    mock_engine = AsyncMock()
    worker = AuditWorker("TEST-WORKER", engine=mock_engine)
    
    # First pop: returns None
    # Second pop: raises CancelledError
    call_count = 0
    async def mock_pop(timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return None
        raise asyncio.CancelledError()
        
    with patch.object(worker, "_is_system_overloaded", return_value=(False, 0, 0)), \
         patch.object(worker.queue, "pop_task", side_effect=mock_pop), \
         patch.object(worker.queue, "connect", AsyncMock()), \
         patch.object(worker.queue, "reset_abandoned_tasks", AsyncMock()), \
         patch.object(worker.queue, "disconnect", AsyncMock()), \
         patch.object(worker.engine, "dispose", AsyncMock()):
         
        await worker.start()

@pytest.mark.asyncio
async def test_worker_process_full_site_task():
    mock_queue = MagicMock()
    mock_queue.complete_task = AsyncMock()
    
    worker = AuditWorker("TEST-WORKER", queue=mock_queue)
    task = {"id": "1", "type": "full_site_audit", "data": {"url": "http://test.com"}}
    
    with patch.object(worker, "_run_site_audit", AsyncMock()) as mock_site:
        await worker._process_task(task)
        mock_site.assert_called_once_with("http://test.com")
        mock_queue.complete_task.assert_called_once_with("1")

@pytest.mark.asyncio
async def test_worker_run_site_audit_exception():
    worker = AuditWorker("TEST-WORKER")
    
    mock_browser = MagicMock()
    mock_browser.start = AsyncMock()
    mock_browser.teardown = AsyncMock()
    
    mock_crawler = MagicMock()
    mock_crawler.teardown = AsyncMock()
    
    mock_run = AsyncMock(side_effect=RuntimeError("Crawl failed"))
    
    mock_session = AsyncMock()
    mock_exec_result = MagicMock()
    mock_target = MagicMock(id="123", url="http://site.com", status="active", scan_profile=None)
    mock_target.frequency_hours = {"hours": 24}
    mock_exec_result.first.return_value = mock_target
    mock_session.exec.return_value = mock_exec_result
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("auditor.application.worker.AsyncSession", return_value=mock_ctx), \
         patch("auditor.application.worker.PlaywrightEngine", return_value=mock_browser), \
         patch("auditor.application.worker.PlaywrightLinkExtractor", return_value=mock_crawler), \
         patch("auditor.application.worker.CrawlService.run", mock_run), \
         patch.object(worker.logger, "exception") as mock_exc:
        
        await worker._run_site_audit("http://site.com")
        mock_exc.assert_called_once()

@pytest.mark.asyncio
async def test_worker_run_single_audit_exception():
    worker = AuditWorker("TEST-WORKER")
    
    mock_browser = MagicMock()
    mock_browser.teardown = AsyncMock()
    
    mock_service = MagicMock()
    mock_service.execute_audit = AsyncMock(side_effect=RuntimeError("Single audit failed"))
    
    with patch("auditor.application.worker.AsyncSession"), \
         patch("auditor.application.worker.PlaywrightEngine", return_value=mock_browser), \
         patch("auditor.application.worker.AuditService", return_value=mock_service), \
         patch.object(worker.logger, "exception") as mock_exc:
         
        await worker._run_single_audit("http://site.com")
        mock_exc.assert_called_once()

def test_worker_cli_entrypoint():
    with patch("asyncio.run") as mock_run:
        with open("src/auditor/application/worker.py") as f:
            code = f.read()
        global_dict = {
            "__name__": "__main__",
            "__file__": "src/auditor/application/worker.py",
            "psutil": MagicMock(),
            "os": MagicMock(),
            "sys": MagicMock()
        }
        try:
            exec(code, global_dict)
        except SystemExit:
            pass
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_worker_overload_mem_only():
    worker = AuditWorker("TEST-WORKER")
    with patch("psutil.cpu_percent", return_value=10.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem.return_value.percent = 90.0
        overloaded, cpu, mem = worker._is_system_overloaded()
        assert overloaded is True
        assert mem == 90.0

@pytest.mark.asyncio
async def test_worker_site_audit_checkpoint_callback():
    worker = AuditWorker("TEST-WORKER")
    
    captured_callback = None
    class FakeCrawlService:
        def __init__(self, *args, **kwargs):
            nonlocal captured_callback
            captured_callback = kwargs.get("checkpoint_callback")
        async def run(self, url):
            pass
            
    mock_session = AsyncMock()
    mock_target = MagicMock()
    mock_target.scan_profile = None # will be set to {}
    
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.return_value = mock_target
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    mock_browser = MagicMock()
    mock_browser.start = AsyncMock()
    mock_browser.teardown = AsyncMock()
    
    mock_crawler = MagicMock()
    mock_crawler.teardown = AsyncMock()
    
    with patch("auditor.application.worker.AsyncSession", return_value=mock_ctx), \
         patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.application.worker.PlaywrightEngine", return_value=mock_browser), \
         patch("auditor.application.worker.PlaywrightLinkExtractor", return_value=mock_crawler), \
         patch("auditor.application.worker.CrawlService", FakeCrawlService):
         
        await worker._run_site_audit("http://site.com")
        
        # Now execute the captured callback
        assert captured_callback is not None
        
        # Case 1: state is not None
        await captured_callback({"page": 1})
        assert mock_target.scan_profile["checkpoint"] == {"page": 1}
        
        # Case 2: state is None
        await captured_callback(None)
        assert "checkpoint" not in mock_target.scan_profile
        
        # Case 3: Exception in callback
        mock_repo.get_domain_by_url.side_effect = Exception("Db failure")
        await captured_callback({"page": 2}) # should log warning and not raise

@pytest.mark.asyncio
async def test_worker_start_general_exception_loop():
    mock_engine = AsyncMock()
    worker = AuditWorker("TEST-WORKER", engine=mock_engine)
    
    call_count = 0
    async def mock_pop(timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Temporary queue failure")
        raise asyncio.CancelledError()
        
    with patch.object(worker, "_is_system_overloaded", return_value=(False, 0, 0)), \
         patch.object(worker.queue, "pop_task", side_effect=mock_pop), \
         patch.object(worker.queue, "connect", AsyncMock()), \
         patch.object(worker.queue, "reset_abandoned_tasks", AsyncMock()), \
         patch.object(worker.queue, "disconnect", AsyncMock()), \
         patch.object(worker.engine, "dispose", AsyncMock()), \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep:
         
        await worker.start()
        mock_sleep.assert_called_with(1)

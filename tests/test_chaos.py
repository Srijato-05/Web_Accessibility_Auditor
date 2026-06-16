import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from auditor.application.worker import AuditWorker
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.domain.exceptions import AuditFailedError, EngineError

@pytest.mark.asyncio
async def test_worker_chaos_redis_failure():
    """Simulate Redis connection dropping during worker loop."""
    worker = AuditWorker(worker_id="chaos-1")
    
    # Mock queue to fail on first pull, succeed on second, return None on third
    worker.queue.pop_task = AsyncMock(side_effect=[
        Exception("Redis connection reset by peer"),
        {"task_id": "t1", "payload": {"url": "http://example.com"}},
        None
    ])
    
    # Mock audit execution
    mock_audit_service = MagicMock()
    mock_audit_service.execute_audit = AsyncMock()
    
    with patch("auditor.application.worker.AuditService", return_value=mock_audit_service), \
         patch("auditor.application.worker.asyncio.sleep", AsyncMock()), \
         patch.object(worker, "_is_system_overloaded", return_value=(False, 0.0, 0.0)): # skip sleep for fast test
        
        # We need a way to stop the infinite loop. We'll set active to False after 3 iterations
        call_count = 0
        original_pop = worker.queue.pop_task
        async def mock_pop(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                worker.stop()
            return await original_pop(*args, **kwargs)
            
        worker.queue.pop_task = mock_pop
        
        await worker.run()
        
        # The worker should survive the exception and continue processing
        assert mock_audit_service.execute_audit.call_count == 1

@pytest.mark.asyncio
async def test_worker_chaos_database_lock():
    """Simulate SQLite database locked exception during checkpoint commit."""
    worker = AuditWorker(worker_id="chaos-2")
    
    worker.queue.pop_task = AsyncMock(side_effect=[
        {"task_id": "t1", "payload": {"url": "http://example.com", "session_id": "uuid"}},
        None
    ])
    
    mock_audit_service = MagicMock()
    mock_audit_service.execute_audit = AsyncMock()
    
    # Simulate DB commit failure
    worker.queue.db_engine = MagicMock()
    # It will fail on the checkpoint callback
    
    with patch("auditor.application.worker.AuditService", return_value=mock_audit_service), \
         patch("auditor.application.worker.asyncio.sleep", AsyncMock()), \
         patch.object(worker, "_is_system_overloaded", return_value=(False, 0.0, 0.0)), \
         patch("auditor.application.worker.AsyncSession") as mock_session_ctx:
        
        mock_session = MagicMock()
        mock_session.commit = AsyncMock(side_effect=Exception("database is locked"))
        mock_session_ctx.return_value.__aenter__.return_value = mock_session
        
        worker.stop() # stop immediately after 1 iter
        worker._active = True
        
        # Stop the worker loop when queue is exhausted to prevent infinite loop / CPU spin
        call_count = 0
        original_pop = worker.queue.pop_task
        async def mock_pop(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                worker.stop()
            return await original_pop(*args, **kwargs)
        worker.queue.pop_task = mock_pop
        
        await worker.run()
        
        # The audit should still run even if checkpoint commit fails (it logs error)
        assert mock_audit_service.execute_audit.call_count == 1

@pytest.mark.asyncio
async def test_playwright_engine_chaos_timeout():
    """Simulate Playwright page loading timeout."""
    engine = PlaywrightEngine(uuid4())
    
    mock_browser = MagicMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_page.goto = AsyncMock(side_effect=Exception("Timeout 30000ms exceeded."))
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    
    engine.browser = mock_browser
    
    with pytest.raises(EngineError) as exc:
        await engine.scan_url("http://example.com")
        
    assert "Timeout" in str(exc.value)

@pytest.mark.asyncio
async def test_playwright_engine_chaos_browser_crash():
    """Simulate Playwright browser crashing entirely."""
    engine = PlaywrightEngine(uuid4())
    
    # If the browser is None, it should try to start it, let's mock start to fail
    engine.start = AsyncMock(side_effect=Exception("Browser closed unexpectedly"))
    
    with pytest.raises(EngineError) as exc:
        await engine.scan_url("http://example.com")
        
    assert "Browser closed unexpectedly" in str(exc.value)

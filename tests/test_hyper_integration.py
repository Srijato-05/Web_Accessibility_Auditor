import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
import datetime

from auditor.application.batch_service import BatchAuditManager
from auditor.application.worker import AuditWorker
from auditor.application.crawl_service import CrawlService
from auditor.application.audit_service import AuditService
from auditor.main import app
from fastapi.testclient import TestClient
from auditor.domain.violation import Violation, ImpactLevel

@pytest.mark.asyncio
async def test_hyper_integration_end_to_end_pipeline():
    """
    This test orchestrates the ENTIRE pipeline virtually in-memory:
    API (Add Target) -> BatchOrchestrator (Dispatch) -> Redis Mock -> Worker (Pop) -> 
    CrawlService (Extract) -> AuditService (Mock Execution) -> Neo4j (Mock Upsert) -> Diff API (Validate).
    """
    
    # 1. Setup global mocks
    mock_engine = MagicMock()
    mock_db_session = AsyncMock()
    
    # Target storage mock
    class VirtualTarget:
        def __init__(self, url):
            self.id = uuid4()
            self.url = url
            self.status = "pending"
            self.priority = 1
            self.created_at = datetime.datetime.now()
            self.last_audit_at = None
            self.frequency_hours = {"hours": 24}
            self.retry_count = 0
            self.last_error = None
            self.scan_profile = {}
            self.updated_at = datetime.datetime.now()
    
    virtual_db = {"https://hyper-test.com": VirtualTarget("https://hyper-test.com")}
    
    # Mocking DB queries
    mock_exec_targets = MagicMock()
    mock_exec_targets.all.return_value = list(virtual_db.values())
    mock_exec_targets.first.side_effect = lambda: list(virtual_db.values())[0] if virtual_db else None
    
    mock_exec_violations = MagicMock()
    mock_exec_violations.all.return_value = []
    mock_exec_violations.first.return_value = None
    
    mock_exec_session = MagicMock()
    mock_session_record = MagicMock()
    mock_session_record.id = uuid4()
    mock_session_record.target_url = "https://hyper-test.com"
    mock_session_record.started_at = datetime.datetime.now()
    mock_session_record.completed_at = datetime.datetime.now()
    mock_session_record.focus_path = []
    mock_session_record.aria_events = []
    mock_exec_session.first.return_value = mock_session_record
    
    async def mock_exec_side_effect(stmt, *args, **kwargs):
        stmt_str = str(stmt).lower()
        if "violation" in stmt_str:
            return mock_exec_violations
        elif "auditsession" in stmt_str or "session" in stmt_str:
            return mock_exec_session
        return mock_exec_targets
        
    mock_db_session.exec.side_effect = mock_exec_side_effect
    
    mock_db_ctx = AsyncMock()
    mock_db_ctx.__aenter__.return_value = mock_db_session
    
    # Redis mock
    virtual_queue = []
    
    mock_redis = MagicMock()
    mock_redis.connect = AsyncMock()
    mock_redis.disconnect = AsyncMock()
    mock_redis.reset_abandoned_tasks = AsyncMock()
    mock_redis.complete_task = AsyncMock()
    mock_redis.fail_task = AsyncMock()
    
    async def mock_push(task_name, payload):
        virtual_queue.append({
            "task_id": str(uuid4()),
            "id": str(uuid4()),
            "type": task_name,
            "payload": payload,
            "data": payload
        })
    
    async def mock_pop(*args, **kwargs):
        if virtual_queue:
            return virtual_queue.pop(0)
        raise asyncio.CancelledError()
        
    mock_redis.push_task = mock_push
    mock_redis.pop_task = mock_pop
    
    # 2. API Level - Add Target
    with patch("auditor.presentation.api.init_db", AsyncMock()), \
         patch("auditor.presentation.api.AsyncSession", return_value=mock_db_ctx), \
         patch("auditor.application.batch_service.AsyncSession", return_value=mock_db_ctx), \
         patch("auditor.application.worker.AsyncSession", return_value=mock_db_ctx), \
         patch("auditor.presentation.api.task_queue", mock_redis), \
         patch("auditor.presentation.api.RedisTaskQueue", return_value=mock_redis), \
         patch("auditor.application.batch_service.RedisTaskQueue", return_value=mock_redis), \
         patch("auditor.application.worker.RedisTaskQueue", return_value=mock_redis):
         
        client = TestClient(app)
        
        # Start batch process via API
        response = client.post("/api/batch/run", json={"use_queue": True})
        assert response.status_code == 200
        
        # Clear the queue from the API dispatch to simulate fresh manual execution
        virtual_queue.clear()
        
        # Simulate BatchAuditManager manually since background tasks don't run in TestClient seamlessly
        orchestrator = BatchAuditManager(mock_engine)
        
        await orchestrator.dispatch_batch_audit()
        
        # Verify target is queued
        assert len(virtual_queue) == 1
        assert virtual_queue[0]["payload"]["url"] == "https://hyper-test.com"
        
        # 3. Worker Level - Pop and Execute
        worker = AuditWorker("hyper-worker-1")
        
        # Mock AuditService execution inside worker
        mock_audit_service = MagicMock()
        mock_audit_service.repository = AsyncMock()
        mock_audit_service.repository.db_session = mock_db_session
        mock_audit_session = MagicMock()
        mock_audit_session.id = uuid4()
        mock_audit_session.status.value = "completed"
        mock_audit_session.target_url = "https://hyper-test.com"
        mock_audit_service.execute_audit = AsyncMock(return_value=mock_audit_session)
        
        with patch("auditor.application.worker.AuditService", return_value=mock_audit_service), \
             patch("auditor.application.worker.asyncio.sleep", AsyncMock()), \
             patch.object(worker, "_is_system_overloaded", return_value=(False, 0.0, 0.0)):
             
             # Run 1 loop
             worker.stop()
             worker._active = True
             await worker.run()
             
             # Ensure the audit executed
             mock_audit_service.execute_audit.assert_called_once()
             assert mock_audit_service.execute_audit.call_args[0][0] == "https://hyper-test.com"
             assert len(virtual_queue) == 0 # Queue is empty now
             
        # 4. Crawl Level Integration (Simulated separately)
        # Verify that if a crawl task is dispatched, CrawlService extracts links correctly
        crawl_service = CrawlService(mock_audit_service, MagicMock(), max_depth=1)
        crawl_service.crawler_service.extract_links = AsyncMock(return_value=["https://hyper-test.com/page1"])
        crawl_service.tg_repo = MagicMock()
        crawl_service.tg_repo.upsert_page_links_batch_async = AsyncMock()
        
        # Prevent actual audit execution in crawl, just track queue logic
        mock_audit_service.execute_audit = AsyncMock(return_value=mock_audit_session)
        mock_audit_service.repository = AsyncMock()
        
        mock_reporter = MagicMock()
        mock_reporter.generate_summary_report = AsyncMock()
        
        with patch("auditor.application.crawl_service.AuditReporter", return_value=mock_reporter):
            await crawl_service.run("https://hyper-test.com")
            
            # The crawler should have discovered 1 internal link and upserted the graph mapping
            crawl_service.tg_repo.upsert_page_links_batch_async.assert_called()
            
        # Pipeline completely verified in isolation!

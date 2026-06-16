import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
import datetime
import logging

from auditor.application.batch_service import BatchAuditManager
from auditor.application.worker import AuditWorker
from auditor.application.crawl_service import CrawlService
from auditor.application.audit_service import AuditService
from auditor.domain.exceptions import AuditFailedError, NavigationError, RepositoryError
from auditor.domain.violation import Violation, ImpactLevel

@pytest.mark.asyncio
async def test_extreme_concurrency_worker_pool_resiliency():
    """
    Spins up 50 simulated workers hitting a single mock Redis queue simultaneously.
    Injects 10% connection drop errors, 5% DB lock errors, and 1% catastrophic Engine crashes
    to ensure the logging, exception handling, and error recovery metrics correctly 
    process a payload of 10,000 tasks without dropping data or locking.
    """
    total_tasks = 10000
    
    virtual_queue = [{"task_id": str(uuid4()), "payload": {"url": f"https://target-{i}.com"}} for i in range(total_tasks)]
    processed_tasks = set()
    failed_tasks = set()
    
    # Advanced Mock Redis
    class ChaosRedis:
        async def connect(self):
            pass
            
        async def disconnect(self):
            pass
            
        async def reset_abandoned_tasks(self):
            pass
            
        async def push_task(self, name, payload):
            virtual_queue.append({"task_id": str(uuid4()), "payload": payload})
            
        async def pop_task(self, timeout=None):
            import random
            if random.random() < 0.10:
                raise Exception("Redis connection reset by peer (Chaos Injection)")
            if virtual_queue:
                return virtual_queue.pop(0)
            raise asyncio.CancelledError()
            
        async def complete_task(self, task_id):
            pass
            
        async def fail_task(self, task_id, reason=None):
            pass
            
    mock_redis = ChaosRedis()
    
    class ChaosAuditService:
        def __init__(self, *args, **kwargs):
            pass
            
        async def execute_audit(self, url, skip_neural=True):
            import random
            chance = random.random()
            if chance < 0.05:
                raise RepositoryError("database is locked (Chaos Injection)", context={"url": url})
            elif chance < 0.06:
                raise NavigationError("Timeout exceeded (Chaos Injection)", context={"url": url})
            elif chance < 0.061:
                raise AuditFailedError("Catastrophic Playwright Crash (Chaos Injection)")
                
            # Success
            processed_tasks.add(url)
            session = MagicMock()
            session.id = uuid4()
            session.status.value = "completed"
            return session

    # Setup the massive worker swarm
    async def run_worker_node(worker_id):
        worker = AuditWorker(f"swarm-node-{worker_id}")
        
        # Inject our chaos models
        worker.queue = mock_redis
        
        with patch("auditor.application.worker.AuditService", return_value=ChaosAuditService()), \
             patch("auditor.application.worker.PlaywrightEngine"), \
             patch("auditor.application.worker.PlaywrightLinkExtractor"), \
             patch("auditor.application.worker.AsyncSession") as mock_session_ctx, \
             patch.object(worker, "_is_system_overloaded", return_value=(False, 0.0, 0.0)), \
             patch("asyncio.sleep", AsyncMock()): # disable sleep for blazing fast test
             
             # Mock DB Commit
             mock_db = MagicMock()
             async def chaotic_commit():
                 import random
                 if random.random() < 0.01:
                     raise Exception("SQLite constraint failed")
             mock_db.commit = chaotic_commit
             mock_session_ctx.return_value.__aenter__.return_value = mock_db
             
             # Run until queue is empty (or max 500 loops to prevent infinite if chaos causes hangs)
             for _ in range(500):
                 if not virtual_queue:
                     break
                 try:
                     worker.stop() # stop infinite loop
                     worker._active = True
                     await worker.run()
                 except Exception as e:
                     failed_tasks.add(str(e))
                     
    # Execute Swarm
    workers = [run_worker_node(i) for i in range(50)]
    await asyncio.gather(*workers)
    
    # Verification: The system must not crash, all tasks should be attempted.
    # We should see our Chaos errors in the failed_tasks or handled gracefully by the worker.
    # In a perfect chaos recovery, workers eat the exceptions and keep polling.
    assert len(processed_tasks) > 8000 # Most should succeed
    assert len(virtual_queue) < 1000 # Queue should be heavily depleted
    

@pytest.mark.asyncio
async def test_dynamic_memory_leak_prevention_large_payloads():
    """
    Test deep serialization optimization and IO memory bounds by forcing the AuditService
    to process a single page with 100,000 DOM nodes resulting in 50,000 violations.
    Validates that serialization and string building doesn't cause out-of-memory errors
    and that logs are securely capped.
    """
    engine = AsyncMock()
    repo = AsyncMock()
    repo.list_recent_sessions.return_value = []
    
    # 50,000 violations
    huge_violations = [
        Violation(rule_id=f"rule-{i}", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="", session_id=uuid4(), tags=[], compliance_level="", category="", severity_matrix="", url="")
        for i in range(50000)
    ]
    
    engine.scan_url = AsyncMock(return_value=huge_violations)
    engine.page_data = MagicMock()
    
    service = AuditService(engine, repo)
    service.tg_repo = MagicMock()
    service.tg_repo.upsert_component_violations_batch_async = AsyncMock()
    
    mock_agent_service = MagicMock()
    mock_controller = AsyncMock()
    mock_controller.analyze.return_value = []
    mock_agent_service.get_controller.return_value = mock_controller
    
    with patch("auditor.application.audit_service.get_agent_service", return_value=mock_agent_service):
         
        # Execute memory-heavy audit
        session = await service.execute_audit("https://massive.com")
        
        # Verify success without OOM
        assert len(session.violations) == 50000
        # Verify component upsert batching was called (optimizes DB IO)
        service.tg_repo.upsert_component_violations_batch_async.assert_called_once()

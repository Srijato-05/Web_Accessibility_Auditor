"""
AUDITOR WORKER: DISTRIBUTED AUDIT EXECUTION ENGINE (W-Z10)
=========================================================

Role: Asynchronous task consumer.
Responsibilities:
  - Subscribing to Redis task queue.
  - Initializing browser and persistence layers.
  - Executing full-site or single-URL audits.
  - Reporting completion/failure back to the ledger.
"""

import asyncio
import json
import os
import sys
import logging
from typing import Dict, Any, Optional

# IDE PATH RECONCILIATION
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore

from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository # type: ignore
from auditor.infrastructure.playwright_engine import PlaywrightEngine # type: ignore
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor # type: ignore
from auditor.domain.crawler import LinkDiscoveryService # type: ignore
from auditor.application.audit_service import AuditService # type: ignore
from auditor.application.crawl_service import CrawlService # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"
REDIS_URL = "redis://localhost:6379"

class AuditWorker:
    """
    Autonomous worker node for the Accessibility Auditor platform.
    """
    
    def __init__(self, worker_id: str = "WORKER-01", engine: Optional[Any] = None, queue: Optional[RedisTaskQueue] = None):
        self.worker_id = worker_id
        self.queue = queue if queue else RedisTaskQueue(REDIS_URL)
        self.engine = engine if engine else create_async_engine(DATABASE_URL, echo=False)
        self.logger = auditor_logger.getChild(f"Worker.{worker_id}")
        self._active = True

    async def start(self):
        """Main event loop for task consumption."""
        self.logger.info(f"Audit Worker {self.worker_id} ONLINE. Awaiting tasks...")
        await self.queue.connect()
        
        try:
            while self._active:
                task = await self.queue.pop_task(timeout=5)
                if not task:
                    continue
                
                await self._process_task(task)
        except asyncio.CancelledError:
            self.logger.warning("Worker shutdown initiated.")
        finally:
            await self.queue.disconnect()
            await self.engine.dispose()

    async def _process_task(self, task: Dict[str, Any]):
        """Dispatches tasks to the appropriate service layer."""
        task_type = task.get("type")
        data = task.get("data", {})
        url = data.get("url")
        
        if not url:
            self.logger.error("Invalid Task: Missing URL.")
            return

        self.logger.info(f"Task Received [{task_type}]: {url}")
        
        if task_type == "full_site_audit":
            await self._run_site_audit(url)
        else:
            self.logger.warning(f"Unknown task type: {task_type}")

    async def _run_site_audit(self, url: str):
        """Executes a comprehensive site audit with persistence isolation."""
        async with AsyncSession(self.engine) as db_session:
            # 1. Initialize Infrastructure Components
            repo = SqlAlchemyAuditRepository(db_session)
            browser = PlaywrightEngine()
            crawler = PlaywrightLinkExtractor()
            
            # 2. Assemble Service Layer
            audit_service = AuditService(browser, repo)
            discovery_service = LinkDiscoveryService(crawler)
            
            crawl_orchestrator = CrawlService(
                audit_service=audit_service,
                crawler_service=discovery_service,
                max_depth=2,
                max_pages=20,
                concurrency=3
            )
            
            # 3. Execution
            try:
                self.logger.info(f"--- [ STARTING DISTRIBUTED AUDIT: {url} ] ---")
                await crawl_orchestrator.process_audit_session(url)
                self.logger.info(f"--- [ AUDIT COMPLETE: {url} ] ---")
            except Exception as e:
                self.logger.error(f"Distributed Audit Failure [{url}]: {e}")

if __name__ == "__main__":
    worker = AuditWorker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        pass

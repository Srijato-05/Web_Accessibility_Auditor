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
import os
import sys
from typing import Dict, Any, Optional, Tuple
from uuid import uuid4
import psutil # type: ignore

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
from auditor.shared.paths import DATABASE_URL, REDIS_URL # type: ignore

class AuditWorker:
    """
    Autonomous worker node for the Accessibility Auditor platform.
    """
    
    def __init__(self, worker_id: str = "WORKER-01", engine: Optional[Any] = None, queue: Optional[RedisTaskQueue] = None):
        self.worker_id = worker_id
        self.engine = engine if engine else create_async_engine(DATABASE_URL, connect_args={"timeout": 30.0}, echo=False)
        
        # WAL journal mode optimization for SQLite high concurrency
        from sqlalchemy import event # type: ignore
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
            except Exception:
                pass
            finally:
                cursor.close()

        self.queue = queue if queue else RedisTaskQueue(REDIS_URL, db_engine=self.engine)
        self.logger = auditor_logger.getChild(f"Worker.{worker_id}")
        self._active = True

    def _is_system_overloaded(self) -> Tuple[bool, float, float]:
        try:
            # interval=None does a non-blocking check
            cpu_load = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            mem_load = memory_info.percent
            threshold = float(os.getenv("AUDITOR_BACKPRESSURE_THRESHOLD", "85.0"))
            if cpu_load > threshold or mem_load > threshold:
                return True, cpu_load, mem_load
            return False, cpu_load, mem_load
        except Exception:
            return False, 0.0, 0.0

    async def run(self):
        """Alias for start to support legacy or alternative test interface calling run()."""
        await self.start()

    def stop(self):
        """Stops the worker loop."""
        self._active = False

    async def start(self):
        """Main event loop for task consumption."""
        self.logger.info(f"Audit Worker {self.worker_id} ONLINE. Awaiting tasks...")
        await self.queue.connect()
        
        try:
            # Phase XIII: Self-Healing Recovery
            await self.queue.reset_abandoned_tasks()

            while self._active:
                overloaded, cpu, mem = self._is_system_overloaded()
                if overloaded:
                    self.logger.warning(
                        f"System Overloaded (CPU: {cpu}%, MEM: {mem}%). Deferring task consumption (sleeping 5s)..."
                    )
                    await asyncio.sleep(5)
                    continue

                try:
                    task = await self.queue.pop_task(timeout=5)
                    if not task:
                        continue
                    
                    await self._process_task(task)
                except asyncio.CancelledError:
                    raise
                except Exception as loop_err:
                    self.logger.error(f"Worker Loop Exception: {loop_err}")
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.warning("Worker shutdown initiated.")
        finally:
            await self.queue.disconnect()
            await self.engine.dispose()

    async def _process_task(self, task: Dict[str, Any]):
        """Dispatches tasks to the appropriate service layer."""
        task_id = task.get("id") or task.get("task_id")
        task_type = task.get("type") or "single_url_audit"
        data = task.get("data") or task.get("payload") or {}
        url = data.get("url")
        
        if not url:
            self.logger.error("Invalid Task: Missing URL.")
            return

        try:
            if task_type == "full_site_audit":
                await self._run_site_audit(url)
            elif task_type == "single_url_audit":
                await self._run_single_audit(url)
            else:
                self.logger.warning(f"Unknown task type: {task_type}")
                await self.queue.fail_task(task_id, f"Unknown task type: {task_type}")
                return
            
            await self.queue.complete_task(task_id)
        except Exception as e:
            self.logger.exception(f"Task Execution Failure [{task_id}]")
            await self.queue.fail_task(task_id, str(e))

    async def _run_site_audit(self, url: str):
        """Executes a comprehensive site audit with persistence isolation."""
        async with AsyncSession(self.engine) as db_session:
            # 1. Fetch Target Registry Profile
            from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
            target_repo = SqlAlchemyTargetRepository(db_session)
            domain = await target_repo.get_domain_by_url(url)
            profile = domain.scan_profile if (domain and domain.scan_profile) else {}
            
            # Extract parameters from profile with fallback defaults
            max_depth = profile.get("depth", 2)
            max_pages = profile.get("max_pages", 20)
            concurrency = profile.get("concurrency", 3)

            # Resilient Checkpoint Callback
            target_url = url
            async def checkpoint_cb(state: Any):
                try:
                    async with AsyncSession(self.engine) as cb_session:
                        cb_repo = SqlAlchemyTargetRepository(cb_session)
                        db_domain = await cb_repo.get_domain_by_url(target_url)
                        if db_domain:
                            if db_domain.scan_profile is None:
                                db_domain.scan_profile = {}
                            if state is None:
                                db_domain.scan_profile.pop("checkpoint", None)
                            else:
                                db_domain.scan_profile["checkpoint"] = state
                            await cb_repo.update_domain(db_domain)
                            await cb_session.commit()
                except Exception as cb_err:
                    self.logger.warning(f"Resilient Checkpoint Save Failure in Worker for {target_url}: {cb_err}")

            # 2. Initialize Infrastructure Components
            repo = SqlAlchemyAuditRepository(db_session)
            browser = PlaywrightEngine(uuid4(), config=profile)
            crawler = PlaywrightLinkExtractor()
            
            # 3. Assemble Service Layer
            audit_service = AuditService(browser, repo)
            discovery_service = LinkDiscoveryService(crawler)
            
            crawl_orchestrator = CrawlService(
                audit_service=audit_service,
                crawler_service=discovery_service,
                max_depth=max_depth,
                max_pages=max_pages,
                concurrency=concurrency,
                config=profile,
                checkpoint_callback=checkpoint_cb
            )
            
            # 4. Execution
            try:
                self.logger.info(f"--- [ STARTING DISTRIBUTED AUDIT: {url} ] ---")
                if domain:
                    domain.mark_crawling()
                    await target_repo.update_domain(domain)
                    await db_session.commit()
                
                await browser.start() # Optimize: Start once for site-wide crawl
                await crawl_orchestrator.run(url)
                
                # Fetch fresh domain instance for merge sanity
                domain_fresh = await target_repo.get_domain_by_url(url)
                if domain_fresh:
                    domain_fresh.mark_active()
                    if domain_fresh.scan_profile and "checkpoint" in domain_fresh.scan_profile:
                        domain_fresh.scan_profile.pop("checkpoint", None)
                    await target_repo.update_domain(domain_fresh)
                    await db_session.commit()
                self.logger.info(f"--- [ AUDIT COMPLETE: {url} ] ---")
            except Exception as e:
                domain_fresh = await target_repo.get_domain_by_url(url)
                if domain_fresh:
                    domain_fresh.mark_failed(str(e))
                    await target_repo.update_domain(domain_fresh)
                    await db_session.commit()
                self.logger.exception(f"Distributed Audit Failure [{url}]")
            finally:
                if browser:
                    await browser.teardown()
                if crawler:
                    try: await crawler.teardown()
                    except: pass

    async def _run_single_audit(self, url: str):
        """Executes a surgical audit for a single page with persistence isolation."""
        async with AsyncSession(self.engine) as db_session:
            # 1. Initialize Infrastructure Components
            repo = SqlAlchemyAuditRepository(db_session)
            browser = PlaywrightEngine(uuid4()) # Fresh engine session
            
            # 2. Assemble Service Layer
            audit_service = AuditService(browser, repo)
            
            # 3. Execution with Surgical Watchdog (10-minute mission limit)
            try:
                self.logger.info(f"--- [ STARTING SURGICAL AUDIT: {url} ] ---")
                await asyncio.wait_for(audit_service.execute_audit(url), timeout=600)
                self.logger.info(f"--- [ AUDIT COMPLETE: {url} ] ---")
            except asyncio.TimeoutError:
                self.logger.error(f"Surgical Watchdog Triggered: Audit for {url} exceeded 10-minute mission limit. Aborting.")
            except Exception as e:
                self.logger.exception(f"Surgical Audit Failure [{url}]")
            finally:
                # Cleanup browser cluster
                if browser:
                    await browser.teardown()

if __name__ == "__main__":
    worker = AuditWorker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        pass

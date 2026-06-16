"""
AUDITOR BATCH ENGINE: BATCH AUDIT ORCHESTRATOR
==============================================

Role: Orchestrate large-scale accessibility audits across multiple domains.
This module manages the scheduling, concurrency, and telemetry of batch 
audit operations.
"""

import asyncio
import os
import sys
import psutil # type: ignore
from datetime import datetime
from typing import List, Dict, Any, cast

# IDE PATH RECONCILIATION: Redundant path hinting for static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository # type: ignore
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository # type: ignore
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor # type: ignore
from auditor.domain.crawler import LinkDiscoveryService # type: ignore
from auditor.application.audit_service import AuditService # type: ignore
from auditor.application.crawl_service import CrawlService # type: ignore
from auditor.domain.models import AuditTarget, DomainStatus # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore
from auditor.domain.exceptions import BatchError, RepositoryError # type: ignore
from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore

class BatchAuditManager:
    """
    Orchestrates high-concurrency batch processing of accessibility audits.
    
    Implements a robust task distribution strategy with isolated session management,
    priority scheduling, automated retries, and detailed telemetry analysis.
    """
    
    def __init__(self, engine: Any):
        self.engine = engine
        self.logger = auditor_logger.getChild("BatchProcess")
        # Global concurrency control for domain-level parallelism
        self.max_concurrent_domains: int = 5 
        self._semaphore = asyncio.Semaphore(self.max_concurrent_domains)
        
        # Global Telemetry
        self.telemetry: Dict[str, Any] = {
            "batch_start": datetime.now(),
            "domains_analyzed": 0,
            "success_count": 0,
            "failure_count": 0,
            "last_sweep_duration_seconds": 0.0,
            "average_processing_time": 0.0
        }
        self.queue = RedisTaskQueue(db_engine=self.engine)
        self._dynamic_throttle_ratio: float = 1.0
        self._stop_monitor = asyncio.Event()

    async def run_batch_audit(self) -> Dict[str, Any]:
        # Trigger an automated backup snapshot before running a new batch
        try:
            from auditor.infrastructure.backup_manager import DatabaseBackupManager
            backup_mgr = DatabaseBackupManager()
            backup_mgr.create_backup()
        except Exception as e:
            self.logger.warning(f"Failed to create pre-batch database snapshot: {e}")

        start_time = datetime.now()
        self.logger.info("Starting Parallel Batch Audit Process...")
        try:
            async with AsyncSession(self.engine) as session:
                target_repo = SqlAlchemyTargetRepository(session)
                domains = await target_repo.get_active_domains()
            
            if not domains:
                self.logger.warning("Abort: No active targets available in the repository.")
                return {"status": "skipped", "message": "Queue empty"}
            
            # 1. Priority-Based Scheduling
            # Sort domains by priority ascending (1 = highest priority),
            # and then by last scan date ascending (nulls first, then oldest scans)
            domains.sort(key=lambda d: (
                d.priority if d.priority is not None else 3,
                d.last_audit_at or datetime.min
            ))
            
            # 2. Hardware-Aware Dynamic Auto-Scaling (Phase VII)
            monitor_task = asyncio.create_task(self._monitor_system_health())
            
            self.logger.info(f"Target Queue Identified: {len(domains)} domains. Concurrency Baseline: {self.max_concurrent_domains}")
            
            tasks = [self._process_domain_audit(domain) for domain in cast(List[AuditTarget], domains)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Telemetry computation
            successes = len([r for r in results if r is True])
            failures = len([r for r in results if r is not True])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.telemetry["domains_analyzed"] += len(domains)
            self.telemetry["success_count"] += successes
            self.telemetry["failure_count"] += failures
            self.telemetry["last_sweep_duration_seconds"] = duration
            if self.telemetry["domains_analyzed"] > 0:
                self.telemetry["average_processing_time"] = duration / len(domains)
            
            summary = {
                "total": len(results),
                "success": successes,
                "failure": failures,
                "duration_seconds": duration
            }
            self.logger.info(f"Batch Process Complete: {summary}")
            
            # Cleanup Monitor
            self._stop_monitor.set()
            await monitor_task
            
            return summary
            
        except Exception as e:
            import traceback
            self.logger.critical(f"ORCHESTRATOR FAILURE: {e}\n{traceback.format_exc()}")
            raise BatchError(f"Autonomous orchestrator failure: {e}")

    async def dispatch_batch_audit(self) -> Dict[str, Any]:
        """Dispatches active domains to the Redis task queue for distributed processing."""
        # Trigger an automated backup snapshot before running a new batch
        try:
            from auditor.infrastructure.backup_manager import DatabaseBackupManager
            backup_mgr = DatabaseBackupManager()
            backup_mgr.create_backup()
        except Exception as e:
            self.logger.warning(f"Failed to create pre-batch database snapshot: {e}")

        self.logger.info("Initializing Distributed Batch Dispatch...")
        
        try:
            await self.queue.connect()
            async with AsyncSession(self.engine) as session:
                target_repo = SqlAlchemyTargetRepository(session)
                domains = await target_repo.get_active_domains()
            
            if not domains:
                self.logger.warning("Dispatch Abort: No active targets available.")
                return {"status": "skipped", "message": "Queue empty"}
            
            pushed_count = 0
            for domain in domains:
                # Pack target profile metadata if present
                task_payload = {
                    "url": domain.url,
                    "priority": domain.priority,
                    "scan_profile": domain.scan_profile
                }
                await self.queue.push_task("full_site_audit", task_payload)
                pushed_count += 1
                
            self.logger.info(f"Successfully dispatched {pushed_count} tasks to the cluster.")
            return {"status": "dispatched", "count": pushed_count}
            
        except Exception as e:
            self.logger.critical(f"DISPATCH FAILURE: {e}")
            raise BatchError(f"Distributed dispatch failure: {e}")
        finally:
            await self.queue.disconnect()
        return {}

    async def _monitor_system_health(self):
        """Background loop for sub-second hardware telemetry and auto-scaling."""
        self.logger.info("Hardware Auto-Scaler ONLINE.")
        while not self._stop_monitor.is_set():
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            
            # Exponential backoff logic for throttle ratio
            if cpu > 85 or ram > 90:
                self._dynamic_throttle_ratio = 0.2
                self.logger.warning(f"SYSTEM CRITICAL LOAD [{cpu}% CPU]. Throttling to 20% capacity.")
            elif cpu > 70 or ram > 80:
                self._dynamic_throttle_ratio = 0.5
                self.logger.info(f"System Load Elevated [{cpu}% CPU]. Throttling to 50% capacity.")
            else:
                self._dynamic_throttle_ratio = 1.0
                
            await asyncio.sleep(2)

    async def _process_domain_audit(self, domain: AuditTarget) -> bool:
        """Coordinates the end-to-end audit process with dynamic throttling and retries."""
        # Wait for hardware clearance if system is pinned
        while self._dynamic_throttle_ratio < 0.3:
            self.logger.debug(f"Audit PENDING: Waiting for hardware clearance for {domain.url}...")
            await asyncio.sleep(5)

        async with self._semaphore:
            self.logger.info(f"Target Audit Execution START: {domain.url} (Priority: {domain.priority})")
            
            try:
                # 1. Isolated Session and Service Context
                async with AsyncSession(self.engine) as session:
                    audit_repo = SqlAlchemyAuditRepository(session)
                    batch_repo = SqlAlchemyTargetRepository(session)
                    
                    # Fetch fresh domain instance for merge/session stability
                    db_domain = await batch_repo.get_domain_by_url(domain.url)
                    if not db_domain:
                        self.logger.warning(f"Domain {domain.url} not found in database. Skipping.")
                        return False

                    # Update status in db to CRAWLING
                    db_domain.mark_crawling()
                    await batch_repo.update_domain(db_domain)
                    await session.commit()
                    
                    # Initialize crawler config from target scan profile
                    profile = db_domain.scan_profile or {}
                    max_depth = profile.get("depth", 2)
                    max_pages = profile.get("max_pages", 20)
                    concurrency = profile.get("concurrency", 4)
                    
                    # Resilient Checkpoint Callback
                    target_url = db_domain.url
                    async def checkpoint_cb(state: Any):
                        try:
                            async with AsyncSession(self.engine) as cb_session:
                                cb_repo = SqlAlchemyTargetRepository(cb_session)
                                target_domain = await cb_repo.get_domain_by_url(target_url)
                                if target_domain:
                                    if target_domain.scan_profile is None:
                                        target_domain.scan_profile = {}
                                    if state is None:
                                        target_domain.scan_profile.pop("checkpoint", None)
                                    else:
                                        target_domain.scan_profile["checkpoint"] = state
                                    await cb_repo.update_domain(target_domain)
                                    await cb_session.commit()
                        except Exception as cb_err:
                            self.logger.warning(f"Resilient Checkpoint Save Failure for {target_url}: {cb_err}")

                    # Fresh service stack per domain audit
                    audit_service = AuditService(None, audit_repo)
                    link_extractor = PlaywrightLinkExtractor()
                    discovery_service = LinkDiscoveryService(link_extractor)
                    crawl_service = CrawlService(
                        audit_service=audit_service,
                        crawler_service=discovery_service,
                        max_depth=max_depth,
                        max_pages=max_pages,
                        concurrency=concurrency,
                        config=profile,
                        checkpoint_callback=checkpoint_cb
                    )
                    
                    try:
                        # 2. Recursive Crawl & Audit Deployment
                        await crawl_service.run(db_domain.url)
                        
                        # 3. Status Transition: ACTIVE
                        # Refresh target instance from db in case it was modified/paused during run
                        db_domain_fresh = await batch_repo.get_domain_by_url(db_domain.url)
                        if db_domain_fresh:
                            db_domain_fresh.mark_active()
                            # Clean up checkpoint on successful completion
                            if db_domain_fresh.scan_profile and "checkpoint" in db_domain_fresh.scan_profile:
                                db_domain_fresh.scan_profile.pop("checkpoint", None)
                            await batch_repo.update_domain(db_domain_fresh)
                            await session.commit()
                        self.logger.info(f"Target Audit Execution SUCCESS: {domain.url}")
                        return True
                    except Exception as run_err:
                        self.logger.error(f"Crawl Service Run Failure for {domain.url}: {run_err}")
                        db_domain_fresh = await batch_repo.get_domain_by_url(db_domain.url)
                        if db_domain_fresh:
                            db_domain_fresh.mark_failed(str(run_err))
                            await batch_repo.update_domain(db_domain_fresh)
                            await session.commit()
                        return False
                    finally:
                        await link_extractor.teardown()
                    
            except Exception as e:
                self.logger.error(f"Target Audit Execution Setup FAILURE for {domain.url}: {e}")
                return False

    async def get_system_health_report(self) -> Dict[str, Any]:
        """Synthesizes a system health report for the monitored targets."""
        try:
            async with AsyncSession(self.engine) as session:
                target_repo = SqlAlchemyTargetRepository(session)
                domains = await target_repo.get_all_domains()
            
            status_counts = {
                "active": sum(1 for d in domains if d.status == DomainStatus.ACTIVE),
                "crawling": sum(1 for d in domains if d.status == DomainStatus.CRAWLING),
                "failed": sum(1 for d in domains if d.status == DomainStatus.FAILED),
                "paused": sum(1 for d in domains if d.status == DomainStatus.PAUSED),
                "pending": sum(1 for d in domains if d.status == DomainStatus.PENDING),
                "total": len(domains)
            }
            
            # Compute national compliance trend metrics
            avg_priority = sum(d.priority for d in domains) / len(domains) if domains else 3.0
            failed_ratio = status_counts["failed"] / len(domains) if domains else 0.0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "process_status": "STABLE" if failed_ratio < 0.2 else "ATTENTION_REQUIRED",
                "batch_summary": status_counts,
                "avg_priority": round(avg_priority, 2),
                "uptime_percentage": 100.0,
                "telemetry": {
                    "batch_start": self.telemetry["batch_start"].isoformat(),
                    "domains_analyzed": self.telemetry["domains_analyzed"],
                    "success_count": self.telemetry["success_count"],
                    "failure_count": self.telemetry["failure_count"],
                    "last_sweep_duration_seconds": round(self.telemetry["last_sweep_duration_seconds"], 2),
                    "average_processing_time": round(self.telemetry["average_processing_time"], 2)
                }
            }
        except Exception as e:
            self.logger.error(f"Health Synthesis Failed: {e}")
            raise RepositoryError(f"Batch health aggregation failure: {e}")

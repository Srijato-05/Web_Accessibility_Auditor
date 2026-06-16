import asyncio
import sys
import os

# IDE PATH RECONCILIATION: Redundant path hinting for static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine # type: ignore
from sqlmodel import SQLModel # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore

# Core Technical Imports
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository # type: ignore
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor # type: ignore
from auditor.domain.crawler import LinkDiscoveryService # type: ignore
from auditor.domain.models import AuditTarget # type: ignore
from auditor.application.batch_service import BatchAuditManager # type: ignore
from auditor.application.reporter import AuditReporter # type: ignore
from auditor.application.discovery_service import DiscoveryService # type: ignore
from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore
from auditor.application.tui_dashboard import AuditorDashboard # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def main():
    """Batch Audit Orchestrator CLI"""
    # Hardware/Database Engine Initialization
    engine = create_async_engine(DATABASE_URL, connect_args={"timeout": 30.0}, echo=False)
    
    # WAL journal mode optimization for SQLite high concurrency
    from sqlalchemy import event # type: ignore
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        finally:
            cursor.close()
    
    # Global Task Registry (Phase XIII)
    from auditor.infrastructure.task_model import task_metadata # type: ignore
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            await conn.run_sync(task_metadata.create_all)

        # Cleanup any orphaned crawling targets left in database from a previous run
        try:
            from auditor.presentation.api import cleanup_orphaned_targets
            await cleanup_orphaned_targets()
        except Exception:
            pass

        # 3. CLI Argument Handling
        if "--help" in sys.argv or "-h" in sys.argv:
            print("""
Accessibility Auditor Batch CLI [v0.1.0]
Usage: python batch_audit.py [options]

Options:
  --help, -h                  Show this help message
  --add-target [url]          Add a new target domain to the audit registry
  --priority [1-5]            Priority level (1=highest, 5=lowest; used with --add-target)
  --dispatch                  Dispatch all active targets to the audit queue (Redis/SQLite)
  --status                    Display a detailed network health and target registry ledger status
  --prune                     Remove all failed target records from the registry
  --discover [url]            Autonomously discover and seed audit targets from sitemaps/robots.txt
  --worker                    Start an autonomous worker node to process the audit queue
  --dashboard                 Launch the real-time TUI cluster monitor
  --run                       Trigger a parallel local batch run of all active targets
            """)
            return

        if "--status" in sys.argv:
            async with AsyncSession(engine) as db_session:
                batch_repo = SqlAlchemyTargetRepository(db_session)
                domains = await batch_repo.get_all_domains()
                print("\n" + "="*80)
                print(f"NETWORK SURVEILLANCE REGISTRY LEDGER ({len(domains)} hosts)")
                print("="*80)
                if not domains:
                    print("No targets registered. Add one with --add-target [url].")
                else:
                    print(f"{'DOMAIN URL':<40} | {'STATUS':<10} | {'PRIORITY':<8} | {'RETRIES':<7} | {'LAST AUDIT'}")
                    print("-"*80)
                    for d in domains:
                        last_scan = d.last_audit_at.isoformat() if d.last_audit_at else "Never"
                        status_str = d.status.value if hasattr(d.status, 'value') else str(d.status)
                        print(f"{d.url:<40} | {status_str:<10} | {d.priority:<8} | {d.retry_count:<7} | {last_scan}")
                        if d.last_error:
                            print(f"   ↳ Error: {d.last_error}")
                        if d.scan_profile and "checkpoint" in d.scan_profile:
                            cp = d.scan_profile["checkpoint"]
                            visited_count = len(cp.get("visited_urls", []))
                            pending_count = len(cp.get("pending_queue", []))
                            print(f"   ↳ Active Checkpoint: {visited_count} pages audited, {pending_count} pending.")
                print("="*80 + "\n")
            return

        if "--prune" in sys.argv:
            async with AsyncSession(engine) as db_session:
                from auditor.domain.models import DomainStatus
                batch_repo = SqlAlchemyTargetRepository(db_session)
                domains = await batch_repo.get_all_domains()
                pruned_count = 0
                for d in domains:
                    if d.status == DomainStatus.FAILED:
                        await batch_repo.delete_domain(d.url)
                        pruned_count += 1
                auditor_logger.info(f"Registry Pruned: Removed {pruned_count} failed target(s).")
            return

        if len(sys.argv) >= 3 and sys.argv[1] == "--add-target":
            priority = 3
            if "--priority" in sys.argv:
                try:
                    p_index = sys.argv.index("--priority") + 1
                    priority = int(sys.argv[p_index])
                except Exception:
                    pass
            async with AsyncSession(engine) as db_session:
                batch_repo = SqlAlchemyTargetRepository(db_session)
                target_url = sys.argv[2]
                new_domain = AuditTarget(url=target_url, priority=priority)
                await batch_repo.add_domain(new_domain)
                auditor_logger.info(f"Target Registered [Priority {priority}]: {target_url}")
                
                # Auto-dispatch if possible to make it user-friendly
                auditor_logger.info("Auto-Dispatching target to Autonomous Queue...")
                batch_orchestrator = BatchAuditManager(engine)
                await batch_orchestrator.dispatch_batch_audit()
            return

        if "--dispatch" in sys.argv:
            batch_orchestrator = BatchAuditManager(engine)
            await batch_orchestrator.dispatch_batch_audit()
            return

        if "--discover" in sys.argv:
            target_index = sys.argv.index("--discover") + 1
            if target_index < len(sys.argv):
                queue = RedisTaskQueue(db_engine=engine)
                link_extractor = PlaywrightLinkExtractor()
                crawler = LinkDiscoveryService(link_extractor)
                try:
                    async with AsyncSession(engine) as db_session:
                        repo = SqlAlchemyTargetRepository(db_session)
                        discovery = DiscoveryService(queue, crawler, repo)
                        await discovery.run_discovery_session(sys.argv[target_index])
                finally:
                    await link_extractor.teardown()
            return
        
        if "--worker" in sys.argv:
            from auditor.application.worker import AuditWorker # type: ignore
            worker = AuditWorker("CLI-WORKER", engine)
            await worker.start()
            return

        if "--report" in sys.argv:
            async with AsyncSession(engine) as report_session:
                reporter = AuditReporter(report_session)
                res = await reporter.generate_summary_report()
                if res.get("html"):
                    auditor_logger.info(f"Stakeholder Report Generated: {res['html']}")
                else:
                    auditor_logger.warning("No report generated (likely no data).")
            return

        if "--dashboard" in sys.argv:
            dash = AuditorDashboard()
            await dash.run()
            return

        if "--run" in sys.argv or len(sys.argv) == 1:
            # 4. Batch Execution
            batch_orchestrator = BatchAuditManager(engine)
            await batch_orchestrator.run_batch_audit()
            return

    except Exception as e:
        auditor_logger.critical(f"Critical System Failure: {e}")
    finally:
        # GUARANTEED ENGINE TEARDOWN
        await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")

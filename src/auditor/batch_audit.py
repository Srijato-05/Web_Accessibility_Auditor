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
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel # type: ignore
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository # type: ignore
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository # type: ignore
from auditor.infrastructure.playwright_engine import PlaywrightEngine # type: ignore
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor # type: ignore
from auditor.domain.crawler import LinkDiscoveryService # type: ignore
from auditor.domain.models import AuditTarget # type: ignore
from auditor.application.audit_service import AuditService # type: ignore
from auditor.application.crawl_service import CrawlService # type: ignore
from auditor.application.batch_service import BatchAuditManager # type: ignore
from auditor.application.reporter import AuditReporter # type: ignore
from auditor.application.discovery_service import DiscoveryService # type: ignore
from auditor.application.tui_dashboard import AuditorDashboard # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

async def main():
    auditor_logger.info("Accessibility Auditor Batch CLI [v0.1.0] Initialized.")

    # 1. Environment Setup
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 3. CLI Argument Handling
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Accessibility Auditor Batch CLI [v0.1.0]
Usage: python batch_audit.py [options]

Options:
  --help, -h    Show this help message
  --add [url]   Add a new target domain to the audit queue
  --dispatch    Dispatch all active domains to the distributed Redis cluster
  --report      Generate a stakeholder report (HTML/JSON) from the latest session
  --discover [url]  Autonomously discover and dispatch audit targets from sitemaps/robots.txt
  --dashboard   Launch the real-time TUI cluster monitor
        """)
        return

    if len(sys.argv) >= 3 and sys.argv[1] == "--add":
        async with AsyncSession(engine) as db_session:
            batch_repo = SqlAlchemyTargetRepository(db_session)
            target_url = sys.argv[2]
            new_domain = AuditTarget(url=target_url)
            await batch_repo.add_domain(new_domain)
            auditor_logger.info(f"Target Added: {target_url}")
            return

    if "--dispatch" in sys.argv:
        try:
            batch_orchestrator = BatchAuditManager(engine)
            await batch_orchestrator.dispatch_batch_audit()
        except Exception as e:
            auditor_logger.critical(f"Dispatch Failure: {e}")
        finally:
            await engine.dispose()
        return

    if "--report" in sys.argv:
        try:
            async with AsyncSession(engine) as session:
                reporter = AuditReporter(session)
                await reporter.generate_summary_report()
        except Exception as e:
            auditor_logger.critical(f"Reporting Failure: {e}")
        finally:
            await engine.dispose()
        return

    if "--discover" in sys.argv:
        try:
            target_index = sys.argv.index("--discover") + 1
            if target_index < len(sys.argv):
                from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore
                queue = RedisTaskQueue()
                discovery = DiscoveryService(queue)
                await discovery.run_discovery_session(sys.argv[target_index])
        except Exception as e:
            auditor_logger.critical(f"Discovery Failure: {e}")
        finally:
            await engine.dispose()
        return
    
    if "--local" in sys.argv:
        try:
            from auditor.application.worker import AuditWorker # type: ignore
            from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore
            queue = RedisTaskQueue()
            await queue.connect() # Will fallback to LOCAL automatically
            
            worker = AuditWorker("LOCAL-ORCHESTRATOR", engine, queue)
            auditor_logger.info("Initializing Local Autonomous Process...")
            
            # Start Worker Task
            worker_task = asyncio.create_task(worker.start())
            
            # Start Batch Logic in same loop
            batch_orchestrator = BatchAuditManager(engine)
            await batch_orchestrator.run_batch_audit()
            
            # Allow worker to finish
            await asyncio.sleep(5)
            worker_task.cancel()
            
            # GENERATE REPORTS (Phase IV Visibility)
            async with AsyncSession(engine) as report_session:
                reporter = AuditReporter(report_session)
                res = await reporter.generate_summary_report()
                if res.get("html"):
                    auditor_logger.info(f"Local Audit Report Live: {res['html']}")
                
        except Exception as e:
            auditor_logger.critical(f"Local Execution Failure: {e}")
        finally:
            await engine.dispose()
        return

    if "--report" in sys.argv:
        try:
            async with AsyncSession(engine) as report_session:
                reporter = AuditReporter(report_session)
                res = await reporter.generate_summary_report()
                if res.get("html"):
                    auditor_logger.info(f"Stakeholder Report Generated: {res['html']}")
                else:
                    auditor_logger.warning("No report generated (likely no data).")
        except Exception as e:
            auditor_logger.critical(f"Reporting Failure: {e}")
        finally:
            await engine.dispose()
        return

    if "--dashboard" in sys.argv:
        try:
            dash = AuditorDashboard()
            await dash.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            auditor_logger.critical(f"Dashboard Failure: {e}")
        finally:
            await engine.dispose()
        return

    # 4. Batch Execution
    try:
        batch_orchestrator = BatchAuditManager(engine)
        await batch_orchestrator.run_batch_audit()
    except Exception as e:
        auditor_logger.critical(f"Critical Batch Process Failure: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        auditor_logger.warning("Auditor Console TERMINATED by User.")
    except Exception as e:
        auditor_logger.critical(f"FATAL SYSTEM FAILURE: {e}")

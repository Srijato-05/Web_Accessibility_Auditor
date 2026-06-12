import os
import sys
import shutil
import asyncio
import warnings
import logging
import time

# ==========================================
# ENTERPRISE LOGGING INFRASTRUCTURE
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SystemPurgeUtility")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Resolve sys.path
root_path = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(root_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel, TargetModel
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.domain.models import AuditTarget

async def clear_and_init():
    logger.info("=========================================")
    logger.info("  ACCESSIBILITY AUDITOR SYSTEM UTILITY")
    logger.info("=========================================")

    # 1. Data Structure Clearing
    logger.info("[1/5] DATA LAYER SETUP & DIRECTORY PURGE")
    reports_dir = os.path.join(root_path, "reports")
    dirs_to_clear = [
        os.path.join(reports_dir, "data"),
        os.path.join(reports_dir, "exports"),
        os.path.join(reports_dir, "logs"),
        os.path.join(reports_dir, "forensics", "har")
    ]

    for path in dirs_to_clear:
        if os.path.exists(path):
            logger.info(f"Clearing directory: {os.path.relpath(path, root_path)}")
            # Robust Retry Logic for Windows File Locks
            for attempt in range(3):
                try:
                    shutil.rmtree(path)
                    break
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"Failed to clear {path} completely. Zombie process holding lock? Error: {e}")
                    else:
                        time.sleep(1)
        os.makedirs(path, exist_ok=True)
    logger.info("Directories successfully re-initialized.")

    # 2. Database Schema Creation
    logger.info("\n[2/5] DATABASE SCHEMA & TABLE INITIALIZATION")
    database_url = "sqlite+aiosqlite:///./reports/data/audit_results.db"
    
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            logger.info("Creating SQLModel tables in audit_results.db...")
            await conn.run_sync(SQLModel.metadata.create_all)
            # Ensure Redis task queue persistence table exists
            from auditor.infrastructure.task_model import task_metadata
            await conn.run_sync(task_metadata.create_all)
        logger.info("Database schema created/verified successfully.")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize SQLite database: {e}")
        sys.exit(1)

    # 3. Truncate Tables (Failsafe for active DBs)
    from sqlalchemy import text
    try:
        async with AsyncSession(engine) as db_session:
            logger.info("Truncating table records for absolute clean slate...")
            await db_session.execute(text("DELETE FROM violations"))
            await db_session.execute(text("DELETE FROM audit_sessions"))
            await db_session.execute(text("DELETE FROM targets"))
            await db_session.execute(text("DELETE FROM audit_task_queue"))
            await db_session.commit()
        logger.info("All table records successfully cleared.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to truncate SQLite tables (Possible Table Lock): {e}")

    # 4. Seeding targets
    logger.info("\n[3/5] SEED DATA REGISTRATION")
    try:
        from auditor.batch_seeding import DEFAULT_SECTOR_MATRIX
        async with AsyncSession(engine) as db_session:
            batch_repo = SqlAlchemyTargetRepository(db_session)
            added = 0
            for category, urls in DEFAULT_SECTOR_MATRIX.items():
                for url in urls:
                    new_target = AuditTarget(url=url)
                    await batch_repo.add_domain(new_target)
                    added += 1
            logger.info(f"Successfully seeded {added} default target hosts into ledger database.")
    except Exception as e:
        logger.error(f"Failed to seed default targets: {e}")

    # 5. External Graph & Cache Purge
    logger.info("\n[4/5] EXTERNAL GRAPH & CACHE PURGE")
    try:
        import redis
        # Add timeouts to prevent hanging if Redis is offline
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3, socket_connect_timeout=3)
        r.ping() # Validate connection explicitly
        r.flushall()
        logger.info("[REDIS] Successfully flushed all cache keys.")
    except ImportError:
        logger.warning("[REDIS] Redis client not installed. Skipping cache flush.")
    except redis.ConnectionError:
        logger.warning("[REDIS] Could not connect to Redis server (Offline). Skipping cache flush.")
    except Exception as e:
        logger.error(f"[REDIS] Unexpected error during cache flush: {e}")

    try:
        from auditor.infrastructure.neo4j_repository import Neo4jRepository
        graph = Neo4jRepository()
        if graph.driver:
            with graph.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            graph.close()
            logger.info("[NEO4J] Successfully wiped all nodes and edges from Graph Database.")
        else:
            logger.warning("[NEO4J] Skipped (Driver offline or missing credentials).")
    except Exception as e:
        logger.error(f"[NEO4J] Warning: Could not execute Cypher purge: {e}")

    # 6. System Structure Verification
    logger.info("\n[5/5] SYSTEM STRUCTURE VERIFICATION")
    frontend_dir = os.path.join(root_path, "frontend")
    backend_dir = os.path.join(root_path, "src", "auditor")
    
    if os.path.exists(frontend_dir):
        logger.info("[FRONTEND] Verified frontend/ directory exists.")
    else:
        logger.warning("[FRONTEND] WARNING: frontend/ directory not found.")
        
    if os.path.exists(backend_dir):
        logger.info("[BACKEND] Verified backend src/auditor/ directory exists.")
    else:
        logger.warning("[BACKEND] WARNING: backend src/auditor/ not found.")
        
    logger.info("\nSystem clean-up and structure initialization completed successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(clear_and_init())
    except KeyboardInterrupt:
        logger.warning("Purge interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Unhandled exception during system purge: {e}")
        sys.exit(1)

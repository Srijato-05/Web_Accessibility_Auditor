"""
TECHNICAL INFRASTRUCTURE: RESILIENT TASK QUEUE (RTQ-Z10)
=========================================================

Role: Domain-agnostic task queuing with autonomous infrastructure fallback.
Architecture: 
  - Primary: Redis Lists (FIFO).
  - Fallback: In-memory asyncio.Queue.
Serialization: JSON.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, Union
from auditor.shared.logging import auditor_logger # type: ignore

try:
    from redis.asyncio import Redis, from_url # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from sqlalchemy.ext.asyncio import create_async_engine # type: ignore
from sqlmodel import select, update, delete # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore
from auditor.infrastructure.task_model import TaskModel # type: ignore

class RedisTaskQueue:
    """
    Autonomous Task Queue with Persistent SQLite Fallback.
    
    Dynamically switches between Redis and SQLite-backed persistence modes.
    """
    
    def __init__(self, redis_urls: Union[str, list[str]] = "redis://localhost:6379", queue_name: str = "auditor_tasks", db_engine: Optional[Any] = None):
        self.redis_urls = [redis_urls] if isinstance(redis_urls, str) else redis_urls
        self.queue_name = queue_name
        self.redis: Optional[Any] = None
        self.engine = db_engine
        self.mode = "PENDING"
        self.logger = auditor_logger.getChild("TaskQueue")

    async def connect(self):
        """Attempts to establish Redis connectivity with multi-node failover."""
        if not REDIS_AVAILABLE:
            self.mode = "LOCAL"
            self.logger.warning("Redis library missing. Initializing PERSISTENT SQLITE MODE.")
            return

        for url in self.redis_urls:
            try:
                self.redis = from_url(url, decode_responses=True)
                await asyncio.wait_for(self.redis.ping(), timeout=1.0) # type: ignore
                self.mode = "REDIS"
                self.logger.info(f"Redis Persistence Established: {url}")
                return
            except (Exception, asyncio.TimeoutError):
                self.logger.warning(f"Node Failover: {url} unreachable. Trying next...")
        
        self.mode = "LOCAL"
        self.logger.error("ALL INFRASTRUCTURE NODES OFFLINE. Falling back to PERSISTENT SQLITE QUEUE.")

    async def disconnect(self):
        """Cleanup resources and release hardware handles."""
        if self.redis:
            await self.redis.close() # type: ignore
            self.redis = None
        self.logger.info("Infrastructure handles released.")

    async def push_task(self, task_type: str, data: Dict[str, Any]):
        """Dispatches a task to the active infrastructure layer."""
        if self.mode == "PENDING": await self.connect()
        
        payload = {
            "type": task_type,
            "data": data,
            "metadata": {"pushed_at": str(datetime.now().isoformat())}
        }
        
        if self.mode == "REDIS" and self.redis:
            await self.redis.lpush(self.queue_name, json.dumps(payload)) # type: ignore
        elif self.engine:
            async with AsyncSession(self.engine) as session:
                task_node = TaskModel(
                    type=task_type,
                    data=data,
                    metadata_json=payload["metadata"]
                )
                session.add(task_node)
                await session.commit()
            
        self.logger.debug(f"Task Dispatched [{self.mode}]: {task_type}")

    async def pop_task(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Extracts a task from the active infrastructure layer."""
        if self.mode == "PENDING": await self.connect()
        
        if self.mode == "REDIS" and self.redis:
            try:
                result = await self.redis.brpop(self.queue_name, timeout=timeout) # type: ignore
                if result:
                    _, payload_str = result
                    return json.loads(payload_str)
            except Exception as e:
                self.logger.error(f"Redis POP anomaly: {e}. Switching to LOCAL fallback.")
                self.mode = "LOCAL"
        
        # Persistent Local Queue Logic (SQLite)
        if self.engine:
            async with AsyncSession(self.engine) as session:
                # 1. Fetch only necessary columns to avoid lazy-load issues
                stmt = select(
                    TaskModel.id, 
                    TaskModel.type, 
                    TaskModel.data, 
                    TaskModel.metadata_json
                ).where(TaskModel.status == "PENDING").order_by(TaskModel.created_at.asc()).limit(1)
                
                res = await session.execute(stmt)
                row = res.first()
                
                if row:
                    task_id, task_type, task_data, task_meta = row
                    
                    # 2. Update status in a separate transactional block (or same session)
                    self.logger.info(f"Task Dequeued from Ledger: [{task_type}] {task_id}")
                    update_stmt = update(TaskModel).where(TaskModel.id == task_id).values(status="PROCESSING")
                    await session.execute(update_stmt)
                    await session.commit()
                    
                    return {
                        "id": task_id,
                        "type": task_type,
                        "data": task_data,
                        "metadata": task_meta
                    }
                else:
                    self.logger.debug("No pending tasks found in persistent ledger.")
        
        await asyncio.sleep(min(timeout, 2))
        return None

    async def reset_abandoned_tasks(self):
        """Resets all 'PROCESSING' or 'FAILED' tasks back to 'PENDING'."""
        if self.mode == "REDIS":
            pass 
        elif self.engine:
            from sqlalchemy import or_ # type: ignore
            async with AsyncSession(self.engine) as session:
                # Reset processing AND failed ones from the previous NameError crash
                stmt = update(TaskModel).where(or_(TaskModel.status == "PROCESSING", TaskModel.status == "FAILED")).values(status="PENDING")
                await session.execute(stmt)
                await session.commit()
            self.logger.info("Self-Healing: Autonomous Ledger Reset to PENDING.")

    async def get_queue_size(self) -> Union[int, str]:
        """Provides real-time queue depth telemetry."""
        if self.mode == "REDIS" and self.redis:
            return await self.redis.llen(self.queue_name) # type: ignore
        if self.engine:
            from sqlmodel import func # type: ignore
            async with AsyncSession(self.engine) as session:
                res = await session.execute(select(func.count()).select_from(TaskModel).where(TaskModel.status == "PENDING"))
                return res.scalar() or 0
        return 0

    async def complete_task(self, task_id: Any):
        """Marks a task as successfully resolved in the persistent ledger."""
        if self.mode == "REDIS":
            pass # Redis tasks are consumed on POP
        elif self.engine and task_id:
            async with AsyncSession(self.engine) as session:
                stmt = update(TaskModel).where(TaskModel.id == task_id).values(status="COMPLETED")
                await session.execute(stmt)
                await session.commit()

    async def fail_task(self, task_id: Any, error: str):
        """Marks a task as failed and attaches forensic error details."""
        if self.mode == "REDIS":
            pass
        elif self.engine and task_id:
            async with AsyncSession(self.engine) as session:
                # 1. Fetch current metadata first (atomic rename/merge is tricky in SQLite JSON)
                stmt = select(TaskModel.metadata_json).where(TaskModel.id == task_id)
                res = await session.execute(stmt)
                meta = res.scalar() or {}
                
                # 2. Update with error detail
                new_meta = dict(meta)
                new_meta["last_error"] = error
                
                update_stmt = update(TaskModel).where(TaskModel.id == task_id).values(
                    status="FAILED",
                    metadata_json=new_meta
                )
                await session.execute(update_stmt)
                await session.commit()

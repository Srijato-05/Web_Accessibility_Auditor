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
from typing import Any, Dict, Optional, Union
from auditor.shared.logging import auditor_logger # type: ignore

try:
    from redis.asyncio import Redis, from_url # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class RedisTaskQueue:
    """
    Autonomous Task Queue with Local Fallback.
    
    Dynamically switches between Redis and In-Memory modes based on connectivity.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", queue_name: str = "auditor_tasks"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.redis: Optional[Any] = None
        self.local_queue: asyncio.Queue = asyncio.Queue()
        self.mode = "PENDING"
        self.logger = auditor_logger.getChild("TaskQueue")

    async def connect(self):
        """Attempts to establish Redis connectivity with local fallback."""
        if not REDIS_AVAILABLE:
            self.mode = "LOCAL"
            self.logger.warning("Redis library missing. Initializing LOCAL PERSISTENCE MODE.")
            return

        try:
            self.redis = from_url(self.redis_url, decode_responses=True)
            await asyncio.wait_for(self.redis.ping(), timeout=2.0) # type: ignore
            self.mode = "REDIS"
            self.logger.info(f"Redis Cluster Connected: {self.redis_url}")
        except (Exception, asyncio.TimeoutError) as e:
            self.mode = "LOCAL"
            self.logger.warning(f"Redis Unreachable: {e}. Falling back to AUTONOMOUS LOCAL QUEUE.")

    async def disconnect(self):
        """Cleanup resources."""
        if self.redis:
            await self.redis.close() # type: ignore
            self.logger.info("Infrastructure handles released.")

    async def push_task(self, task_type: str, data: Dict[str, Any]):
        """Dispatches a task to the active infrastructure layer."""
        if self.mode == "PENDING": await self.connect()
        
        payload = {
            "type": task_type,
            "data": data,
            "metadata": {"pushed_at": str(asyncio.get_event_loop().time())}
        }
        
        if self.mode == "REDIS" and self.redis:
            await self.redis.lpush(self.queue_name, json.dumps(payload)) # type: ignore
        else:
            await self.local_queue.put(payload)
            
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
        
        # Local Queue Logic
        try:
            return await asyncio.wait_for(self.local_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    async def get_queue_size(self) -> Union[int, str]:
        """Provides real-time queue depth telemetry."""
        if self.mode == "REDIS" and self.redis:
            return await self.redis.llen(self.queue_name) # type: ignore
        return self.local_queue.qsize()

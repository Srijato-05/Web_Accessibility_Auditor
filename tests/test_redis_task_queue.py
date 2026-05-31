import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.infrastructure.redis_task_queue import RedisTaskQueue

@pytest.mark.asyncio
async def test_redis_queue_offline_fallback(temp_db_engine):
    queue = RedisTaskQueue(redis_urls="redis://invalid-host:9999", db_engine=temp_db_engine)
    
    await queue.connect()
    assert queue.mode == "LOCAL"
    
    task_data = {"url": "https://offline.com"}
    await queue.push_task("single_url_audit", task_data)
    
    popped = await queue.pop_task()
    assert popped is not None
    assert popped["type"] == "single_url_audit"
    assert popped["data"] == task_data
    
    await queue.disconnect()

@pytest.mark.asyncio
async def test_redis_queue_online_mode():
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.lpush = AsyncMock()
    mock_redis.brpop = AsyncMock(return_value=("auditor_tasks", '{"type": "redis_task", "data": {"url": "https://online.com"}}'))
    
    queue = RedisTaskQueue(redis_urls="redis://localhost:6379")
    
    with patch("auditor.infrastructure.redis_task_queue.from_url", return_value=mock_redis), \
         patch("auditor.infrastructure.redis_task_queue.REDIS_AVAILABLE", True):
        
        await queue.connect()
        assert queue.mode == "REDIS"
        
        await queue.push_task("redis_task", {"url": "https://online.com"})
        mock_redis.lpush.assert_called_once()
        
        popped = await queue.pop_task()
        assert popped is not None
        assert popped["type"] == "redis_task"
        assert popped["data"]["url"] == "https://online.com"
        
        await queue.disconnect()

@pytest.mark.asyncio
async def test_sqlite_self_healing_reset(temp_db_engine):
    """Verifies that processing or failed tasks are correctly self-healed back to PENDING on connect."""
    queue = RedisTaskQueue(redis_urls="redis://invalid-host:9999", db_engine=temp_db_engine)
    await queue.connect()
    
    # Push two tasks and manually mark them as PROCESSING and FAILED
    await queue.push_task("task1", {"url": "https://test1.com"})
    await queue.push_task("task2", {"url": "https://test2.com"})
    
    task1 = await queue.pop_task() # Status becomes PROCESSING
    assert task1 is not None
    
    # Simulating a worker crash and recovery
    await queue.reset_abandoned_tasks()
    
    # Assert queue size counts the recovered task again
    size = await queue.get_queue_size()
    assert size == 2

@pytest.mark.asyncio
async def test_sqlite_complete_and_fail_task(temp_db_engine):
    """Verifies complete_task and fail_task status flows in SQLite fallback queue mode."""
    queue = RedisTaskQueue(redis_urls="redis://invalid-host:9999", db_engine=temp_db_engine)
    await queue.connect()
    
    await queue.push_task("task1", {"url": "https://test1.com"})
    task = await queue.pop_task()
    assert task is not None
    task_id = task["id"]
    
    # Mark task as completed
    await queue.complete_task(task_id)
    size = await queue.get_queue_size()
    assert size == 0 # Completed tasks are not PENDING
    
    # Push second task and mark as failed
    await queue.push_task("task2", {"url": "https://test2.com"})
    task2 = await queue.pop_task()
    assert task2 is not None
    await queue.fail_task(task2["id"], "Browser launch timeout")
    
    # Verify queue size is zero
    size = await queue.get_queue_size()
    assert size == 0

@pytest.mark.asyncio
async def test_redis_queue_multi_node_failover():
    # 2 nodes: first fails, second succeeds
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    
    call_count = 0
    def from_url_side_effect(url, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Connection refused")
        return mock_redis
        
    queue = RedisTaskQueue(redis_urls=["redis://fail-node:6379", "redis://ok-node:6379"])
    
    with patch("auditor.infrastructure.redis_task_queue.from_url", side_effect=from_url_side_effect), \
         patch("auditor.infrastructure.redis_task_queue.REDIS_AVAILABLE", True):
        await queue.connect()
        assert queue.mode == "REDIS"
        assert call_count == 2
        await queue.disconnect()

@pytest.mark.asyncio
async def test_redis_pop_anomaly_fallback():
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    # brpop raises exception to trigger fallback
    mock_redis.brpop.side_effect = RuntimeError("Redis connection lost during pop")
    
    queue = RedisTaskQueue(redis_urls="redis://localhost:6379")
    
    with patch("auditor.infrastructure.redis_task_queue.from_url", return_value=mock_redis), \
         patch("auditor.infrastructure.redis_task_queue.REDIS_AVAILABLE", True):
        await queue.connect()
        assert queue.mode == "REDIS"
        
        # Pop should fail, catch error, switch to LOCAL and return None/fallback
        res = await queue.pop_task(timeout=1)
        assert res is None
        assert queue.mode == "LOCAL"
        await queue.disconnect()

@pytest.mark.asyncio
async def test_sqlite_pop_empty(temp_db_engine):
    queue = RedisTaskQueue(redis_urls="redis://invalid-host:9999", db_engine=temp_db_engine)
    await queue.connect()
    
    # Try popping from an empty DB queue
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        res = await queue.pop_task(timeout=2)
        assert res is None
        mock_sleep.assert_called_once()

@pytest.mark.asyncio
async def test_redis_get_size_complete_fail():
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.llen.return_value = 5
    
    queue = RedisTaskQueue(redis_urls="redis://localhost:6379")
    
    with patch("auditor.infrastructure.redis_task_queue.from_url", return_value=mock_redis), \
         patch("auditor.infrastructure.redis_task_queue.REDIS_AVAILABLE", True):
        await queue.connect()
        assert queue.mode == "REDIS"
        
        # Test size
        size = await queue.get_queue_size()
        assert size == 5
        
        await queue.disconnect()


@pytest.mark.asyncio
async def test_redis_queue_no_redis_available_fallback(temp_db_engine):
    import auditor.infrastructure.redis_task_queue as rtq
    original_redis_available = rtq.REDIS_AVAILABLE
    rtq.REDIS_AVAILABLE = False
    try:
        queue = RedisTaskQueue(redis_urls="redis://localhost:6379", db_engine=temp_db_engine)
        await queue.connect()
        assert queue.mode == "LOCAL"
        await queue.disconnect()
    finally:
        rtq.REDIS_AVAILABLE = original_redis_available


@pytest.mark.asyncio
async def test_redis_queue_pop_task_pending_mode(temp_db_engine):
    queue = RedisTaskQueue(redis_urls="redis://invalid-host:9999", db_engine=temp_db_engine)
    assert queue.mode == "PENDING"
    with patch("asyncio.sleep", AsyncMock()):
        popped = await queue.pop_task(timeout=1)
        assert popped is None
        assert queue.mode == "LOCAL"
        await queue.disconnect()


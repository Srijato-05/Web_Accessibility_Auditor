import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.application.batch_service import BatchAuditManager
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.domain.models import AuditTarget, DomainStatus

@pytest.mark.asyncio
async def test_run_batch_audit_no_domains(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    res = await manager.run_batch_audit()
    assert res == {"status": "skipped", "message": "Queue empty"}

@pytest.mark.asyncio
async def test_run_batch_audit_success(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    
    # Register 2 active targets in DB
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        await repo.add_domain(AuditTarget(url="https://site1.com"))
        await repo.add_domain(AuditTarget(url="https://site2.com"))
        await session.commit()
    
    # Mock CPU percent to keep loop healthy
    # Mock CrawlService run method to return successfully immediately
    with patch("psutil.cpu_percent", return_value=15.0), \
         patch("psutil.virtual_memory") as mock_ram, \
         patch("auditor.application.batch_service.CrawlService.run", AsyncMock()) as mock_crawl_run:
        
        mock_ram.return_value.percent = 30.0
        
        res = await manager.run_batch_audit()
        assert res["total"] == 2
        assert res["success"] == 2
        assert res["failure"] == 0
        assert mock_crawl_run.call_count == 2

@pytest.mark.asyncio
async def test_dispatch_batch_audit(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    
    # Register targets
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        await repo.add_domain(AuditTarget(url="https://site1.com"))
        await repo.add_domain(AuditTarget(url="https://site2.com"))
        await session.commit()
        
    # Mock queue functions
    mock_connect = AsyncMock()
    mock_push = AsyncMock()
    mock_disconnect = AsyncMock()
    
    manager.queue.connect = mock_connect
    manager.queue.push_task = mock_push
    manager.queue.disconnect = mock_disconnect
    
    res = await manager.dispatch_batch_audit()
    assert res["status"] == "dispatched"
    assert res["count"] == 2
    
    mock_connect.assert_called_once()
    assert mock_push.call_count == 2
    mock_push.assert_any_call("full_site_audit", {"url": "https://site1.com"})
    mock_push.assert_any_call("full_site_audit", {"url": "https://site2.com"})
    mock_disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_system_health_auto_scaler_throttling(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    assert manager._dynamic_throttle_ratio == 1.0
    
    # Monitor health with high CPU load mock
    with patch("psutil.cpu_percent", return_value=90.0), \
         patch("psutil.virtual_memory") as mock_ram:
        mock_ram.return_value.percent = 20.0
        
        # Start scaler background task, run loop once and cancel
        monitor_task = asyncio.create_task(manager._monitor_system_health())
        await asyncio.sleep(1.2) # Let loop run once (interval=1)
        
        manager._stop_monitor.set()
        await monitor_task
        
        # Verify it throttled to 20% capacity
        assert manager._dynamic_throttle_ratio == 0.2

@pytest.mark.asyncio
async def test_get_system_health_report(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    
    # Setup targets
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        await repo.add_domain(AuditTarget(url="https://active.com", status=DomainStatus.ACTIVE))
        await repo.add_domain(AuditTarget(url="https://crawl.com", status=DomainStatus.CRAWLING))
        await session.commit()
        
    report = await manager.get_system_health_report()
    assert report["process_status"] == "STABLE"
    assert report["batch_summary"]["active"] == 1
    assert report["batch_summary"]["crawling"] == 1
    assert report["batch_summary"]["total"] == 2

from auditor.domain.exceptions import BatchError, RepositoryError

@pytest.mark.asyncio
async def test_system_health_medium_cpu_load(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    with patch("psutil.cpu_percent", return_value=75.0), \
         patch("psutil.virtual_memory") as mock_ram:
        mock_ram.return_value.percent = 20.0
        monitor_task = asyncio.create_task(manager._monitor_system_health())
        await asyncio.sleep(1.2)
        manager._stop_monitor.set()
        await monitor_task
        assert manager._dynamic_throttle_ratio == 0.5

@pytest.mark.asyncio
async def test_run_batch_orchestrator_failure(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    with patch("auditor.application.batch_service.SqlAlchemyTargetRepository.get_active_domains", side_effect=Exception("DB Down")):
        with pytest.raises(BatchError):
            await manager.run_batch_audit()

@pytest.mark.asyncio
async def test_dispatch_batch_failure(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    manager.queue.connect = AsyncMock()
    manager.queue.disconnect = AsyncMock()
    manager.queue.push_task = AsyncMock(side_effect=Exception("Redis down"))
    
    # Setup domains
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        await repo.add_domain(AuditTarget(url="https://site1.com"))
        await session.commit()
        
    with pytest.raises(BatchError):
        await manager.dispatch_batch_audit()

@pytest.mark.asyncio
async def test_process_domain_throttle_wait_and_failure(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    manager._dynamic_throttle_ratio = 0.2 # Below 0.3 throttle threshold
    
    domain = AuditTarget(url="https://site1.com")
    
    # We will trigger the wait, mock sleep to set the ratio back to 1.0 to let it progress,
    # and mock PlaywrightLinkExtractor to throw to verify exception/failure paths.
    async def mock_sleep_impl(sec):
        manager._dynamic_throttle_ratio = 1.0
        
    with patch("asyncio.sleep", side_effect=mock_sleep_impl) as mock_sleep, \
         patch("auditor.application.batch_service.PlaywrightLinkExtractor", side_effect=RuntimeError("Extractor Failure")):
        res = await manager._process_domain_audit(domain)
        assert res is False
        mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_health_synthesis_failure(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    with patch("auditor.application.batch_service.SqlAlchemyTargetRepository.get_active_domains", side_effect=Exception("DB failure")):
        with pytest.raises(RepositoryError):
            await manager.get_system_health_report()


@pytest.mark.asyncio
async def test_dispatch_batch_audit_no_domains(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    manager.queue.connect = AsyncMock()
    manager.queue.disconnect = AsyncMock()
    res = await manager.dispatch_batch_audit()
    assert res == {"status": "skipped", "message": "Queue empty"}


@pytest.mark.asyncio
async def test_process_domain_audit_success_and_fallback(temp_db_engine):
    manager = BatchAuditManager(temp_db_engine)
    domain = AuditTarget(url="https://site1.com")
    
    with patch("auditor.application.batch_service.PlaywrightLinkExtractor"), \
         patch("auditor.application.batch_service.CrawlService.run", AsyncMock()) as mock_crawl_run:
        res = await manager._process_domain_audit(domain)
        assert res is True
        mock_crawl_run.assert_called_once_with("https://site1.com")
        
    with patch("auditor.application.batch_service.AsyncSession", return_value=MagicMock(__aenter__=AsyncMock(return_value=None))):
        res = await manager._process_domain_audit(domain)
        assert res is False



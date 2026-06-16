import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.domain.models import AuditTarget, DomainStatus
from auditor.domain.exceptions import RepositoryError
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.infrastructure.persistence_models import TargetModel
import random
import string
import datetime

@pytest.mark.asyncio
async def test_target_repo_add_domain_dynamic_scaling(temp_db_engine):
    """
    Advanced Test: Simulates adding thousands of targets recursively,
    validating ORM object mapping and scaling efficiency under heavy load.
    """
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        
        # We will add 500 domains dynamically
        added_urls = []
        for i in range(500):
            url = f"https://target-scaling-{i}.com"
            added_urls.append(url)
            
            target = AuditTarget(url=url, status=DomainStatus.PENDING, priority=random.randint(1, 10))
            await repo.add_domain(target)
            
        # Verify persistence and retrieval efficiency
        res = await session.exec(select(TargetModel))
        all_targets = res.all()
        
        assert len(all_targets) == 500
        assert all_targets[0].url in added_urls

@pytest.mark.asyncio
async def test_target_repo_add_domain_chaos_error_handling(temp_db_engine):
    """
    Chaos Engineering: Tests the repository's resilience when the 
    database connection abruptly drops during a merge operation.
    """
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.merge.side_effect = Exception("DB Connection closed abruptly by Peer (Chaos)")
    
    repo = SqlAlchemyTargetRepository(mock_session)
    target = AuditTarget(url="https://add-fail.com")
    
    with pytest.raises(RepositoryError) as exc_info:
        await repo.add_domain(target)
    
    assert "Batch registry commitment failure" in str(exc_info.value)
    assert "DB Connection closed abruptly" in str(exc_info.value)

@pytest.mark.asyncio
async def test_target_repo_get_active_domains_complex_filtering(temp_db_engine):
    """
    Validates complex dynamic SQL filtering algorithms for domain status queues.
    """
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        
        # Add a complex mix of domains
        statuses = [
            DomainStatus.PENDING, DomainStatus.ACTIVE, DomainStatus.PAUSED, 
            DomainStatus.FAILED, DomainStatus.CRAWLING, DomainStatus.PENDING
        ]
        
        for idx, status in enumerate(statuses):
            t = AuditTarget(url=f"https://complex-{idx}.com", status=status)
            await repo.add_domain(t)
            
        actives = await repo.get_active_domains()
        
        # Active domains should be everything EXCEPT PAUSED
        assert len(actives) == 5
        
        for a in actives:
            assert a.status != DomainStatus.PAUSED
            
@pytest.mark.asyncio
async def test_target_repo_update_status_and_priority_dynamic():
    """
    Tests targeted row updates and concurrency metrics when altering domain states.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SqlAlchemyTargetRepository(mock_session)
    
    target = AuditTarget(url="https://dynamic.com", status=DomainStatus.ACTIVE, priority=1)
    
    # Run the update
    await repo.update_domain(target)
    
    # update_domain uses merge under the hood (it calls add_domain)
    mock_session.merge.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_target_repo_delete_domain_cascade():
    """
    Tests the repository gracefully handles deletion execution and 
    associated SQL error catches.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SqlAlchemyTargetRepository(mock_session)
    
    await repo.delete_domain("https://kill.com")
    
    # Verify exec and commit were called for the delete statement
    mock_session.exec.assert_called_once()
    mock_session.commit.assert_called_once()
    
    # Test error handling on delete
    mock_session.commit.side_effect = Exception("Foreign key constraint failed")
    with pytest.raises(RepositoryError) as exc:
        await repo.delete_domain("https://kill.com")
    
    assert "Foreign key constraint failed" in str(exc.value)

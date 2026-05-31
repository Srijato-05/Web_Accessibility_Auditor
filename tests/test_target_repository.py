import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.domain.models import AuditTarget, DomainStatus
from auditor.domain.exceptions import RepositoryError
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.infrastructure.persistence_models import TargetModel

@pytest.mark.asyncio
async def test_add_domain_success(temp_db_engine):
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        target = AuditTarget(url="https://add-test.com")
        
        await repo.add_domain(target)
        
        # Verify persistence
        res = await session.exec(select(TargetModel).where(TargetModel.url == "https://add-test.com"))
        persisted = res.first()
        assert persisted is not None
        assert persisted.status == DomainStatus.PENDING.value

@pytest.mark.asyncio
async def test_add_domain_error_raises_repository_error(temp_db_engine):
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.merge.side_effect = Exception("DB Connection closed")
    
    repo = SqlAlchemyTargetRepository(mock_session)
    target = AuditTarget(url="https://add-fail.com")
    
    with pytest.raises(RepositoryError) as exc_info:
        await repo.add_domain(target)
    assert "Batch registry commitment failure" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_active_domains(temp_db_engine):
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        
        # Add 3 domains: 2 active, 1 paused
        t1 = AuditTarget(url="https://active1.com", status=DomainStatus.PENDING)
        t2 = AuditTarget(url="https://active2.com", status=DomainStatus.ACTIVE)
        t3 = AuditTarget(url="https://paused.com", status=DomainStatus.PAUSED)
        
        await repo.add_domain(t1)
        await repo.add_domain(t2)
        await repo.add_domain(t3)
        
        actives = await repo.get_active_domains()
        assert len(actives) == 2
        urls = [a.url for a in actives]
        assert "https://active1.com" in urls
        assert "https://active2.com" in urls
        assert "https://paused.com" not in urls

@pytest.mark.asyncio
async def test_get_domain_by_url(temp_db_engine):
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        
        target = AuditTarget(url="https://search.com")
        await repo.add_domain(target)
        
        found = await repo.get_domain_by_url("https://search.com")
        assert found is not None
        assert found.url == "https://search.com"
        
        missing = await repo.get_domain_by_url("https://missing.com")
        assert missing is None

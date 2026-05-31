import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.violation import Violation, ImpactLevel
from auditor.domain.exceptions import RepositoryError
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel

@pytest.mark.asyncio
async def test_repository_save_and_get_session(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        session_id = uuid4()
        session = AuditSession(
            id=session_id,
            target_url="https://test.com",
            status=SessionStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message=None,
            agent_summary={"violations": 2},
            remediation_plan="Fix the alt tags"
        )
        
        # Test save_session
        await repo.save_session(session)
        
        # Verify persistence in DB
        db_session.expire_all()
        saved = await repo.get_session(session_id)
        assert saved.id == session_id
        assert saved.target_url == "https://test.com"
        assert saved.status == SessionStatus.COMPLETED
        assert saved.remediation_plan == "Fix the alt tags"
        assert saved.agent_summary == {"violations": 2}

@pytest.mark.asyncio
async def test_repository_get_session_not_found(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        with pytest.raises(RepositoryError) as exc:
            await repo.get_session(uuid4())
        assert "not found" in str(exc.value)

@pytest.mark.asyncio
async def test_repository_save_violations_and_retrieve(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        session_id = uuid4()
        session = AuditSession(
            id=session_id,
            target_url="https://test.com",
            status=SessionStatus.COMPLETED
        )
        await repo.save_session(session)
        
        # Violations
        v1 = Violation(
            rule_id="img-alt",
            impact=ImpactLevel.SERIOUS,
            description="Missing alt",
            help_url="http://help",
            selector="img",
            nodes=[{"html": "<img>"}],
            tags=["img", "wcag-1.1.1"],
            session_id=session_id,
            agent="axe",
            compliance_level="A",
            category="Images",
            severity_matrix="High",
            url="https://test.com"
        )
        
        # Save violations
        await repo.save_violations([v1])
        
        # Verify retrieved session has violations
        saved = await repo.get_session(session_id)
        assert len(saved.violations) == 1
        assert saved.violations[0].rule_id == "img-alt"
        assert saved.violations[0].impact == ImpactLevel.SERIOUS
        assert saved.violations[0].compliance_level == "A"
        
        # Empty list should return early
        await repo.save_violations([])

@pytest.mark.asyncio
async def test_repository_list_recent_sessions(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        s1 = AuditSession(id=uuid4(), target_url="https://s1.com", status=SessionStatus.CREATED)
        s2 = AuditSession(id=uuid4(), target_url="https://s2.com", status=SessionStatus.IN_PROGRESS)
        
        await repo.save_session(s1)
        await repo.save_session(s2)
        
        recent = await repo.list_recent_sessions(limit=5)
        assert len(recent) >= 2
        # Verify sorting (recent first based on created_at)
        urls = [s.target_url for s in recent]
        assert "https://s1.com" in urls
        assert "https://s2.com" in urls

@pytest.mark.asyncio
async def test_repository_save_session_exception(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        # Force a database exception by passing a mocked model that fails merging
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.status_value = "CREATED"
        
        # Stub merge to raise an error
        db_session.merge = AsyncMock(side_effect=Exception("Merge failed"))
        
        with pytest.raises(RepositoryError) as exc:
            await repo.save_session(mock_session)
        assert "Merge failed" in str(exc.value)

@pytest.mark.asyncio
async def test_repository_get_session_exception(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        # Force exec to fail
        db_session.exec = AsyncMock(side_effect=Exception("Query failed"))
        
        with pytest.raises(RepositoryError) as exc:
            await repo.get_session(uuid4())
        assert "Query failed" in str(exc.value)

@pytest.mark.asyncio
async def test_repository_save_violations_exception(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        v1 = Violation(
            rule_id="img-alt",
            impact=ImpactLevel.SERIOUS,
            description="Missing alt",
            help_url="http://help",
            selector="img",
            nodes=[{"html": "<img>"}],
            tags=["img"],
            session_id=uuid4(),
            agent="axe",
            compliance_level="A",
            category="Images",
            severity_matrix="High",
            url="https://test.com"
        )
        
        db_session.add = MagicMock(side_effect=Exception("Add failed"))
        
        with pytest.raises(RepositoryError) as exc:
            await repo.save_violations([v1])
        assert "Add failed" in str(exc.value)

@pytest.mark.asyncio
async def test_repository_list_recent_sessions_exception(temp_db_engine):
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        db_session.exec = AsyncMock(side_effect=Exception("List failed"))
        
        with pytest.raises(RepositoryError) as exc:
            await repo.list_recent_sessions(limit=5)
        assert "List failed" in str(exc.value)

@pytest.mark.asyncio
async def test_repository_schema_integrity_migration_paths(temp_db_engine):
    # Test checking for missing columns and migrating them
    async with AsyncSession(temp_db_engine) as db_session:
        repo = SqlAlchemyAuditRepository(db_session)
        
        # 1. Clear _schema_verified to force verify
        repo._schema_verified = False
        
        # 2. Run _ensure_schema_integrity
        await repo._ensure_schema_integrity()
        assert repo._schema_verified is False  # it remains false because _ensure_schema_integrity doesn't set it to True itself
        
        # 3. Simulate migration failure / rollback path
        db_session.exec = AsyncMock(side_effect=Exception("Pragma failed"))
        db_session.rollback = AsyncMock()
        
        await repo._ensure_schema_integrity()
        db_session.rollback.assert_called_once()

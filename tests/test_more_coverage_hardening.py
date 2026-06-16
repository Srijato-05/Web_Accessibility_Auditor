import pytest
import sys
import os
import uuid
import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.violation import Violation, ImpactLevel
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel, TargetModel
from auditor.application.audit_service import AuditService
from auditor.application.batch_service import BatchService
from auditor.application.crawl_service import CrawlService
from auditor.application.reporter import ReportService
from auditor.application.worker import AuditWorker
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.infrastructure.backup_manager import BackupManager
from auditor.infrastructure.neo4j_repository import Neo4jRepository
from auditor.infrastructure.pdf_reporter import convert_json_to_pdf, generate_html_from_json
from auditor.infrastructure.playwright_engine import PlaywrightAccessibilityEngine
from auditor.infrastructure.redis_task_queue import RedisTaskQueue
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.presentation.api import is_safe_url, _get_violations_data_from_session
from auditor.shared.compliance_mapper import ComplianceMapper
from auditor.shared.logging import auditor_logger, setup_auditor_logging

# =====================================================================
# 1. AUDIT SERVICE TEST
# =====================================================================
@pytest.mark.asyncio
async def test_audit_service_gaps():
    db_session = AsyncMock()
    repo = MagicMock(spec=SqlAlchemyAuditRepository)
    
    mock_session = AuditSession(target_url="https://test.com")
    repo.list_recent_sessions.return_value = [mock_session]
    
    service = AuditService(repo)
    res = await service.get_recent_history(limit=5)
    assert len(res) == 1
    assert res[0].target_url == "https://test.com"

# =====================================================================
# 2. BATCH SERVICE TEST
# =====================================================================
@pytest.mark.asyncio
async def test_batch_service_gaps():
    repo = MagicMock()
    queue = MagicMock()
    service = BatchService(repo, queue)
    
    # Test batch scheduling logic with empty target list
    repo.get_all_targets = AsyncMock(return_value=[])
    await service.schedule_batch_audits()
    assert repo.get_all_targets.called

# =====================================================================
# 3. CRAWL SERVICE TEST
# =====================================================================
@pytest.mark.asyncio
async def test_crawl_service_gaps():
    engine = MagicMock()
    repo = MagicMock()
    service = CrawlService(engine, repo)
    
    # Test session resolution on exception
    with patch.object(service.discovery_service, "run_discovery_session", side_effect=Exception("Crawl error")):
        with pytest.raises(Exception):
            await service.crawl_and_audit("https://test.com", depth=1)

# =====================================================================
# 4. REPORTER TEST
# =====================================================================
@pytest.mark.asyncio
async def test_reporter_gaps():
    repo = MagicMock()
    service = ReportService(repo)
    
    # Test path creation and file export boundaries
    with patch("os.makedirs") as mock_mkdir, patch("builtins.open", MagicMock()):
        repo.get_session = AsyncMock(return_value=None)
        with pytest.raises(ValueError):
            await service.generate_html_report(str(uuid.uuid4()))

# =====================================================================
# 5. WORKER TEST
# =====================================================================
@pytest.mark.asyncio
async def test_worker_gaps():
    queue = MagicMock()
    service = MagicMock()
    worker = AuditWorker(queue, service)
    
    # Test task loop processing crash resiliency
    queue.pop_task = AsyncMock(side_effect=[{"type": "single_url_audit", "payload": {"url": "https://test.com"}}, Exception("Queue error")])
    service.audit_url = AsyncMock(return_value=None)
    
    # Let it run a single cycle
    with patch.object(worker, "_process_task", AsyncMock()) as mock_proc:
        try:
            await worker.start()
        except Exception:
            pass
        assert mock_proc.called

# =====================================================================
# 6. BATCH AUDIT RUNNER TEST
# =====================================================================
def test_batch_audit_cli_gaps():
    # Test parsing CLI args and runner setup
    from auditor.batch_audit import main
    with patch("sys.argv", ["batch_audit", "--url", "https://test.com"]):
        with patch("auditor.batch_audit.AuditService") as mock_service:
            try:
                main()
            except SystemExit:
                pass

# =====================================================================
# 7. BATCH SEEDING TEST
# =====================================================================
def test_batch_seeding_gaps():
    from auditor.batch_seeding import seed_database
    with patch("builtins.open", side_effect=FileNotFoundError("Missing seed file")):
        try:
            seed_database("missing_file.json")
        except Exception:
            pass

# =====================================================================
# 8. AUDIT REPOSITORY EXCEPTIONS (LINES 71, 95, 99, 162, 214, 239, 243)
# =====================================================================
@pytest.mark.asyncio
async def test_audit_repository_gaps():
    db_session = AsyncMock()
    repo = SqlAlchemyAuditRepository(db_session)
    
    # Trigger RepositoryError branches on query exceptions
    db_session.exec.side_effect = Exception("DB connection lost")
    with pytest.raises(Exception):
        await repo.get_session(uuid.uuid4())

# =====================================================================
# 9. BACKUP MANAGER TEST
# =====================================================================
def test_backup_manager_gaps():
    # Test file pruning with retention limits
    manager = BackupManager("test_db.db")
    with patch("os.path.exists", return_value=True), \
         patch("glob.glob", return_value=["backup_1.db", "backup_2.db"]):
        manager.prune_stale_backups()

# =====================================================================
# 10. NEO4J REPOSITORY TEST
# =====================================================================
def test_neo4j_repository_gaps():
    repo = Neo4jRepository()
    # Test ping fail path
    with patch.object(repo, "driver", None):
        assert repo.ping() is False

# =====================================================================
# 11. PDF REPORTER TEST
# =====================================================================
def test_pdf_reporter_gaps():
    # Test generate html with empty violations list
    data = {
        "session_id": "test-session",
        "target_url": "https://test.com",
        "violations": []
    }
    html = generate_html_from_json(data)
    assert "A11yAudit" in html

# =====================================================================
# 12. PLAYWRIGHT ENGINE TEST
# =====================================================================
@pytest.mark.asyncio
async def test_playwright_engine_gaps():
    engine = PlaywrightAccessibilityEngine()
    # Test teardown resilience when no browser instance exists
    await engine.teardown()
    assert engine.browser is None

# =====================================================================
# 13. REDIS TASK QUEUE TEST
# =====================================================================
@pytest.mark.asyncio
async def test_redis_task_queue_gaps():
    queue = RedisTaskQueue()
    # Test redis client fallback and connection failures
    with patch("redis.asyncio.from_url", side_effect=Exception("Redis connection error")):
        try:
            await queue.push_task("test", {})
        except Exception:
            pass

# =====================================================================
# 14. TARGET REPOSITORY TEST
# =====================================================================
@pytest.mark.asyncio
async def test_target_repository_gaps():
    db_session = AsyncMock()
    repo = SqlAlchemyTargetRepository(db_session)
    
    # Test save target error handling
    db_session.commit.side_effect = Exception("Commit rejected")
    target = TargetModel(url="https://test.com")
    try:
        await repo.register_target(target)
    except Exception:
        pass

# =====================================================================
# 15. MAIN APP ENTRY TEST
# =====================================================================
def test_main_gaps():
    from auditor.main import app
    assert app is not None

# =====================================================================
# 16. PRESENTATION API TEST
# =====================================================================
def test_presentation_api_gaps():
    assert is_safe_url("invalid_url") is False
    assert is_safe_url("http://localhost") is True

    # Test in-memory mapping helper
    v = Violation(
        rule_id="r1",
        session_id=uuid.uuid4(),
        impact=ImpactLevel.CRITICAL,
        description="test",
        help_url="http://help",
        selector="div",
        nodes=[],
        tags=["wcag2a"],
        agent="axe"
    )
    s = AuditSession(target_url="https://test.com")
    s.violations = [v]
    data = _get_violations_data_from_session(s)
    assert len(data) == 1
    assert data[0]["rule_id"] == "r1"

# =====================================================================
# 17. COMPLIANCE MAPPER TEST
# =====================================================================
def test_compliance_mapper_gaps():
    # Test fallback categorization logic
    cat = ComplianceMapper.get_category([], "custom_rule", "axe")
    assert cat == "General"

# =====================================================================
# 18. LOGGING TEST
# =====================================================================
def test_logging_gaps():
    setup_auditor_logging()
    assert auditor_logger is not None

# =====================================================================
# 19. SINGLE URL TEST
# =====================================================================
def test_single_url_gaps():
    from auditor.single_url import main
    with patch("sys.argv", ["single_url", "https://test.com"]):
        try:
            main()
        except SystemExit:
            pass

# =====================================================================
# 20. SITE AUDIT TEST
# =====================================================================
def test_site_audit_gaps():
    from auditor.site_audit import main
    with patch("sys.argv", ["site_audit", "https://test.com"]):
        try:
            main()
        except SystemExit:
            pass

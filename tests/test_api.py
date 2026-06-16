import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import uuid
from uuid import UUID
import socket
import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from auditor.presentation.api import router, AuditRequest
from auditor.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_db_init():
    with patch("auditor.presentation.api.init_db", AsyncMock()), \
         patch("auditor.main.os.makedirs"):
        yield

def test_api_audit_direct_execution():
    mock_save_session = AsyncMock()
    mock_run_worker = AsyncMock()
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.save_session", mock_save_session), \
         patch("auditor.presentation.api.async_run_audit_worker", mock_run_worker):
        
        response = client.post("/api/audit", json={"url": "https://direct.com", "use_queue": False})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "session_id" in data
        mock_save_session.assert_called_once()

def test_api_audit_queued_execution():
    mock_save_session = AsyncMock()
    mock_push_task = AsyncMock()
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.save_session", mock_save_session), \
         patch("auditor.presentation.api.task_queue.push_task", mock_push_task):
        
        response = client.post("/api/audit", json={"url": "https://queued.com", "use_queue": True})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        mock_save_session.assert_called_once()
        mock_push_task.assert_called_once_with("single_url_audit", {"url": "https://queued.com"})

def test_api_audit_validation_error():
    """Verifies that posting an empty URL or invalid JSON format yields a 422 validation error."""
    # Post missing required 'url' field
    response = client.post("/api/audit", json={"scan_type": "precision"})
    assert response.status_code == 422
    
    # Post invalid parameter types
    response = client.post("/api/audit", json={"url": "https://test.com", "use_queue": "not-a-boolean"})
    assert response.status_code == 422

def test_api_dashboard_summary():
    """Verifies dashboard summaries correctly aggregate violation levels and categories from SQL sessions."""
    mock_list_recent = AsyncMock()
    
    # Setup mock session with standard violations
    mock_session = MagicMock()
    mock_session.agent_summary = None
    mock_session.started_at = None
    mock_session.status.value = "completed"
    
    mock_violation = MagicMock()
    mock_violation.impact.value = "critical"
    mock_violation.category = "perceivable"
    mock_violation.severity_matrix = "High"
    mock_session.violations = [mock_violation]
    mock_list_recent.return_value = [mock_session]
    
    mock_get_violations = AsyncMock(return_value=[{
        "impact": "critical",
        "category": "perceivable",
        "nodes": [{"impact": "critical"}]
    }])
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.list_recent_sessions", mock_list_recent), \
         patch("auditor.presentation.api.get_audit_violations", mock_get_violations):
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert data["health_score"] == 95
        assert data["rating"] == "A"
        assert data["issues"]["critical"] == 1
        assert data["issues"]["major"] == 0
        assert data["issues"]["minor"] == 0

def test_api_ping_graph_online():
    """Verifies that ping-graph reports online state when Neo4j is responsive."""
    mock_ping = MagicMock(return_value=True)
    with patch("auditor.presentation.api.Neo4jRepository.ping", mock_ping):
        response = client.get("/api/ping-graph")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

def test_api_ping_graph_offline():
    """Verifies that ping-graph reports offline state when Neo4j repository throws or fails."""
    mock_ping = MagicMock(return_value=False)
    with patch("auditor.presentation.api.Neo4jRepository.ping", mock_ping):
        response = client.get("/api/ping-graph")
        assert response.status_code == 200
        assert response.json()["status"] == "offline"

def test_api_graph_insights():
    """Verifies that graph insights correctly fetch from the Neo4jRepository graph engine."""
    mock_insights = MagicMock(return_value={
        "impact_probability": "Critical",
        "top_node": "Navbar",
        "component_id": "nav-id",
        "reach": 12,
        "violations_prevented": 5
    })
    
    mock_repo_inst = MagicMock()
    mock_repo_inst.driver = MagicMock()
    mock_repo_inst.get_graph_insights = mock_insights
    
    with patch("auditor.presentation.api.Neo4jRepository", return_value=mock_repo_inst):
        response = client.get("/api/audits/session-uuid/graph-insights")
        assert response.status_code == 200
        data = response.json()
        assert data["impact_probability"] == "Critical"
        assert data["top_node"] == "Navbar"
        assert data["reach"] == 12

def test_api_session_not_found():
    """Verifies that requests to non-existent session IDs yield a 404 Not Found error."""
    mock_get_session = AsyncMock(return_value=None)
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session):
        random_uuid = str(uuid.uuid4())
        response = client.get(f"/api/sessions/{random_uuid}")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]

        assert "Session not found" in response.json()["detail"]

def test_main_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online"}

def test_main_favicon():
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.json() == {}

import os
from unittest.mock import mock_open

def test_is_safe_url():
    from auditor.presentation.api import is_safe_url
    assert is_safe_url("invalid-url") is False
    assert is_safe_url("ftp://example.com") is False
    assert is_safe_url("http://") is False
    
    with patch.dict(os.environ, {"AUDITOR_ALLOW_LOCAL": "false"}):
        assert is_safe_url("http://localhost") is False
        assert is_safe_url("http://127.0.0.1") is False
        assert is_safe_url("http://192.168.1.1") is False
        
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            assert is_safe_url("http://google.com") is False
        with patch("socket.gethostbyname", side_effect=socket.gaierror):
            assert is_safe_url("http://google.com") is False

@pytest.mark.asyncio
async def test_api_audit_worker_loop_panic():
    from auditor.presentation.api import async_run_audit_worker
    
    mock_service = MagicMock()
    mock_service.execute_audit = AsyncMock(side_effect=RuntimeError("Worker panic test"))
    
    with patch("auditor.presentation.api.AuditService", return_value=mock_service), \
         patch("logging.getLogger") as mock_logger:
        await async_run_audit_worker("http://google.com")
        mock_logger.return_value.critical.assert_called()

def test_api_dashboard_summary_with_all_viol_types():
    mock_list_recent = AsyncMock()
    
    # Session 1: Completed, with multiple violation types
    session_1 = MagicMock()
    session_1.status.value = "completed"
    session_1.started_at = datetime.datetime.now()
    session_1.agent_summary = {"visual_count": 1, "motor_count": 2, "cognitive_count": 3, "neural_count": 4}
    
    v1 = MagicMock()
    v1.impact.value = "serious"
    v1.category = "perceivable"
    v1.severity_matrix = "Medium"
    
    v2 = MagicMock()
    v2.impact.value = "minor"
    v2.category = "operable"
    v2.severity_matrix = "Low"
    
    session_1.violations = [v1, v2]
    mock_list_recent.return_value = [session_1]
    
    mock_get_violations = AsyncMock(return_value=[
        {"impact": "serious", "category": "perceivable", "nodes": [{"impact": "serious"}]},
        {"impact": "minor", "category": "operable", "nodes": [{"impact": "minor"}]}
    ])
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.list_recent_sessions", mock_list_recent), \
         patch("auditor.presentation.api.get_audit_violations", mock_get_violations):
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["issues"]["major"] == 1
        assert data["issues"]["minor"] == 1
        assert data["agent_insights"]["breakdown"]["neural"] == 4

def test_api_audits_violations_categories_and_selectors():
    mock_get_session = AsyncMock()
    
    session = MagicMock()
    session.violations = []
    
    # 1. ARIA/Semantics rule
    v1 = MagicMock()
    v1.rule_id = "aria-allowed-attr"
    v1.impact.value = "serious"
    v1.description = "Aria description"
    v1.selector = "#test"
    v1.nodes = [{"target": "#node-target", "html": "<div>a</div>"}]
    session.violations.append(v1)
    
    # 2. Keyboard rule
    v2 = MagicMock()
    v2.rule_id = "keyboard-focus"
    v2.impact.value = "moderate"
    v2.description = "Keyboard description"
    v2.selector = ""
    v2.nodes = []
    session.violations.append(v2)
    
    # 3. Default category rule
    v3 = MagicMock()
    v3.rule_id = "other-rule"
    v3.impact.value = "critical"
    v3.description = "Other description"
    v3.selector = "#other"
    v3.nodes = []
    session.violations.append(v3)
    
    mock_get_session.return_value = session
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session):
        # Invalid UUID format
        response = client.get("/api/audits/invalid-uuid/violations")
        assert response.status_code == 200
        assert response.json() == []
        
        # Valid UUID
        valid_uuid = str(uuid.uuid4())
        response = client.get(f"/api/audits/{valid_uuid}/violations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["category"] == "ARIA & Semantics"
        assert data[0]["target"] == "#node-target"
        assert data[1]["category"] == "Keyboard Navigation"
        assert data[2]["category"] == "Structure"

def test_api_static_posts():
    response = client.post("/api/violations/some-id/fix")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.post("/api/sessions/some-id/remediate")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.post("/api/graph/fix", json={"component_id": "navbar"})
    assert response.status_code == 200
    assert response.json()["patched_component"] == "navbar"
    
    response = client.post("/api/support/ticket", json={"msg": "help"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_api_graph_operations_mock():
    mock_repo = MagicMock()
    mock_repo.driver = None
    
    with patch("auditor.presentation.api.Neo4jRepository", return_value=mock_repo):
        response = client.get("/api/audits/some-id/graph")
        assert response.json() == {"nodes": [], "links": []}
        
        response = client.get("/api/audits/some-id/graph-insights")
        assert response.json()["reach"] == 0
        
    mock_repo.driver = MagicMock()
    mock_repo.get_graph_data.return_value = {"nodes": [1], "links": []}
    mock_repo.get_graph_insights.return_value = {"reach": 100}
    
    with patch("auditor.presentation.api.Neo4jRepository", return_value=mock_repo):
        response = client.get("/api/audits/some-id/graph")
        assert response.json() == {"nodes": [1], "links": []}
        
        response = client.get("/api/audits/some-id/graph-insights")
        assert response.json()["reach"] == 100
        
        response = client.get("/api/graph-visualization")
        assert response.status_code == 200

def test_api_history_and_profile():
    mock_list_recent = AsyncMock()
    s = MagicMock()
    s.id = uuid.uuid4()
    s.target_url = "http://test.com"
    s.started_at = None
    s.violations = []
    s.status.value = "completed"
    s.agent_summary = {}
    mock_list_recent.return_value = [s]
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.list_recent_sessions", mock_list_recent):
        response = client.get("/api/audits/history")
        assert response.status_code == 200
        assert len(response.json()) == 1
        
    response = client.get("/api/user/profile")
    assert response.json()["role"] == "Auditor"
    
    response = client.get("/api/user/export-logs")
    assert response.status_code == 200

def test_api_sessions_detail():
    # Invalid session UUID
    response = client.get("/api/sessions/invalid-uuid")
    assert response.status_code == 400
    
    # Session not found
    mock_get_session = AsyncMock(return_value=None)
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session):
        response = client.get(f"/api/sessions/{uuid.uuid4()}")
        assert response.status_code == 404
        
    # Session present
    mock_session = MagicMock()
    mock_session.target_url = "http://target.com"
    mock_session.status.value = "completed"
    mock_session.updated_at = datetime.datetime.now()
    mock_session.remediation_plan = "plan"
    mock_session.agent_summary = {}
    mock_session.violations = []
    
    mock_get_session.return_value = mock_session
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session):
        response = client.get(f"/api/sessions/{uuid.uuid4()}")
        assert response.status_code == 200
        assert response.json()["remediation_plan"] == "plan"

@pytest.mark.asyncio
async def test_api_reports_download_flow():
    from auditor.presentation.api import download_report
    session_id = str(uuid.uuid4())
    
    # Fallback 1: combined PDF matches
    with patch("glob.glob", return_value=["/exports/audit_report_123.pdf"]), \
         patch("os.path.getctime", return_value=123.0), \
         patch("auditor.presentation.api.FileResponse") as mock_file_response:
        await download_report(session_id, MagicMock())
        mock_file_response.assert_called_once()
        
    # Fallback 2: missing but regenerated on-the-fly
    mock_get_session = AsyncMock()
    mock_session = MagicMock()
    mock_session.id = UUID(session_id)
    mock_get_session.return_value = mock_session
    
    mock_reporter = MagicMock()
    mock_reporter.generate_summary_report = AsyncMock(return_value={"pdf": "/exports/regenerated.pdf"})
    
    with patch("glob.glob") as mock_glob, \
         patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session), \
         patch("auditor.application.reporter.AuditReporter", return_value=mock_reporter), \
         patch("os.path.getctime", return_value=124.0), \
         patch("auditor.presentation.api.FileResponse") as mock_file_response:
        
        # First call: return empty for matches first, then match the regenerated one
        mock_glob.side_effect = [[], ["/exports/regenerated.pdf"]]
        await download_report(session_id, MagicMock())
        mock_file_response.assert_called_once()

    # Fallback 3: check domain pattern match
    mock_session.target_url = "http://mypage.com"
    with patch("glob.glob") as mock_glob, \
         patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session), \
         patch("os.path.getctime", return_value=125.0), \
         patch("auditor.presentation.api.FileResponse") as mock_file_response:
          
        mock_glob.side_effect = [[], [], ["/exports/mypage_findings.pdf"], []]
        await download_report(session_id, MagicMock())
        mock_file_response.assert_called_once()

    # Case: completely not found
    with patch("glob.glob", return_value=[]), \
         patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as exc:
            await download_report(session_id, MagicMock())
        assert exc.value.status_code == 404

def test_api_reports_generate_manual():
    session_id = str(uuid.uuid4())
    
    mock_reporter = MagicMock()
    mock_reporter.generate_summary_report = AsyncMock(return_value={"json": "/exports/session.json"})
    
    with patch("auditor.application.reporter.AuditReporter", return_value=mock_reporter), \
         patch("auditor.presentation.api.convert_json_to_pdf") as mock_convert, \
         patch("asyncio.to_thread", AsyncMock()) as mock_thread:
        response = client.post(f"/api/reports/{session_id}/generate")
        assert response.status_code == 200
        assert "regenerated successfully" in response.json()["message"]

def test_main_lifespan_startup():
    with patch("auditor.main.init_db", AsyncMock()) as mock_init:
        with TestClient(app) as local_client:
            mock_init.assert_called_once()

def test_api_scans_creation():
    mock_save_session = AsyncMock()
    mock_run_worker = AsyncMock()
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.save_session", mock_save_session), \
         patch("auditor.presentation.api.async_run_audit_worker", mock_run_worker):
        
        response = client.post("/api/scans", json={"url": "https://scans-test.com", "depth": 1, "agent": "secure_auditor"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "scan_id" in data
        mock_save_session.assert_called_once()

def test_api_update_user_settings():
    mock_save = MagicMock()
    with patch("auditor.presentation.api.save_persisted_settings", mock_save):
        response = client.patch("/api/user/settings", json={"concurrency": 8, "ruleset": "wcag22aaa"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_save.assert_called_once_with({"concurrency": 8, "ruleset": "wcag22aaa", "max_depth": None, "timeout": None, "skip_external": None, "user_agent": None, "politeness_delay": None, "ignored_patterns": None, "retry_limit": None, "robots_txt": None, "audit_scope": None, "report_template": None, "ignored_selectors": None})


def test_api_audits_detail():
    # Invalid session UUID
    response = client.get("/api/audits/invalid-uuid")
    assert response.status_code == 400
    
    # Session not found
    mock_get_session = AsyncMock(return_value=None)
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session):
        response = client.get(f"/api/audits/{uuid.uuid4()}")
        assert response.status_code == 404
        
    # Session present
    mock_session = MagicMock()
    mock_session.target_url = "http://target.com"
    mock_session.status.value = "failed"
    mock_session.started_at = datetime.datetime.now()
    mock_session.updated_at = datetime.datetime.now()
    mock_session.remediation_plan = "remediation details"
    mock_session.agent_summary = {"applied_config": {"agent": "secure_auditor"}}
    mock_session.error_message = "Target host unreachable"
    mock_session.violations = []
    
    mock_get_session.return_value = mock_session
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.get_session", mock_get_session), \
         patch("auditor.presentation.api.get_audit_violations", AsyncMock(return_value=[])):
        response = client.get(f"/api/audits/{uuid.uuid4()}")
        assert response.status_code == 200
        data = response.json()
        assert data["remediation_plan"] == "remediation details"
        assert data["error_message"] == "Target host unreachable"
        assert data["status"] == "failed"
        assert data["agent_summary"]["applied_config"]["agent"] == "secure_auditor"


def test_api_export_logs_success():
    with patch("os.path.exists", return_value=True), \
         patch("auditor.presentation.api.FileResponse", return_value=MagicMock()) as mock_file_response:
        response = client.get("/api/user/export-logs")
        assert response.status_code == 200
        mock_file_response.assert_called_once()

def test_api_export_logs_missing():
    with patch("os.path.exists", return_value=False):
        response = client.get("/api/user/export-logs")
        assert response.status_code == 200
        assert "No logs recorded yet." in response.text


def test_api_get_violation_endpoint():
    # 1. Test invalid UUID format -> 400
    response = client.get("/api/violations/not-a-uuid")
    assert response.status_code == 400
    assert "Invalid violation ID" in response.json()["detail"]

    # 2. Test violation not found -> 404
    mock_exec = MagicMock()
    mock_exec.first = MagicMock(return_value=None)
    mock_exec.all = MagicMock(return_value=[])
    
    mock_db_session = MagicMock()
    mock_db_session.exec = AsyncMock(return_value=mock_exec)
    
    mock_db_context = AsyncMock()
    mock_db_context.__aenter__.return_value = mock_db_session
    
    with patch("auditor.presentation.api.AsyncSession", return_value=mock_db_context):
        response = client.get(f"/api/violations/{uuid.uuid4()}")
        assert response.status_code == 404
        assert "Violation not found" in response.json()["detail"]
        
    # 3. Test violation found (direct lookup) -> 200
    mock_violation = MagicMock()
    mock_violation.id = uuid.uuid4()
    mock_violation.session_id = uuid.uuid4()
    mock_violation.rule_id = "color-contrast"
    mock_violation.selector = "div > p"
    mock_violation.description = "Low contrast"
    mock_violation.nodes = [{"html": "<span>text</span>", "target": "span", "failure_summary": "low contrast"}]
    
    mock_exec_found = MagicMock()
    mock_exec_found.first = MagicMock(return_value=mock_violation)
    mock_exec_found.all = MagicMock(return_value=[mock_violation])
    
    mock_db_session_found = MagicMock()
    mock_db_session_found.exec = AsyncMock(return_value=mock_exec_found)
    
    mock_db_context_found = AsyncMock()
    mock_db_context_found.__aenter__.return_value = mock_db_session_found
    
    with patch("auditor.presentation.api.AsyncSession", return_value=mock_db_context_found):
        response = client.get(f"/api/violations/{mock_violation.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_violation.id)
        assert data["rule_id"] == "color-contrast"
        assert "fix" in data

@pytest.mark.asyncio
async def test_api_cleanup_orphaned_targets():
    from auditor.presentation.api import cleanup_orphaned_targets
    from auditor.domain.models import DomainStatus
    
    mock_domain = MagicMock()
    mock_domain.status = DomainStatus.CRAWLING
    
    mock_repo = AsyncMock()
    mock_repo.get_all_domains.return_value = [mock_domain]
    
    mock_db = AsyncMock()
    
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = mock_db
        
        await cleanup_orphaned_targets()
        
        status_val = mock_domain.status.value if hasattr(mock_domain.status, 'value') else str(mock_domain.status)
        assert status_val == "failed" or mock_domain.status == DomainStatus.FAILED
        assert mock_repo.update_domain.called
        assert mock_db.commit.called

    # Test exception handling
    mock_repo.get_all_domains.side_effect = Exception("DB error")
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = mock_db
        await cleanup_orphaned_targets() # Should not raise exception

@pytest.mark.asyncio
async def test_api_run_audit_worker_pdf_generation_fails():
    from auditor.presentation.api import async_run_audit_worker
    
    mock_session = MagicMock()
    mock_session.status.value = "completed"
    mock_session.id = uuid.uuid4()
    
    mock_repo = AsyncMock()
    mock_repo.execute_audit = AsyncMock(return_value=mock_session)
    
    mock_db_session = AsyncMock()
    
    # Reporter raises error
    with patch("auditor.presentation.api.AsyncSession") as mock_sess_cls, \
         patch("auditor.presentation.api.SqlAlchemyAuditRepository"), \
         patch("auditor.presentation.api.AuditService", return_value=mock_repo), \
         patch("auditor.application.reporter.AuditReporter.generate_summary_report", side_effect=Exception("PDF error")), \
         patch("logging.getLogger") as mock_log:
        
        mock_sess_cls.return_value.__aenter__.return_value = mock_db_session
        await async_run_audit_worker("http://google.com")
        mock_log.return_value.error.assert_called()

def test_api_start_audit_proactor_diagnostics():
    import inspect
    import asyncio
    original_get_running_loop = asyncio.get_running_loop
    
    def mock_get_running_loop():
        frame = inspect.currentframe()
        try:
            while frame:
                if frame.f_code.co_name == "start_audit":
                    mock_loop = MagicMock()
                    mock_loop.__class__.__name__ = "SelectorEventLoop"
                    return mock_loop
                frame = frame.f_back
        finally:
            del frame
        return original_get_running_loop()

    with patch("sys.platform", "win32"), \
         patch("asyncio.get_running_loop", side_effect=mock_get_running_loop), \
         patch("auditor.presentation.api.is_safe_url", return_value=True), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls, \
         patch("logging.getLogger") as mock_log:
         
        mock_db = AsyncMock()
        mock_begin_ctx = AsyncMock()
        mock_db.begin = MagicMock(return_value=mock_begin_ctx)
        
        mock_db_context = AsyncMock()
        mock_db_context.__aenter__.return_value = mock_db
        mock_sess_cls.return_value = mock_db_context
        
        response = client.post("/api/audit", json={"url": "http://direct.com"})
        assert response.status_code == 200
        mock_log.return_value.critical.assert_called()

def test_api_verify_violation_endpoint():
    # Invalid verification status
    response = client.patch(f"/api/violations/{uuid.uuid4()}/verify", json={"status": "invalid"})
    assert response.status_code == 400
    
    # Violation not found
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_db_sess = AsyncMock()
    mock_db_sess.exec.return_value = mock_exec
    
    with patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = mock_db_sess
        response = client.patch(f"/api/violations/{uuid.uuid4()}/verify", json={"status": "true_positive"})
        assert response.status_code == 404
        
    # Success path
    mock_viol = MagicMock()
    mock_exec.first.return_value = mock_viol
    with patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = mock_db_sess
        v_id = uuid.uuid4()
        response = client.patch(f"/api/violations/{v_id}/verify", json={"status": "true_positive"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"

def test_api_get_targets():
    mock_domain = MagicMock()
    mock_domain.id = uuid.uuid4()
    mock_domain.url = "http://target.com"
    mock_domain.status.value = "active"
    mock_domain.created_at = None
    mock_domain.last_audit_at = None
    mock_domain.frequency_hours = 24
    mock_domain.priority = 3
    mock_domain.retry_count = 0
    mock_domain.last_error = None
    mock_domain.scan_profile = {}
    
    mock_repo = AsyncMock()
    mock_repo.get_all_domains.return_value = [mock_domain]
    
    mock_exec = MagicMock()
    mock_session_model = MagicMock()
    mock_session_model.id = uuid.uuid4()
    mock_exec.first.return_value = mock_session_model
    
    mock_db = AsyncMock()
    mock_db.exec.return_value = mock_exec
    
    with patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = mock_db
        response = client.get("/api/targets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_session_id"] == str(mock_session_model.id)

def test_api_get_target_diff():
    mock_diff = AsyncMock(return_value={"diff": "details"})
    with patch("auditor.application.diff_service.AuditDiffService.calculate_diff_by_target", mock_diff):
        response = client.get("/api/targets/diff?url=http://target.com")
        assert response.status_code == 200
        assert response.json() == {"diff": "details"}

def test_api_create_target_already_exists():
    mock_domain = MagicMock()
    mock_domain.id = uuid.uuid4()
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.return_value = mock_domain
    
    with patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets", json={"url": "http://target.com"})
        assert response.status_code == 200
        assert response.json()["status"] == "already_exists"

def test_api_update_target_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.return_value = None
    
    with patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets/update", json={"url": "http://target.com"})
        assert response.status_code == 404

def test_api_prune_targets():
    mock_domain = MagicMock()
    mock_domain.url = "http://target.com"
    from auditor.domain.models import DomainStatus
    mock_domain.status = DomainStatus.FAILED
    
    mock_domain2 = MagicMock()
    mock_domain2.url = "http://target2.com"
    mock_domain2.status = DomainStatus.ACTIVE
    
    mock_repo = AsyncMock()
    mock_repo.get_all_domains.return_value = [mock_domain, mock_domain2]
    
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets/prune")
        assert response.status_code == 200
        assert response.json()["pruned_count"] == 1

def test_api_toggle_target():
    # Case target not found
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.return_value = None
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets/toggle", json={"url": "http://target.com"})
        assert response.status_code == 404

    # Case active -> paused
    mock_domain = MagicMock()
    from auditor.domain.models import DomainStatus
    mock_domain.status = DomainStatus.ACTIVE
    mock_repo.get_domain_by_url.return_value = mock_domain
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets/toggle", json={"url": "http://target.com"})
        assert response.json()["new_status"] == "paused"

    # Case paused -> active
    mock_domain.status = DomainStatus.PAUSED
    mock_repo.get_domain_by_url.return_value = mock_domain
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets/toggle", json={"url": "http://target.com"})
        assert response.json()["new_status"] == "active"

def test_api_delete_target():
    mock_repo = AsyncMock()
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.delete("/api/targets?url=http://target.com")
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_api_async_run_discovery():
    from auditor.presentation.api import async_run_discovery
    
    mock_discovery = AsyncMock()
    mock_discovery.run_discovery_session = AsyncMock()
    
    with patch("auditor.infrastructure.link_extractor.PlaywrightLinkExtractor") as mock_ext, \
         patch("auditor.domain.crawler.LinkDiscoveryService"), \
         patch("auditor.application.discovery_service.DiscoveryService", return_value=mock_discovery), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
         
        mock_ext.return_value.teardown = AsyncMock()
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        await async_run_discovery("http://target.com")
        assert mock_discovery.run_discovery_session.called

    # Test error handling path
    mock_discovery.run_discovery_session.side_effect = Exception("Discovery failed")
    with patch("auditor.infrastructure.link_extractor.PlaywrightLinkExtractor") as mock_ext, \
         patch("auditor.domain.crawler.LinkDiscoveryService"), \
         patch("auditor.application.discovery_service.DiscoveryService", return_value=mock_discovery), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls, \
         patch("logging.getLogger") as mock_log:
          
        mock_ext.return_value.teardown = AsyncMock()
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        await async_run_discovery("http://target.com")
        assert mock_log.return_value.error.called

def test_api_discover_targets_endpoint():
    with patch("auditor.presentation.api.is_safe_url", return_value=True), \
         patch("auditor.presentation.api.async_run_discovery") as mock_bg:
        response = client.post("/api/targets/discover", json={"url": "http://target.com"})
        assert response.status_code == 200
        assert response.json()["status"] == "started"

def test_api_batch_status():
    mock_manager = MagicMock()
    mock_manager.get_system_health_report = AsyncMock(return_value={"status": "healthy"})
    
    with patch("auditor.application.batch_service.BatchAuditManager", return_value=mock_manager):
        response = client.get("/api/batch/status")
        assert response.status_code == 200
        assert "cpu_percent" in response.json()

def test_api_batch_exports():
    # export_batch_csv success
    with patch("auditor.application.batch_exporter.BatchReportExporter.generate_aggregated_csv", AsyncMock(return_value="/exports/batch.csv")), \
         patch("os.path.exists", return_value=True), \
         patch("auditor.presentation.api.FileResponse") as mock_file:
        response = client.get("/api/batch/export/csv")
        assert response.status_code == 200
        
    # export_violations_csv success
    with patch("auditor.application.batch_exporter.BatchReportExporter.generate_detailed_violations_csv", AsyncMock(return_value="/exports/violations.csv")), \
         patch("os.path.exists", return_value=True), \
         patch("auditor.presentation.api.FileResponse") as mock_file:
        response = client.get("/api/batch/export/violations/csv")
        assert response.status_code == 200

def test_api_ensure_directories_permission_error():
    from auditor.presentation.api import ensure_directories
    with patch("os.makedirs", side_effect=PermissionError("Permission denied")), \
         pytest.raises(PermissionError):
        ensure_directories()

def test_api_ensure_directories_success():
    from auditor.presentation.api import ensure_directories
    with patch("os.makedirs") as mock_makedirs:
        ensure_directories()
        assert mock_makedirs.called

def test_api_update_target_success():
    mock_domain = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.return_value = mock_domain
    
    with patch("auditor.infrastructure.target_repository.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.SqlAlchemyTargetRepository", return_value=mock_repo), \
         patch("auditor.presentation.api.AsyncSession") as mock_sess_cls:
        mock_sess_cls.return_value.__aenter__.return_value = AsyncMock()
        response = client.post("/api/targets/update", json={
            "url": "http://target.com",
            "priority": 1,
            "frequency_hours": 12,
            "scan_profile": {"custom": True}
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert mock_domain.priority == 1
        assert mock_domain.frequency_hours == 12
        assert mock_domain.scan_profile == {"custom": True}

def test_api_batch_exports_failures():
    # export_batch_csv failure
    with patch("auditor.application.batch_exporter.BatchReportExporter.generate_aggregated_csv", AsyncMock(return_value=None)):
        response = client.get("/api/batch/export/csv")
        assert response.status_code == 500
        assert "Failed to compile" in response.json()["detail"]
        
    with patch("auditor.application.batch_exporter.BatchReportExporter.generate_aggregated_csv", AsyncMock(return_value="/nonexistent/path.csv")), \
         patch("os.path.exists", return_value=False):
        response = client.get("/api/batch/export/csv")
        assert response.status_code == 500

    # export_violations_csv failure
    with patch("auditor.application.batch_exporter.BatchReportExporter.generate_detailed_violations_csv", AsyncMock(return_value=None)):
        response = client.get("/api/batch/export/violations/csv")
        assert response.status_code == 500
        assert "Failed to compile" in response.json()["detail"]

    with patch("auditor.application.batch_exporter.BatchReportExporter.generate_detailed_violations_csv", AsyncMock(return_value="/nonexistent/path.csv")), \
         patch("os.path.exists", return_value=False):
        response = client.get("/api/batch/export/violations/csv")
        assert response.status_code == 500

def test_api_run_batch_audit_background():
    with patch("auditor.presentation.api.async_run_batch_audit_manager") as mock_bg:
        response = client.post("/api/batch/run", json={"use_queue": False})
        assert response.status_code == 200
        assert response.json()["status"] == "started"

def test_api_batch_status_error():
    mock_manager = MagicMock()
    mock_manager.get_system_health_report.side_effect = Exception("System status retrieval failed")
    with patch("auditor.application.batch_service.BatchAuditManager", return_value=mock_manager):
        response = client.get("/api/batch/status")
        assert response.status_code == 500
        assert "System status retrieval failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_api_async_run_batch_audit_manager():
    from auditor.presentation.api import async_run_batch_audit_manager
    mock_manager = MagicMock()
    mock_manager.run_batch_audit = AsyncMock()
    
    with patch("auditor.application.batch_service.BatchAuditManager", return_value=mock_manager):
        await async_run_batch_audit_manager()
        assert mock_manager.run_batch_audit.called

    # Error path
    mock_manager.run_batch_audit.side_effect = Exception("Batch audit failure")
    with patch("auditor.application.batch_service.BatchAuditManager", return_value=mock_manager), \
         patch("logging.getLogger") as mock_log:
        await async_run_batch_audit_manager()
        assert mock_log.return_value.error.called







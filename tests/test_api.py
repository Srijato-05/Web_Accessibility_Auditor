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
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.list_recent_sessions", mock_list_recent):
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
    
    with patch("auditor.presentation.api.SqlAlchemyAuditRepository.list_recent_sessions", mock_list_recent):
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





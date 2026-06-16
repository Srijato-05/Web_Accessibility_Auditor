import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime
from auditor.application.diff_service import AuditDiffService
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel

class AsyncMockSession:
    def __init__(self, sessions=None):
        self.sessions = sessions or []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def exec(self, query):
        mock_result = MagicMock()
        mock_result.all.return_value = self.sessions
        return mock_result

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def sample_violations():
    s_id = uuid4()
    v1 = ViolationModel(id=uuid4(), session_id=s_id, rule_id="rule1", url="/page1", selector="#btn1", impact="minor", description="d1")
    v2 = ViolationModel(id=uuid4(), session_id=s_id, rule_id="rule2", url="/page1", selector="#img1", impact="critical", description="d2")
    v3 = ViolationModel(id=uuid4(), session_id=s_id, rule_id="rule3", url="/page2", selector=".nav", impact="moderate", description="d3")
    return [v1, v2, v3]

@pytest.mark.asyncio
@patch("auditor.application.diff_service.AsyncSession")
async def test_calculate_diff_insufficient_data(mock_async_session, mock_engine):
    # Only 1 session returned
    session1 = AuditSessionModel(id=uuid4(), target_url="https://example.com", status="completed")
    mock_async_session.return_value = AsyncMockSession(sessions=[session1])
    
    diff_service = AuditDiffService(mock_engine)
    result = await diff_service.calculate_diff_by_target("https://example.com")
    
    assert result["status"] == "insufficient_data"
    assert result["scans_found"] == 1

@pytest.mark.asyncio
@patch("auditor.application.diff_service.AsyncSession")
async def test_calculate_diff_success(mock_async_session, mock_engine, sample_violations):
    # session_new (latest)
    s_new_id = uuid4()
    v1_new = ViolationModel(id=uuid4(), session_id=s_new_id, rule_id="rule1", url="/page1", selector="#btn1", impact="minor", description="d1")
    v4_new = ViolationModel(id=uuid4(), session_id=s_new_id, rule_id="rule4", url="/page3", selector="footer", impact="minor", description="d4") # new
    
    session_new = AuditSessionModel(
        id=s_new_id, 
        target_url="https://example.com", 
        status="completed",
        completed_at=datetime.now()
    )
    session_new.violations = [v1_new, v4_new]
    
    # session_old
    s_old_id = uuid4()
    v1_old = ViolationModel(id=uuid4(), session_id=s_old_id, rule_id="rule1", url="/page1", selector="#btn1", impact="minor", description="d1")
    v2_old = ViolationModel(id=uuid4(), session_id=s_old_id, rule_id="rule2", url="/page1", selector="#img1", impact="critical", description="d2")
    
    session_old = AuditSessionModel(
        id=s_old_id, 
        target_url="https://example.com", 
        status="completed",
        completed_at=datetime.now()
    )
    session_old.violations = [v1_old, v2_old]
    
    # The query order_by desc means new is first, old is second
    mock_async_session.return_value = AsyncMockSession(sessions=[session_new, session_old])
    
    diff_service = AuditDiffService(mock_engine)
    result = await diff_service.calculate_diff_by_target("https://example.com")
    
    assert result["status"] == "success"
    assert result["summary"]["new_count"] == 1
    assert result["summary"]["fixed_count"] == 1
    assert result["summary"]["remaining_count"] == 1
    
    assert len(result["new_violations"]) == 1
    assert result["new_violations"][0]["rule_id"] == "rule4"
    
    assert len(result["fixed_violations"]) == 1
    assert result["fixed_violations"][0]["rule_id"] == "rule2"
    
    assert len(result["remaining_violations"]) == 1
    assert result["remaining_violations"][0]["rule_id"] == "rule1"

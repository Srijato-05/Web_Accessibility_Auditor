import os
import pytest
import csv
from unittest.mock import patch, MagicMock
from sqlmodel import SQLModel, Field, select
from datetime import datetime
from uuid import uuid4
from auditor.application.batch_exporter import BatchReportExporter
from auditor.infrastructure.persistence_models import TargetModel, AuditSessionModel, ViolationModel

# Setup an async mock engine for testing
class AsyncMockSession:
    def __init__(self, targets=None, sessions=None):
        self.targets = targets or []
        self.sessions = sessions or []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def exec(self, query):
        mock_result = MagicMock()
        # Simplified query matching based on what the exporter does
        query_str = str(query).lower()
        if "targets" in query_str:
            mock_result.all.return_value = self.targets
        elif "audit_sessions" in query_str:
            mock_result.first.return_value = self.sessions[0] if self.sessions else None
        else:
            mock_result.all.return_value = []
            mock_result.first.return_value = None
        return mock_result

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def sample_target():
    return TargetModel(url="https://example.com", status="completed")

@pytest.fixture
def sample_violation():
    return ViolationModel(
        rule_id="color-contrast",
        impact="critical",
        description="Text has insufficient contrast.",
        help_url="https://help.url",
        selector="#bad-text",
        tags=["wcag2aa"],
        url="https://example.com/page1",
        nodes=[{"html": "<p id='bad-text'>Hello</p>"}]
    )

@pytest.fixture
def sample_session(sample_violation):
    session = AuditSessionModel(
        target_url="https://example.com",
        status="completed",
        completed_at=datetime.now()
    )
    session.violations = [sample_violation]
    return session

@pytest.mark.asyncio
@patch("auditor.application.batch_exporter.AsyncSession")
async def test_generate_aggregated_csv_no_targets(mock_async_session, mock_engine, tmp_path):
    mock_async_session.return_value = AsyncMockSession(targets=[])
    
    with patch("auditor.application.batch_exporter.EXPORTS_DIR", str(tmp_path)):
        exporter = BatchReportExporter(mock_engine)
        csv_path = await exporter.generate_aggregated_csv()
        
        assert csv_path is not None
        assert os.path.exists(csv_path)
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert "Target URL" in headers

@pytest.mark.asyncio
@patch("auditor.application.batch_exporter.AsyncSession")
async def test_generate_aggregated_csv_with_data(mock_async_session, mock_engine, tmp_path, sample_target, sample_session):
    mock_async_session.return_value = AsyncMockSession(targets=[sample_target], sessions=[sample_session])
    
    with patch("auditor.application.batch_exporter.EXPORTS_DIR", str(tmp_path)):
        exporter = BatchReportExporter(mock_engine)
        csv_path = await exporter.generate_aggregated_csv()
        
        assert csv_path is not None
        assert os.path.exists(csv_path)
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["Target URL"] == "https://example.com"
            assert rows[0]["Total Violations Count"] == "1"
            assert rows[0]["Critical Violations"] == "1"

@pytest.mark.asyncio
@patch("auditor.application.batch_exporter.AsyncSession")
async def test_generate_detailed_violations_csv(mock_async_session, mock_engine, tmp_path, sample_target, sample_session):
    mock_async_session.return_value = AsyncMockSession(targets=[sample_target], sessions=[sample_session])
    
    with patch("auditor.application.batch_exporter.EXPORTS_DIR", str(tmp_path)):
        exporter = BatchReportExporter(mock_engine)
        csv_path = await exporter.generate_detailed_violations_csv()
        
        assert csv_path is not None
        assert os.path.exists(csv_path)
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["Target Site URL"] == "https://example.com"
            assert rows[0]["Violating HTML Snippet"] == "<p id='bad-text'>Hello</p>"
            assert rows[0]["Rule ID"] == "color-contrast"

@pytest.mark.asyncio
@patch("auditor.application.batch_exporter.AsyncSession")
async def test_batch_exporter_edge_cases(mock_async_session, mock_engine, tmp_path, sample_target):
    # Case 1: Target has no session
    mock_async_session.return_value = AsyncMockSession(targets=[sample_target], sessions=[])
    with patch("auditor.application.batch_exporter.EXPORTS_DIR", str(tmp_path)):
        exporter = BatchReportExporter(mock_engine)
        csv_path = await exporter.generate_aggregated_csv()
        assert csv_path is not None
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert rows[0]["Scan Status"] == "COMPLETED"

    # Case 2: Exception handling
    mock_async_session.side_effect = Exception("DB error")
    exporter = BatchReportExporter(mock_engine)
    res = await exporter.generate_aggregated_csv()
    assert res is None
    
    res_detail = await exporter.generate_detailed_violations_csv()
    assert res_detail is None

    # Case 3: Different tags and impact coverage
    v_other = ViolationModel(
        rule_id="other-rule",
        impact="serious",
        description="serious violation",
        help_url="https://help.url",
        selector="#serious-element",
        tags=["wcag2a", "wcag21", "section508"],
        url="https://example.com/page2",
        nodes=[]
    )
    v_mod = ViolationModel(
        rule_id="mod-rule",
        impact="moderate",
        tags=["some-other-tag"],
        url=""
    )
    v_minor = ViolationModel(
        rule_id="minor-rule",
        impact="minor",
        tags=[]
    )
    session = AuditSessionModel(
        target_url="https://example.com",
        status="completed",
        completed_at=None
    )
    session.violations = [v_other, v_mod, v_minor]
    
    # We directly test _aggregate_session_data
    res_data = exporter._aggregate_session_data("https://example.com", session)
    assert res_data["Serious Violations"] == 1
    assert res_data["Moderate Violations"] == 1
    assert res_data["Minor Violations"] == 1
    assert res_data["WCAG 2.0 Violations"] == 1
    assert res_data["WCAG 2.1 Violations"] == 1
    assert res_data["Section 508 Violations"] == 1
    assert res_data["Audit Completed At"] == "N/A"

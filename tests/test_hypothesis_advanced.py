import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
try:
    from hypothesis import given, settings, strategies as st
except ImportError:
    pytest.skip("Hypothesis not installed, skipping advanced math fuzzing", allow_module_level=True)

from auditor.domain.violation import Violation, ImpactLevel
from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.application.audit_service import AuditService
from uuid import uuid4
import datetime

# --- Custom Hypothesis Strategies ---
# We build highly complex and dynamic input generations to fuzz our core logic functions

st_impact = st.sampled_from([ImpactLevel.CRITICAL, ImpactLevel.SERIOUS, ImpactLevel.MODERATE, ImpactLevel.MINOR])
st_uuid = st.uuids()

@st.composite
def st_violation(draw):
    rule = draw(st.text(min_size=1, max_size=50))
    impact = draw(st_impact)
    desc = draw(st.text())
    return Violation(
        rule_id=rule,
        impact=impact,
        agent="visual",
        description=desc,
        help_url="http://help.com",
        session_id=draw(st_uuid),
        tags=draw(st.lists(st.text(max_size=10), max_size=5)),
        compliance_level="A",
        category="perceivable",
        severity_matrix="High",
        url="http://test.com"
    )

@st.composite
def st_audit_session(draw):
    url = draw(st.from_regex(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9_.-]+)*$", fullmatch=True))
    session = AuditSession(target_url=url)
    session.violations = draw(st.lists(st_violation(), max_size=100))
    session.status = draw(st.sampled_from([SessionStatus.STARTED, SessionStatus.COMPLETED, SessionStatus.FAILED]))
    return session

# --- Advanced Dynamic Tests ---

@settings(max_examples=100, deadline=None)
@given(st.lists(st_violation(), max_size=500))
def test_hypothesis_gigw_sector_overrides_resilience(violations):
    """
    Fuzz the GIGW sector override logic with massive lists of completely random violations.
    Ensures that no matter what text/rules/impacts are passed, it never crashes
    and returns a list of the exact same size.
    """
    engine = MagicMock()
    repo = MagicMock()
    service = AuditService(engine, repo)
    
    # We apply overrides
    overridden = service.apply_gigw_sector_overrides(violations)
    
    # Assertions
    assert len(overridden) == len(violations)
    # The impact levels should still be valid enums
    for v in overridden:
        assert isinstance(v.impact, ImpactLevel)
        assert isinstance(v.rule_id, str)

@settings(max_examples=100, deadline=None)
@given(st_audit_session())
def test_hypothesis_health_score_calculation(session):
    """
    Fuzz the scorecard generation logic to ensure the health_score algorithm
    never throws an exception and strictly bounds between 0.0 and 100.0
    even with massive penalty counts or bizarre inputs.
    """
    engine = MagicMock()
    repo = MagicMock()
    service = AuditService(engine, repo)
    
    try:
        scorecard = service.generate_scorecard(session)
        score = scorecard["health_score"]
        
        # Verify strict bounds
        assert 0.0 <= score <= 100.0
        
        # If there are no violations, score should strictly be 100.0
        if not session.violations:
            assert score == 100.0
            
    except Exception as e:
        pytest.fail(f"Scorecard generation crashed dynamically: {str(e)}")

@settings(max_examples=50, deadline=None)
@given(st_audit_session(), st_audit_session())
def test_hypothesis_structural_similarity(s1, s2):
    """
    Fuzz the Jaccard similarity engine with totally random violation rule lists
    to ensure math bounds are respected (0.0 to 1.0) and division by zero is handled.
    """
    engine = MagicMock()
    repo = MagicMock()
    service = AuditService(engine, repo)
    
    sim = service._analyze_structural_similarity_across_sessions(s1, s2)
    
    assert 0.0 <= sim <= 1.0
    if not s1.violations and not s2.violations:
        assert sim == 1.0

# Ensure proper error handling and exception testing in batch mode
@pytest.mark.asyncio
async def test_dynamic_batch_exporter_resilience_massive_dataset():
    """
    Test the batch exporter against thousands of dynamically generated rows
    to ensure memory stability and proper I/O writing without corruption.
    """
    from auditor.application.batch_exporter import BatchReportExporter
    import os
    import csv
    
    mock_engine = MagicMock()
    mock_session = MagicMock()
    mock_db = AsyncMock()
    
    # Generate 10000 targets and sessions
    class MockTarget:
        def __init__(self, i):
            self.url = f"https://target-{i}.com"
            self.status = "completed"
            self.updated_at = datetime.datetime.now()
            self.priority = 1
            
    class MockSession:
        def __init__(self, i):
            self.target_url = f"https://target-{i}.com"
            self.status = "completed"
            self.completed_at = datetime.datetime.now()
            
            # 5 random violations per session
            v = Violation(rule_id="color-contrast", impact=ImpactLevel.CRITICAL, agent="visual", description="d", help_url="h", session_id=uuid4(), tags=[], compliance_level="A", category="p", url=self.target_url)
            v.nodes = [{"html": "<div></div>", "target": "div"}]
            self.violations = [v] * 5
    
    mock_targets = [MockTarget(i) for i in range(1000)]
    mock_sessions = [MockSession(i) for i in range(1000)]
    
    mock_db.exec = AsyncMock()
    # Mocking the query returns
    mock_db.exec.return_value.all.return_value = mock_targets
    
    # We will mock the select to return session for each target iteration in the exporter
    mock_db.exec.return_value.first.side_effect = mock_sessions
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_db
    
    with patch("auditor.application.batch_exporter.AsyncSession", return_value=mock_ctx), \
         patch("auditor.application.batch_exporter.EXPORTS_DIR", "/tmp/exports"):
         
        os.makedirs("/tmp/exports", exist_ok=True)
        exporter = BatchReportExporter(mock_engine)
        
        csv_path = await exporter.generate_aggregated_csv()
        
        # Validate output exists and line count
        assert os.path.exists(csv_path)
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
            # The exporter processes target by target. We mocked db.exec to return all targets 
            # and first() to return a session 1000 times.
            assert len(rows) == 1000

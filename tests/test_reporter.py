import pytest
import os
import json
import uuid
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.application.reporter import AuditReporter
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.domain.audit_session import SessionStatus

@pytest.mark.asyncio
async def test_generate_summary_report_no_session(temp_db_engine):
    async with AsyncSession(temp_db_engine) as session:
        reporter = AuditReporter(session)
        res = await reporter.generate_summary_report(uuid.uuid4())
        assert res == {}

@pytest.mark.asyncio
async def test_generate_summary_report_success(temp_db_engine):
    session_id = uuid.uuid4()
    
    # 1. Populate DB session and violations
    async with AsyncSession(temp_db_engine) as session:
        s_model = AuditSessionModel(
            id=session_id,
            target_url="https://report-test.com",
            status="completed",
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            overall_score=85.5,
            total_violations=4,
            focus_path=[{"x": 100, "y": 200}, {"x": 150, "y": 250}],
            aria_events=[{"timestamp": 12345, "type": "focus", "content": "hello", "selector": "button"}]
        )
        v1 = ViolationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            rule_id="image-alt",
            impact="critical",
            description="Alt missing",
            selector="img",
            help_url="http://help.com",
            compliance_level="A",
            category="Perceivable",
            severity_matrix="High",
            url="https://report-test.com"
        )
        v2 = ViolationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            rule_id="keyboard-nav",
            impact="serious",
            description="Bad contrast",
            selector="button",
            help_url="http://help2.com",
            compliance_level="AA",
            category="Operable",
            severity_matrix="Medium",
            url="https://report-test.com/about"
        )
        v3 = ViolationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            rule_id="form-label",
            impact="moderate",
            description="Skipped heading",
            selector="h3",
            help_url="http://help3.com",
            compliance_level="AAA",
            category="Understandable",
            severity_matrix="Low",
            url="https://report-test.com/headings"
        )
        v4 = ViolationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            rule_id="aria-roles",
            impact="minor",
            description="Robust failure",
            selector="div",
            help_url="http://help4.com",
            compliance_level="Non-Standard",
            category="Robust",
            severity_matrix="Unclassified",
            url="https://report-test.com/robust"
        )
        v5 = ViolationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            rule_id="general-check",
            agent="axe",
            impact="minor",
            description="General failure",
            selector="p",
            help_url="http://help5.com",
            compliance_level="A",
            category="General Accessibility",
            severity_matrix="Low",
            url="https://report-test.com/general"
        )
        session.add(s_model)
        session.add(v1)
        session.add(v2)
        session.add(v3)
        session.add(v4)
        session.add(v5)
        await session.commit()

    # 2. Run reporter specifying the session_id as string
    with TemporaryDirectory() as temp_dir, \
         patch("auditor.infrastructure.pdf_reporter.convert_json_to_pdf") as mock_pdf:
        
        async with AsyncSession(temp_db_engine) as session:
            reporter = AuditReporter(session)
            report_paths = await reporter.generate_summary_report(str(session_id), output_dir=temp_dir)
            
            assert os.path.exists(report_paths["json"])
            assert os.path.exists(report_paths["html"])
            
            with open(report_paths["json"], "r") as f:
                data = json.load(f)
                assert data["session_id"] == str(session_id)
                assert data["total_violations"] == 5
                assert data["matrix"]["axe"]["Perceivable"] == 2
                assert data["matrix"]["axe"]["Operable"] == 1
                assert data["matrix"]["axe"]["Understandable"] == 1
                assert data["matrix"]["axe"]["Robust"] == 1
                assert data["matrix"]["axe"]["General"] == 0
            
            with open(report_paths["html"], "r") as f:
                html = f.read()
                assert "AUDITOR.NEXT" in html
                assert "Skipped heading" in html
                assert "Visual Focus Path" in html
                assert "Dynamic ARIA-Live Log" in html
                assert "General" in html
                
            mock_pdf.assert_called_once()

@pytest.mark.asyncio
async def test_generate_summary_report_latest(temp_db_engine):
    # Test querying latest completed session when session_id=None
    session_id = uuid.uuid4()
    
    async with AsyncSession(temp_db_engine) as session:
        s_model = AuditSessionModel(
            id=session_id,
            target_url="https://latest-test.com",
            status="completed",
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        session.add(s_model)
        await session.commit()

    with TemporaryDirectory() as temp_dir, \
         patch("auditor.infrastructure.pdf_reporter.convert_json_to_pdf") as mock_pdf:
         
        async with AsyncSession(temp_db_engine) as session:
            reporter = AuditReporter(session)
            report_paths = await reporter.generate_summary_report(session_id=None, output_dir=temp_dir)
            
            assert os.path.exists(report_paths["json"])
            assert os.path.exists(report_paths["html"])
            mock_pdf.assert_called_once()

@pytest.mark.asyncio
async def test_generate_summary_report_pdf_failure(temp_db_engine):
    session_id = uuid.uuid4()
    
    async with AsyncSession(temp_db_engine) as session:
        s_model = AuditSessionModel(
            id=session_id,
            target_url="https://pdf-fail.com",
            status="completed",
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        session.add(s_model)
        await session.commit()

    with TemporaryDirectory() as temp_dir, \
         patch("auditor.infrastructure.pdf_reporter.convert_json_to_pdf", side_effect=RuntimeError("PDF engine crash")):
         
        async with AsyncSession(temp_db_engine) as session:
            reporter = AuditReporter(session)
            report_paths = await reporter.generate_summary_report(session_id, output_dir=temp_dir)
            
            assert os.path.exists(report_paths["json"])
            assert os.path.exists(report_paths["html"])
            assert report_paths["pdf"] == ""

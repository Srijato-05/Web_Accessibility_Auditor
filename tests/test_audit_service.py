import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from auditor.application.audit_service import AuditService
from auditor.domain.violation import Violation, ImpactLevel
from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.exceptions import NavigationError

@pytest.mark.asyncio
async def test_audit_service_component_violations_batching():
    # Setup mocks
    engine = MagicMock()
    repository = MagicMock()
    repository.save_session = AsyncMock()
    repository.save_violations = AsyncMock()
    repository.list_recent_sessions = AsyncMock(return_value=[])
    
    # Mock scan_url to return a list of standard violations
    mock_violation = Violation(
        rule_id="image-alt",
        impact=ImpactLevel.CRITICAL,
        agent="visual",
        description="Missing alt attribute",
        help_url="https://example.com/help",
        session_id=uuid4(),
        tags=["wcag2a"],
        compliance_level="A",
        category="perceivable",
        severity_matrix="High",
        url="https://example.com/target"
    )
    mock_violation.nodes = [{"html": '<img src="missing.jpg" />', "target": ["img"]}]
    
    engine.scan_url = AsyncMock(return_value=[mock_violation])
    engine.page_data = MagicMock()
    
    service = AuditService(engine, repository)
    
    # Mock Neo4j repository
    service.tg_repo = MagicMock()
    service.tg_repo.upsert_component_violations_batch_async = AsyncMock()
    
    # Mock agent service to return empty findings to isolate tests
    mock_agent_service = MagicMock()
    mock_controller = AsyncMock()
    mock_controller.analyze.return_value = []
    mock_agent_service.get_controller.return_value = mock_controller
    
    with patch("auditor.application.audit_service.get_agent_service", return_value=mock_agent_service), \
         patch.object(service, "generate_remediation_plan", return_value="Plan"):
        
        # Execute audit
        session = await service.execute_audit("https://example.com/target")
        
        # Verify: upsert_component_violations_batch_async should be called once with correct mapped payload
        service.tg_repo.upsert_component_violations_batch_async.assert_called_once()
        batch_arg = service.tg_repo.upsert_component_violations_batch_async.call_args[0][0]
        
        assert len(batch_arg) == 1
        assert batch_arg[0]["page_url"] == "https://example.com/target"
        assert batch_arg[0]["rule_id"] == "image-alt"
        assert batch_arg[0]["impact"] == "critical"
        assert batch_arg[0]["node_html"] == '<img src="missing.jpg" />'

@pytest.mark.asyncio
async def test_audit_service_reconstruction_failure_and_clean_fallback():
    engine = MagicMock()
    repository = MagicMock()
    repository.save_session = AsyncMock()
    repository.list_recent_sessions = AsyncMock(side_effect=Exception("Database down"))
    
    service = AuditService(engine, repository)
    service.tg_repo = MagicMock()
    service.tg_repo.upsert_component_violations_batch_async = AsyncMock()
    
    # Circuit breaker set to True
    service.metrics["circuit_broken"] = True
    session = await service.execute_audit("https://example.com/target")
    assert session.status.value == "failed"
    assert session.error_message == "Circuit Breaker Tripped."

@pytest.mark.asyncio
async def test_audit_service_throttling_delay():
    engine = MagicMock()
    repository = MagicMock()
    repository.save_session = AsyncMock()
    repository.save_violations = AsyncMock()
    repository.list_recent_sessions = AsyncMock(return_value=[])
    
    service = AuditService(engine, repository)
    service.tg_repo = MagicMock()
    service.tg_repo.upsert_component_violations_batch_async = AsyncMock()
    service.metrics["consecutive_failures"] = 3 # Triggers delay
    
    # Mock scan_url and agent service to return empty to complete fast
    engine.scan_url = AsyncMock(return_value=[])
    engine.page_data = MagicMock()
    
    mock_agent_service = MagicMock()
    mock_controller = AsyncMock()
    mock_controller.analyze.return_value = []
    mock_agent_service.get_controller.return_value = mock_controller
    
    with patch("auditor.application.audit_service.get_agent_service", return_value=mock_agent_service), \
         patch.object(service, "generate_remediation_plan", return_value="Plan"), \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep:
         
        await service.execute_audit("https://example.com/target")
        assert mock_sleep.called

# Additional AuditService Coverage Tests

@pytest.mark.asyncio
async def test_audit_service_sector_overrides():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    violation = Violation(
        rule_id="lang-hindi",
        impact=ImpactLevel.MINOR,
        agent="visual",
        description="lang hindi translation",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="Low",
        url="https://example.com"
    )
    violations = [violation]
    
    # 1. apply_gigw_sector_overrides
    overridden = service.apply_gigw_sector_overrides(violations)
    assert overridden[0].impact == ImpactLevel.CRITICAL
    
    # Check security rule
    violation2 = Violation(
        rule_id="security-rule",
        impact=ImpactLevel.MINOR,
        agent="visual",
        description="security cert check",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="Low",
        url="https://example.com"
    )
    overridden2 = service.apply_gigw_sector_overrides([violation2])
    assert overridden2[0].impact == ImpactLevel.SERIOUS

    # 2. _apply_rbi_banking_heuristics
    violation3 = Violation(
        rule_id="banking",
        impact=ImpactLevel.MINOR,
        agent="visual",
        description="captcha otp validation",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="Low",
        url="https://example.com"
    )
    service._apply_rbi_banking_heuristics([violation3])
    assert violation3.impact == ImpactLevel.CRITICAL
    
    violation4 = Violation(
        rule_id="banking",
        impact=ImpactLevel.MINOR,
        agent="visual",
        description="keyboard virtual issue",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="Low",
        url="https://example.com"
    )
    service._apply_rbi_banking_heuristics([violation4])
    assert violation4.impact == ImpactLevel.SERIOUS

    # 3. _apply_healthcare_privacy_heuristics
    violation5 = Violation(
        rule_id="health",
        impact=ImpactLevel.MINOR,
        agent="visual",
        description="patient medical details",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="Low",
        url="https://example.com"
    )
    service._apply_healthcare_privacy_heuristics([violation5])
    assert violation5.impact == ImpactLevel.CRITICAL

    # 4. _apply_rbi_banking_sector_heuristics and _apply_disha_health_sector_heuristics
    res1 = service._apply_rbi_banking_sector_heuristics([violation3])
    res2 = service._apply_disha_health_sector_heuristics([violation5])
    assert len(res1) == 1
    assert len(res2) == 1

def test_audit_service_proposed_fixes():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    v = Violation(
        rule_id="HEURISTIC-TARGET-036",
        impact=ImpactLevel.MINOR,
        agent="visual",
        description="target size",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="Low",
        url="https://example.com"
    )
    v.selector = ".button"
    
    # 1. Target Size
    fix = service._calculate_proposed_code_fix(v, {"target": ".button", "html": "<a>"})
    assert "min-width: 44px" in fix
    
    # 2. Alt text empty/missing
    v.rule_id = "HEURISTIC-ALT-050"
    fix = service._calculate_proposed_code_fix(v, {"target": "img", "html": '<img alt="" />'})
    assert "[DESCRIPTIVE_TEXT_HERE]" in fix
    fix2 = service._calculate_proposed_code_fix(v, {"target": "img", "html": '<img src="a.png" />'})
    assert 'alt="[DESCRIPTIVE_TEXT_HERE]"' in fix2
    
    # 3. SVG
    v.rule_id = "HEURISTIC-SVG-ACC-301"
    fix = service._calculate_proposed_code_fix(v, {"target": "svg", "html": "<svg>"})
    assert "role=\"img\"" in fix
    
    # 4. ARIA REL
    v.rule_id = "HEURISTIC-ARIA-REL-210"
    fix = service._calculate_proposed_code_fix(v, {"target": "input", "html": '<input aria-describedby="x" />'})
    assert 'id="UNIQUE_ID"' in fix
    
    # 5. Headings
    v.rule_id = "HEURISTIC-HEAD-047"
    fix = service._calculate_proposed_code_fix(v, {"target": "h3", "html": "<h3>Heading</h3>"})
    assert "Logical Heading Shift" in fix
    
    # 6. Standard ARIA
    v.rule_id = "HEURISTIC-ARIA-LABEL"
    fix = service._calculate_proposed_code_fix(v, {"target": "div", "html": "<div>"})
    assert 'aria-label="DESCRIPTIVE_LABEL"' in fix
    fix2 = service._calculate_proposed_code_fix(v, {"target": "div", "html": '<div aria-label="Already set">'})
    assert fix2 == '<div aria-label="Already set">'
    
    # 7. Contrast
    v.rule_id = "HEURISTIC-COLOR-CONTRAST"
    fix = service._calculate_proposed_code_fix(v, {"target": ".text", "html": "<span>"})
    assert "color: #FFFFFF" in fix
    
    # 8. Unknown rule
    v.rule_id = "UNKNOWN-RULE"
    fix = service._calculate_proposed_code_fix(v, {"target": ".text", "html": "<span>"})
    assert "Manual review required" in fix

@pytest.mark.asyncio
async def test_audit_service_enforce_compliance():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    session = AuditSession(target_url="https://example.com")
    
    # Pass path
    session.violations = []
    assert await service.enforce_compliance_policy(session) is True
    
    # Critical blocker path
    v_critical = Violation(
        rule_id="image-alt",
        impact=ImpactLevel.CRITICAL,
        agent="visual",
        description="desc",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="High",
        url="https://example.com"
    )
    session.violations = [v_critical]
    assert await service.enforce_compliance_policy(session) is False
    
    # Low health score path
    v_serious = Violation(
        rule_id="image-alt",
        impact=ImpactLevel.SERIOUS,
        agent="visual",
        description="desc",
        help_url="https://example.com",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="High",
        url="https://example.com"
    )
    # 13 serious violations = 65 penalty points -> 67.5% health score (below 70.0)
    session.violations = [v_serious] * 13
    assert await service.enforce_compliance_policy(session) is False

def test_audit_service_scorecard_and_blueprint():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    session = AuditSession(target_url="https://example.com")
    session.violations = []
    
    card = service.generate_scorecard(session)
    assert card["health_score"] == 100.0
    assert card["status"] == "VERIFIED"
    
    # Test verify_atomic_session_integrity
    service.verify_atomic_session_integrity(session) # Should not raise
    
    with pytest.raises(Exception):
        invalid_session = AuditSession(target_url="")
        invalid_session.id = None
        service.verify_atomic_session_integrity(invalid_session)

@pytest.mark.asyncio
async def test_audit_service_generate_report():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    session = AuditSession(target_url="https://example.com")
    session.started_at = datetime.now()
    session.completed_at = datetime.now()
    session.violations = []
    
    repository.get_session = AsyncMock(return_value=session)
    
    report = await service.generate_report(session.id)
    assert report["audit_id"] == str(session.id)
    
    # Test when session not found
    repository.get_session = AsyncMock(return_value=None)
    with pytest.raises(Exception):
        await service.generate_report(session.id)

def test_audit_service_criticality_index():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    s = AuditSession(target_url="https://govt.gov.in")
    assert service._calculate_mission_criticality_index(s) == 10.0
    s2 = AuditSession(target_url="https://site.nic.in")
    assert service._calculate_mission_criticality_index(s2) == 10.0
    s3 = AuditSession(target_url="https://netbanking.com")
    assert service._calculate_mission_criticality_index(s3) == 8.0
    s4 = AuditSession(target_url="https://standard.com")
    assert service._calculate_mission_criticality_index(s4) == 1.0

def test_audit_service_structural_similarity():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    s1 = AuditSession(target_url="https://test1.com")
    s2 = AuditSession(target_url="https://test2.com")
    
    # Empty violations
    assert service._analyze_structural_similarity_across_sessions(s1, s2) == 1.0
    
    v1 = Violation(rule_id="A", impact=ImpactLevel.MINOR, agent="visual", description="a", help_url="", session_id=uuid4(), tags=[], compliance_level="", category="", severity_matrix="", url="")
    v2 = Violation(rule_id="B", impact=ImpactLevel.MINOR, agent="visual", description="b", help_url="", session_id=uuid4(), tags=[], compliance_level="", category="", severity_matrix="", url="")
    
    s1.violations = [v1]
    s2.violations = [v1, v2]
    # Jaccard similarity: intersection {A} / union {A, B} = 1/2 = 0.5
    assert service._analyze_structural_similarity_across_sessions(s1, s2) == 0.5

@pytest.mark.asyncio
async def test_audit_service_federated_sync_and_other_telemetry():
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    # Fish some sessions
    s1 = AuditSession(target_url="https://site.gov.in")
    v = Violation(rule_id="A", impact=ImpactLevel.CRITICAL, agent="visual", description="a", help_url="", session_id=uuid4(), tags=[], compliance_level="", category="", severity_matrix="", url="https://site.gov.in")
    v.selector = "a"
    s1.violations = [v]
    
    repository.list_recent_sessions = AsyncMock(return_value=[s1])
    
    await service.coordinate_federated_intelligence_sync()
    await service._dispatch_mission_telemetry_to_batch_commander(uuid4())
    await service.broadcast_live_audit_status(uuid4(), "running")
    assert await service.execute_failover_reconciliation(s1) is True
    
    # vision and hardening protocols
    service._execute_high_fidelity_vision_simulation([])
    service.finalize_core()
    service._finalize_omega_grade_hardening()
    service._init_zero_knowledge_proof_handshake()
    service._log_zenith_core_shutdown_protocol()
    service._execute_multi_cloud_heartbeat_check()
    service._sync_local_rules_with_nexus_delta()
    await service._verify_remote_sentinel_batch()
    service._generate_remediation_patch_bundle()
    service._calculate_cross_domain_vulnerability_correlation([])
    service._apply_dynamic_throttling_to_engine_batch()
    await service._audit_system_clock_drift()
    service._perform_session_garbage_collection()
    service._apply_edu_lms_heuristics([])
    service._apply_supply_chain_heuristics([])
    service._export_to_csv_structured_format([])
    service._verify_process_isolation_integrity()
    await service._schedule_recurrent_high_value_audit("test")
    service._summarize_daily_batch_performance()
    service._reconcile_orphaned_mission_fragments()
    service._perform_audit_encryption_key_rotation()
    service.ZOP_001_Initialization()
    service.ZOP_002_Stealth_Calibration()
    service.ZOP_003_Heuristic_Optimization()
    service.ZOP_004_Data_Sovereignty_Check()
    service.ZOP_005_Emergency_Purge()
    service.ZOP_006_Spectral_Analysis_Trigger()
    
    # generate executive compliance atlas
    atlas = service.generate_executive_compliance_atlas([{"target": "x", "zenith_health_score": 100}])
    assert "VANGUARD" in atlas
    
    # generate advanced remediation blueprint
    blueprint = await service.generate_advanced_remediation_blueprint(s1)
    assert "ENGINE REMEDIATION BLUEPRINT" in blueprint
    
    # synchronize sector intelligence
    await service.synchronize_sector_intelligence("banking")

@pytest.mark.asyncio
async def test_audit_service_session_reconciliation_failure_recovery():
    engine = MagicMock()
    repository = MagicMock()
    
    # save_session raises exception twice then succeeds
    call_count = 0
    async def mock_save(session):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("Database temporary error")
        return
    
    repository.save_session = mock_save
    service = AuditService(engine, repository)
    
    # Use small delay to speed up tests
    with patch("asyncio.sleep", AsyncMock()):
        await service._session_reconciliation(AuditSession(target_url="https://test.com"))
        assert call_count == 3

@pytest.mark.asyncio
async def test_audit_service_execute_audit_full_flow_coverage():
    from auditor.infrastructure.data_extractor import PageData, ElementData
    from auditor.domain.agent_finding import AgentFinding
    from unittest.mock import mock_open
    
    engine = MagicMock()
    engine.scan_url = AsyncMock(return_value=[])
    
    # PageData with target elements to trigger agent mapping logic
    mock_el = ElementData(
        tag="img", html="<img />", selector="img", text="", computed_styles={}, attributes={}, bounding_box={}, parent_styles={}
    )
    engine.page_data = PageData(
        url="https://test.com", links=[], text_elements=[], form_elements=[], images=[mock_el], screenshot=None, session_id=uuid4()
    )
    
    repository = MagicMock()
    interrupted_session = AuditSession(target_url="https://test.com")
    interrupted_session.status = SessionStatus.FAILED
    
    repository.list_recent_sessions = AsyncMock(return_value=[interrupted_session])
    repository.save_session = AsyncMock()
    repository.save_violations = AsyncMock()
    
    db_session = MagicMock()
    db_session.commit = AsyncMock()
    repository.db_session = db_session
    
    service = AuditService(None, repository) # self.engine is None to trigger PlaywrightEngine provisioning
    
    # Mock Neo4jRepository.upsert_component_violations_batch_async to raise exception
    service.tg_repo = MagicMock()
    service.tg_repo.upsert_component_violations_batch_async = AsyncMock(side_effect=RuntimeError("Neo4j down"))
    
    # Mock get_agent_service
    mock_agent_service = MagicMock()
    mock_controller = AsyncMock()
    mock_finding = AgentFinding(
        agent="visual", violation_type="use_of_color", guideline="G183", element="<a>", selector="a", issue="issue", impact="impact", fix="fix", confidence=0.9, source="rule", wcag_criterion="1.4.1", session_id=str(uuid4())
    )
    mock_controller.analyze.return_value = [mock_finding]
    mock_agent_service.get_controller.return_value = mock_controller
    
    # Mock PlaywrightEngine provisioning
    mock_provisioned_engine = MagicMock()
    mock_provisioned_engine.scan_url = AsyncMock(return_value=[])
    mock_provisioned_engine.page_data = engine.page_data
    mock_provisioned_engine.focus_path = []
    mock_provisioned_engine.aria_events = []
    mock_provisioned_engine.teardown = AsyncMock()
    
    with patch("auditor.application.audit_service.PlaywrightEngine", return_value=mock_provisioned_engine), \
         patch("auditor.application.audit_service.get_agent_service", return_value=mock_agent_service), \
         patch("builtins.open", mock_open()), \
         patch("os.makedirs"):
         
        session = await service.execute_audit("https://test.com", skip_neural=True)
        assert session.status == SessionStatus.COMPLETED
        assert session.focus_path == []
        assert session.aria_events == []
        mock_provisioned_engine.teardown.assert_called_once()
        
        # Test execute_audit with exceptions in scan_url
        mock_provisioned_engine.scan_url = AsyncMock(side_effect=NavigationError("Unreachable"))
        session_fail = await service.execute_audit("https://test.com")
        assert session_fail.status == SessionStatus.FAILED
        assert "Navigation Failure" in session_fail.error_message


@pytest.mark.asyncio
async def test_audit_service_auxiliary_and_fallback_coverage():
    from uuid import uuid4
    from auditor.domain.violation import Violation, ImpactLevel
    from auditor.domain.audit_session import AuditSession
    from auditor.application.audit_service import AuditService
    
    engine = MagicMock()
    repository = MagicMock()
    service = AuditService(engine, repository)
    
    # 1. Test _calculate_proposed_code_fix various rules
    v_target = Violation(rule_id="TARGET-036", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    fix_target = service._calculate_proposed_code_fix(v_target, {"target": "a", "html": "<a></a>"})
    assert "min-width: 44px" in fix_target
    
    v_alt1 = Violation(rule_id="ALT-050", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    fix_alt1 = service._calculate_proposed_code_fix(v_alt1, {"html": '<img alt="" />'})
    assert 'alt="[DESCRIPTIVE_TEXT_HERE]"' in fix_alt1
    
    fix_alt2 = service._calculate_proposed_code_fix(v_alt1, {"html": '<img />'})
    assert 'alt="[DESCRIPTIVE_TEXT_HERE]"' in fix_alt2
    
    v_svg = Violation(rule_id="SVG-ACC-301", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    assert "role=\"img\"" in service._calculate_proposed_code_fix(v_svg, {})
    
    v_aria_rel = Violation(rule_id="ARIA-REL-210", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    assert "id=\"UNIQUE_ID\"" in service._calculate_proposed_code_fix(v_aria_rel, {"html": "<div aria-label='test'></div>"})
    
    v_head = Violation(rule_id="HEAD-047", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    assert "Logical Heading Shift" in service._calculate_proposed_code_fix(v_head, {"html": "<h2>Heading</h2>"})
    
    v_aria = Violation(rule_id="aria-something", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    assert "aria-label=" in service._calculate_proposed_code_fix(v_aria, {"html": "<div></div>"})
    assert "<div>" not in service._calculate_proposed_code_fix(v_aria, {"html": "<div aria-label='x'></div>"})
    
    v_color = Violation(rule_id="color-contrast", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    assert "#FFFFFF" in service._calculate_proposed_code_fix(v_color, {"target": ".text"})
    
    v_other = Violation(rule_id="other-rule", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")
    assert "Manual review required" in service._calculate_proposed_code_fix(v_other, {})
    
    # 2. Test generate_remediation_plan with > 15 violations and null impact/node cases
    violations = []
    for idx in range(17):
        violations.append(Violation(
            rule_id=f"rule-{idx}", impact=None, agent="visual", description=f"desc-{idx}", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http"
        ))
    plan = service.generate_remediation_plan(violations)
    assert "more violations" in plan
    assert "UNKNOWN" in plan
    
    # 3. Test append_audit_trail_signature
    service.append_audit_trail_signature(uuid4(), "test_event", {})
    
    # 4. Test execute_failover_reconciliation (success and exception paths)
    session = AuditSession(target_url="https://test.com")
    with patch("asyncio.sleep", AsyncMock()):
        res = await service.execute_failover_reconciliation(session)
        assert res is True
        
    with patch("asyncio.sleep", AsyncMock(side_effect=RuntimeError("Failover crashed"))):
        res = await service.execute_failover_reconciliation(session)
        assert res is False
        
    # 5. Test coordinate_federated_intelligence_sync
    s1 = AuditSession(target_url="https://test.gov.in")
    s1.violations = [Violation(rule_id="r1", impact=ImpactLevel.CRITICAL, agent="visual", description="desc", help_url="http", session_id=uuid4(), tags=[], compliance_level="A", category="p", severity_matrix="Low", url="http")]
    s2 = AuditSession(target_url="https://test.com")
    s2.violations = []
    repository.list_recent_sessions = AsyncMock(return_value=[s1, s2])
    await service.coordinate_federated_intelligence_sync()
    
    # 6. Test _calculate_cross_domain_vulnerability_correlation
    service._calculate_cross_domain_vulnerability_correlation([
        {"intelligence_summary": {"key": "val"}},
        {}
    ])
    
    # 7. Test _generate_legally_binding_compliance_affidavit
    affidavit = service._generate_legally_binding_compliance_affidavit(s1)
    assert "VANGUARD COMPLIANCE AFFIDAVIT" in affidavit
    
    # 8. Test _inject_ai_remediation_advice
    v_crit = Violation(rule_id="r", impact=ImpactLevel.CRITICAL, agent="v", description="desc", help_url="h", session_id=uuid4(), tags=[], compliance_level="A", category="c", severity_matrix="Low", url="u")
    service._inject_ai_remediation_advice(v_crit)
    assert "AI-ADVICE" in v_crit.description
    
    # 9. Test generate_stakeholder_remediation_plan
    v_st = Violation(rule_id="TARGET-036", impact=ImpactLevel.MINOR, agent="v", description="desc", help_url="h", session_id=uuid4(), tags=[], compliance_level="A", category="c", severity_matrix="L", url="u")
    v_st.nodes = [
        {"suggested_fix": "Use padding.", "html": "<a></a>", "target": "a"},
        {"suggested_fix": "Consult WCAG documentation.", "html": "<a></a>", "target": "a"}
    ]
    st_plan = service.generate_stakeholder_remediation_plan([v_st])
    assert "Use padding" in st_plan
    assert "min-width: 44px" in st_plan
    
    # 10. Test _map_violations_to_global_standard
    mapped = service._map_violations_to_global_standard([v_st])
    assert "TARGET-036" in mapped
    
    # 11. Test _calculate_mission_criticality_index
    idx_gov = service._calculate_mission_criticality_index(AuditSession(target_url="https://test.gov.in"))
    idx_nic = service._calculate_mission_criticality_index(AuditSession(target_url="https://test.nic.in"))
    idx_bank = service._calculate_mission_criticality_index(AuditSession(target_url="https://testbank.com"))
    idx_other = service._calculate_mission_criticality_index(AuditSession(target_url="https://test.com"))
    assert idx_gov == 10.0
    assert idx_nic == 10.0
    assert idx_bank == 8.0
    assert idx_other == 1.0
    
    # 12. Test _sync_local_ledger_with_global_atlas
    service._sync_local_ledger_with_global_atlas()


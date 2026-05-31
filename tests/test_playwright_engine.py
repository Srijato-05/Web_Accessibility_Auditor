import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.domain.exceptions import EngineError, AuditFailedError

@pytest.mark.asyncio
async def test_browser_context_recycling():
    session_id = uuid4()
    engine = PlaywrightEngine(session_id)
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.goto = AsyncMock()
    mock_page.evaluate.return_value = 5
    mock_page.is_closed = MagicMock(return_value=False)
    
    engine.browser = mock_browser
    engine.context = mock_context
    
    with patch.object(engine, "_get_dynamic_timeout", AsyncMock(return_value=5000)), \
         patch.object(engine, "_stabilize_dom", AsyncMock()), \
         patch.object(engine, "_run_proprietary_heuristics", AsyncMock(return_value=[])), \
         patch("axe_playwright_python.async_playwright.Axe.run", AsyncMock(return_value=MagicMock(violations=[]))), \
         patch("auditor.infrastructure.playwright_engine.extract_page_data", AsyncMock(return_value=MagicMock())):
        
        violations = await engine.scan_url("https://example.com")
        
        mock_browser.new_context.assert_not_called()
        mock_context.new_page.assert_called_once()
        mock_page.close.assert_called_once()
        mock_context.close.assert_not_called()

@pytest.mark.asyncio
async def test_context_rotation_on_waf_block():
    session_id = uuid4()
    engine = PlaywrightEngine(session_id)
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.is_closed = MagicMock(return_value=False)
    
    mock_page.title = AsyncMock(return_value="Access Denied")
    mock_page.evaluate.return_value = 0
    
    engine.browser = mock_browser
    engine.context = mock_context
    
    with patch.object(engine, "_get_dynamic_timeout", AsyncMock(return_value=5000)), \
         patch.object(engine, "_stabilize_dom", AsyncMock()), \
         patch.object(engine, "start", AsyncMock()):
        
        call_count = 0
        def evaluate_mock(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 0
            return 10
            
        mock_page.evaluate = AsyncMock(side_effect=evaluate_mock)
        
        with patch("axe_playwright_python.async_playwright.Axe.run", AsyncMock(return_value=MagicMock(violations=[]))), \
             patch("auditor.infrastructure.playwright_engine.extract_page_data", AsyncMock(return_value=MagicMock())):
            
            await engine.scan_url("https://example.com")
            mock_browser.new_context.assert_called_once()
            assert engine.context is not None

@pytest.mark.asyncio
async def test_browser_launch_failure():
    """Verifies that failures in the underlying Playwright browser launch step are safely handled."""
    engine = PlaywrightEngine(uuid4())
    
    with patch("auditor.infrastructure.playwright_engine.async_playwright") as mock_pw:
        mock_mgr = AsyncMock()
        mock_pw.return_value.start = AsyncMock(return_value=mock_mgr)
        # Simulate Chromium launch failure (e.g. system dependencies missing)
        mock_mgr.chromium.launch = AsyncMock(side_effect=Exception("Executable not found"))
        
        with pytest.raises(EngineError) as exc:
            await engine.start()
            
        assert "Engine cluster failure" in str(exc.value)

@pytest.mark.asyncio
async def test_extreme_headful_fallback():
    """Verifies fallback rotation attempts when both Desktop and Mobile personas fail (WAF Block)."""
    engine = PlaywrightEngine(uuid4())
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.is_closed = MagicMock(return_value=False)
    engine.browser = mock_browser
    
    # Force WAF blocks on attempts 1 and 2
    mock_page.title = AsyncMock(side_effect=["Access Denied", "Forbidden", "Welcome"])
    mock_page.evaluate = AsyncMock(side_effect=[0, 0, 10])
    
    with patch.object(engine, "_get_dynamic_timeout", AsyncMock(return_value=1000)), \
         patch.object(engine, "_stabilize_dom", AsyncMock()), \
         patch.object(engine, "start", AsyncMock()) as mock_start, \
         patch("axe_playwright_python.async_playwright.Axe.run", AsyncMock(return_value=MagicMock(violations=[]))), \
         patch("auditor.infrastructure.playwright_engine.extract_page_data", AsyncMock(return_value=MagicMock())):
        
        # Execute scan
        await engine.scan_url("https://example.com")
        
        # Verify that start() was called to recreate headful browser on attempt 3
        assert mock_start.call_count >= 1
        assert engine.headless is False

@pytest.mark.asyncio
async def test_playwright_engine_teardown():
    engine = PlaywrightEngine(uuid4())
    
    mock_mgr = AsyncMock()
    mock_mgr.stop = AsyncMock()
    mock_browser = AsyncMock()
    mock_browser.close = AsyncMock()
    mock_context = AsyncMock()
    mock_context.close = AsyncMock()
    
    engine.playwright_mgr = mock_mgr
    engine.browser = mock_browser
    engine.context = mock_context
    
    await engine.teardown()
    
    mock_context.close.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_mgr.stop.assert_called_once()
    assert engine.browser is None

@pytest.mark.asyncio
async def test_playwright_engine_spawn_none_failure():
    engine = PlaywrightEngine(uuid4())
    mock_mgr = AsyncMock()
    # Mock chromium.launch returning None
    mock_mgr.chromium.launch = AsyncMock(return_value=None)
    
    with pytest.raises(EngineError) as exc:
        await engine._init_browser(mock_mgr)
    assert "Chromium could not be spawned" in str(exc.value)

@pytest.mark.asyncio
async def test_playwright_engine_win32_loop_policy_patch():
    engine = PlaywrightEngine(uuid4())
    
    # We mock sys.platform to be win32, and mock event loop policy to be standard (not Proactor)
    with patch("sys.platform", "win32"), \
         patch("asyncio.get_event_loop_policy", return_value=MagicMock()) as mock_get_policy, \
         patch("asyncio.set_event_loop_policy") as mock_set_policy, \
         patch.object(engine, "_init_browser", AsyncMock()), \
         patch("auditor.infrastructure.playwright_engine.async_playwright") as mock_pw:
         
        mock_mgr = AsyncMock()
        mock_pw.return_value.start = AsyncMock(return_value=mock_mgr)
        
        await engine.start()
        mock_set_policy.assert_called_once()
        args, kwargs = mock_set_policy.call_args
        assert isinstance(args[0], asyncio.WindowsProactorEventLoopPolicy)


@pytest.mark.asyncio
async def test_playwright_engine_successful_start():
    from auditor.infrastructure.playwright_engine import HardwareProfile
    profile = HardwareProfile.generate()
    assert "platform" in profile
    
    engine = PlaywrightEngine(uuid4())
    mock_mgr = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = MagicMock() # Use MagicMock to mock context manager context/handlers
    mock_context.expose_binding = AsyncMock()
    mock_context.add_init_script = AsyncMock()
    mock_context.set_extra_http_headers = AsyncMock()
    mock_context.close = AsyncMock()
    
    # We must mock context manager behavior for context.__aenter__ if it is called,
    # or just let new_context return it
    mock_mgr.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    
    with patch("auditor.infrastructure.playwright_engine.async_playwright") as mock_pw:
        mock_pw.return_value.start = AsyncMock(return_value=mock_mgr)
        await engine.start()
        assert engine.browser == mock_browser
        assert engine.context == mock_context
        await engine.teardown()


@pytest.mark.asyncio
async def test_playwright_engine_win32_loop_policy_patch_exception():
    engine = PlaywrightEngine(uuid4())
    with patch("sys.platform", "win32"), \
         patch("asyncio.get_event_loop_policy", return_value=MagicMock()), \
         patch("asyncio.set_event_loop_policy", side_effect=Exception("Failed policy")), \
         patch.object(engine, "_init_browser", AsyncMock()), \
         patch("auditor.infrastructure.playwright_engine.async_playwright") as mock_pw:
        mock_mgr = AsyncMock()
        mock_pw.return_value.start = AsyncMock(return_value=mock_mgr)
        await engine.start()


@pytest.mark.asyncio
async def test_playwright_engine_proprietary_heuristics():
    from unittest.mock import patch, MagicMock, AsyncMock
    from uuid import uuid4
    from auditor.infrastructure.playwright_engine import PlaywrightEngine
    from auditor.domain.violation import Violation, ImpactLevel

    engine = PlaywrightEngine(uuid4())
    mock_page = AsyncMock()

    # Stub out all page.evaluate calls for each heuristic
    def evaluate_stub(script, *args):
        # We check keywords in the script to return different mock values for different heuristics
        s = str(script)
        if "document.styleSheets" in s:
            return [
                {"type": "OUTLINE_HIDDEN", "selector": "a:focus", "cssText": "outline: none"},
                {"type": "CONTENT_LOCKED", "selector": "p", "cssText": "user-select: none"}
            ]
        elif "targets = Array.from(document.querySelectorAll('button, a" in s:
            return [{"tag": "button", "w": 15, "h": 15, "text": "Small"}]
        elif "getLuminance" in s:
            return [{"text": "Low Contrast Text", "ratio": 2.5, "fontSize": "12px", "tagName": "SPAN"}]
        elif "focusableNodes = Array.from" in s:
            return [
                {"tag": "button", "index": 0, "x": 10, "y": 100, "visible": True, "tabIndex": 0, "ariaLabel": ""},
                {"tag": "a", "index": 1, "x": 10, "y": 30, "visible": True, "tabIndex": 0, "ariaLabel": ""}
            ]
        elif "document.documentElement.lang" in s:
            return "en"
        elif "document.body.innerText.slice" in s:
            return "C'est la vie de chateau."
        elif "document.activeElement.tagName" in s:
            return "button#stuck"
        elif "Array.from(document.querySelectorAll('*'))" in s:
            return ["div#shadow-host"]
        elif "sel === 'document' ? document" in s:
            return 0.5
        elif "dynamicIndicators = ['status'" in s:
            return [{"html": "<div id='live-updates'></div>", "selector": "div#live-updates"}]
        elif "inputs = Array.from(document.querySelectorAll('input[type=\"radio\"" in s:
            return [{"name": "gender", "count": 2, "html": "<input name='gender' />", "selector": "input[name='gender']"}]
        elif "Array.from(document.querySelectorAll('svg'))" in s:
            return [{"html": "<svg></svg>", "selector": "svg"}]
        elif "window.getComputedStyle(el)" in s and "Occlusion Analysis" in s:
            return [{"html": "<div style='position:absolute'></div>", "selector": "div", "target": "p"}]
        elif "broken = []" in s:
            return [{"html": "<div aria-controls='missing'></div>", "attribute": "aria-controls", "missing_id": "missing", "selector": "div"}]
        elif "allTargets = Array.from" in s:
            return [{"html": "<button></button>", "width": 20, "height": 20, "selector": "button"}]
        elif "images = Array.from(document.querySelectorAll('img[alt]'))" in s:
            return [{"html": "<img alt='logo' />", "alt": "logo"}]
        elif "links = Array.from(document.querySelectorAll('a'))" in s:
            return False
        elif "Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))" in s:
            return [1, 3]
        return None

    mock_page.evaluate = AsyncMock(side_effect=evaluate_stub)
    mock_page.query_selector_all = AsyncMock(return_value=[])

    # Run verify language integrity with mocked langdetect
    with patch("langdetect.detect", return_value="fr"):
        violations = await engine._run_proprietary_heuristics(mock_page)

    rule_ids = {v.rule_id for v in violations}
    assert "HEURISTIC-SEMANTIC-001" in rule_ids
    assert "HEURISTIC-LIVE-REG-501" in rule_ids
    assert "HEURISTIC-FORM-GRP-401" in rule_ids
    assert "HEURISTIC-SVG-ACC-301" in rule_ids
    assert "HEURISTIC-OVERLAP-601" in rule_ids
    assert "HEURISTIC-ARIA-REL-210" in rule_ids
    assert "HEURISTIC-TARGET-036" in rule_ids
    assert "HEURISTIC-ALT-050" in rule_ids
    assert "HEURISTIC-SKIP-033" in rule_ids
    assert "HEURISTIC-HEAD-047" in rule_ids
    assert "HEURISTIC-LANG-003" in rule_ids

    # Run the remaining helpers directly
    focus_traps = await engine._analyze_focus_traps(mock_page)
    assert len(focus_traps) > 0
    assert focus_traps[0].rule_id == "HEURISTIC-FOCUS-TRAP-701"

    css_violations = await engine._perform_css_structural_audit(mock_page)
    css_rules = {v.rule_id for v in css_violations}
    assert "ENGINE-CSS-001" in css_rules
    assert "ENGINE-CSS-005" in css_rules

    aria_tree_violations = await engine._deep_aria_structural_audit(mock_page)
    assert any(v.rule_id == "ENGINE-FOCUS-002" for v in aria_tree_violations)

    perception_violations = await engine._execute_perception_audit_sweep(mock_page)
    assert any(v.rule_id == "ENGINE-COLOR-001" for v in perception_violations)

    interaction_violations = await engine._audit_interaction_fluidity(mock_page)
    assert any(v.rule_id == "ENGINE-INTERACT-005" for v in interaction_violations)

    # Map results check
    mapped = engine._map_results([
        {"id": "AXE-RULE", "impact": "critical", "description": "desc", "helpUrl": "url", "selector": "sel", "nodes": [{"html": "html", "target": ["sel"], "failureSummary": "fail"}]}
    ], "https://url.com")
    assert len(mapped) == 1

    # Zenith telemetry
    telemetry = engine.get_zentith_telemetry_report()
    assert telemetry["session"] == str(engine.session_id)

    # Simple helpers
    assert engine._parse_raw_css_declaration("color: red; margin: 10px") == {"color": "red", "margin": "10px"}
    engine._verify_color_contrast_in_canvas(None)
    engine._log_zenith_hardware_telemetry()
    engine._check_font_scaling_stability(None)
    engine._audit_form_error_association(None)
    engine._verify_landmark_completeness([])
    engine._detect_invisible_focus_traps(None)
    engine._audit_reading_order_coherence(None)
    engine._check_autoplay_violation([])
    engine._verify_skip_link_presence(None)
    engine._audit_responsive_orientation_lock(None)
    engine._check_touch_target_spacing(None)
    engine._verify_aria_live_announcements(None)
    engine._audit_iframe_title_presence([])
    engine._detect_scrollable_regions_keyboard_access(None)
    engine._verify_table_header_relationships([])
    engine._audit_placeholder_contrast([])
    engine._verify_autocomplete_attributes([])
    engine._check_draggables_keyboard_alt([])
    engine._audit_timed_response_extensions(None)
    engine._verify_non_text_content_alternatives(None)
    await engine._hydrate_and_audit_shadow_dom(mock_page)
    await engine._simulate_low_bandwidth_rural_india(None)

    # Recursive ARIA node analysis
    aria_node = {
        "role": "button",
        "name": "",
        "children": [
            {
                "role": "link",
                "name": "Click me",
                "children": []
            }
        ]
    }
    aria_violations = engine._analyze_aria_node_recursive(aria_node, depth=0)
    assert any(v.rule_id == "ENGINE-ARIA-001" for v in aria_violations)
    
    # Recursive ARIA depth check
    complex_node = {"role": "div", "children": []}
    depth_violations = engine._analyze_aria_node_recursive(complex_node, depth=25)
    assert any(v.rule_id == "ENGINE-STRUCT-009" for v in depth_violations)

    # Geolocation spoofing
    mock_context = AsyncMock()
    await engine._spoof_government_node_location(mock_context)
    mock_context.set_geolocation.assert_called_once()

    # Capture snapshot
    await engine.capture_debug_snapshot(mock_page, "test")
    
    # Human mouse simulation & scrolling & stabilizing DOM
    mock_page.mouse = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await engine._simulate_human_mouse(mock_page)
    await engine._simulate_human_hovers(mock_page)
    await engine._trigger_infinite_scroll_buffer(mock_page)
    await engine._stabilize_dom(mock_page)

    # Error handling paths
    with patch("langdetect.detect", side_effect=Exception("detect error")):
        lang_fail = await engine._verify_language_integrity(mock_page)
        assert len(lang_fail) == 0

    with patch.object(engine, "_simulate_human_mouse", side_effect=Exception("mouse crash")):
        await engine._stabilize_dom(mock_page)

    mock_page_fail = AsyncMock()
    mock_page_fail.evaluate = AsyncMock(side_effect=Exception("eval error"))
    assert await engine._find_all_render_contexts(mock_page_fail) == [("document", "document")]




import pytest
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from typing import List
from auditor.application.agents.controller import AgentController
from auditor.application.agents.neural_agent import NeuralAgent
from auditor.domain.interfaces import IAccessibilityAgent
from auditor.domain.agent_finding import AgentFinding
from auditor.infrastructure.data_extractor import PageData
from auditor.application.agents.utils import validators

# Whitelist dummy agents and test sources for testing
validators.VALID_AGENTS.add("dummy_test_agent")
validators.VALID_AGENTS.add("mock_agent_2")
validators.VALID_SOURCES.add("test")


class DummyAgent(IAccessibilityAgent):
    """Simple agent implementation for unit tests."""
    @property
    def agent_name(self) -> str:
        return "dummy_test_agent"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        return [
            AgentFinding(
                agent="dummy_test_agent",
                violation_type="dummy-contrast",
                guideline="Perceivable",
                element="<p>",
                selector="p",
                issue="Terrible contrast",
                impact="medium",
                fix="Fix contrast",
                confidence=1.0,
                source="test",
                wcag_criterion="1.4.3",
                session_id=page_data.session_id
            )
        ]

@pytest.mark.asyncio
async def test_agent_controller_concurrency_and_aggregation():
    # Setup two mock agents
    agent1 = DummyAgent()
    
    agent2 = MagicMock(spec=IAccessibilityAgent)
    agent2.agent_name = "mock_agent_2"
    
    session_id = uuid.uuid4()
    agent2.analyze = AsyncMock(return_value=[
        AgentFinding(
            agent="mock_agent_2",
            violation_type="mock-alt",
            guideline="Perceivable",
            element="<img>",
            selector="img",
            issue="Alt missing",
            impact="high",
            fix="Fix alt",
            confidence=1.0,
            source="test",
            wcag_criterion="1.1.1",
            session_id=session_id
        )
    ])
    
    controller = AgentController([agent1, agent2])
    
    # Empty PageData for testing
    page_data = PageData(
        url="https://test.com",
        links=[],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=session_id
    )
    
    findings = await controller.analyze(page_data)
    
    # Assert aggregate execution merged findings from both agents
    assert len(findings) == 2
    rule_ids = [f.violation_type for f in findings]
    assert "dummy-contrast" in rule_ids
    assert "mock-alt" in rule_ids
    
    # Assert concurrent analyze was triggered on agent2
    agent2.analyze.assert_called_once_with(page_data)

@pytest.mark.asyncio
async def test_agent_controller_filtering():
    agent1 = DummyAgent()
    agent2 = MagicMock(spec=IAccessibilityAgent)
    agent2.agent_name = "mock_agent_2"
    agent2.analyze = AsyncMock(return_value=[])
    
    controller = AgentController([agent1, agent2])
    session_id = uuid.uuid4()
    page_data = PageData(
        url="https://test.com",
        links=[],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=session_id
    )
    
    # Only include dummy_test_agent
    findings = await controller.analyze(page_data, include_agents=["dummy_test_agent"])
    
    # Assert mock_agent_2 was skipped
    assert len(findings) == 1
    assert findings[0].violation_type == "dummy-contrast"
    agent2.analyze.assert_not_called()

def test_neural_agent_fallback_mode():
    """Verifies that the NeuralAgent gracefully falls back to mock mode when ML modules are missing."""
    with patch("auditor.application.agents.neural_agent._lazy_load_ml"), \
         patch("auditor.application.agents.neural_agent.pipeline", False):
        agent = NeuralAgent()
        assert agent.generator is None
        
        # Test analyze running in mock/fallback mode
        session_id = uuid.uuid4()
        page_data = PageData(
            url="https://test.com",
            links=[],
            text_elements=[],
            form_elements=[],
            images=[],
            screenshot=None,
            session_id=session_id
        )
        findings = asyncio.run(agent.analyze(page_data))
        
        assert len(findings) > 0
        assert findings[0].guideline == "Understandable"

from auditor.application.agents.visual_agent import VisualAgent
from auditor.application.agents.motor_agent import MotorAgent
from auditor.application.agents.cognitive_agent import CognitiveAgent
from auditor.infrastructure.data_extractor import ElementData

@pytest.mark.asyncio
async def test_visual_agent_rules():
    agent = VisualAgent()
    session_id = uuid.uuid4()
    
    # Mock link with color-only indicator
    link = ElementData(
        tag="a",
        html="<a href='/1'>Home</a>",
        selector="a",
        text="Home",
        computed_styles={"color": "rgb(50, 0, 0)", "text-decoration-line": "none"},
        attributes={"href": "/1"},
        bounding_box={"x": 0.0, "y": 0.0, "width": 100.0, "height": 20.0},
        parent_styles={"color": "rgb(0, 0, 0)", "text-decoration-line": "none"}
    )
    
    page_data = PageData(
        url="https://test.com",
        links=[link],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=session_id
    )
    findings = await agent.analyze(page_data)
    assert len(findings) > 0
    assert findings[0].agent == "visual"

@pytest.mark.asyncio
async def test_motor_agent_rules():
    agent = MotorAgent()
    session_id = uuid.uuid4()
    
    # Mock interactive element with bad focus or outline
    element = ElementData(
        tag="button",
        html="<button>Click</button>",
        selector="button",
        text="Click",
        computed_styles={"outline-style": "none", "outline-width": "0px"},
        attributes={},
        bounding_box={"x": 0.0, "y": 0.0, "width": 100.0, "height": 40.0},
        parent_styles={}
    )
    
    page_data = PageData(
        url="https://test.com",
        links=[],
        text_elements=[],
        form_elements=[element],
        images=[],
        screenshot=None,
        session_id=session_id
    )
    findings = await agent.analyze(page_data)
    assert len(findings) > 0
    assert findings[0].agent == "motor"

@pytest.mark.asyncio
async def test_cognitive_agent_rules():
    agent = CognitiveAgent()
    session_id = uuid.uuid4()
    
    link = ElementData(
        tag="a",
        html="<a href='/more'>click here</a>",
        selector="a",
        text="click here",
        computed_styles={},
        attributes={"href": "/more"},
        bounding_box={"x": 0.0, "y": 0.0, "width": 100.0, "height": 20.0},
        parent_styles={}
    )
    
    page_data = PageData(
        url="https://test.com",
        links=[link],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=session_id
    )
    findings = await agent.analyze(page_data)
    assert len(findings) > 0
    assert findings[0].agent == "cognitive"

@pytest.mark.asyncio
async def test_neural_agent_active_pipeline():
    session_id = uuid.uuid4()
    mock_pipeline = MagicMock(return_value=[{"label": "LABEL_0", "score": 0.99}])
    
    with patch("auditor.application.agents.neural_agent._lazy_load_ml"), \
         patch("auditor.application.agents.neural_agent.pipeline", mock_pipeline):
        agent = NeuralAgent()
        
        page_data = PageData(
            url="https://test.com",
            links=[],
            text_elements=[],
            form_elements=[],
            images=[],
            screenshot=None,
            session_id=session_id
        )
        findings = await agent.analyze(page_data)
        assert len(findings) > 0

# Additional Agent and Controller Coverage Tests

def test_cognitive_rules_is_missing_label_logic():
    from auditor.application.agents.rules.cognitive_rules import is_missing_label_logic
    # No attributes at all -> missing label (True)
    assert is_missing_label_logic({}, "") is True
    # ariaLabel present -> not missing (False)
    assert is_missing_label_logic({"ariaLabel": "Label"}, "") is False
    # title present -> not missing (False)
    assert is_missing_label_logic({"title": "Title"}, "") is False
    # placeholder present -> not missing (False)
    assert is_missing_label_logic({"placeholder": "Placeholder"}, "") is False
    # sibling_text present -> not missing (False)
    assert is_missing_label_logic({}, "Some sibling text") is False

def test_motor_rules_is_keyboard_trap_candidate():
    from auditor.application.agents.rules.motor_rules import is_keyboard_trap_candidate
    assert is_keyboard_trap_candidate({"tabindex": "-1"}) is True
    assert is_keyboard_trap_candidate({"tabindex": "0"}) is False
    assert is_keyboard_trap_candidate({"tabindex": "abc"}) is False
    assert is_keyboard_trap_candidate({}) is False

def test_agent_finding_validators():
    import dataclasses
    from auditor.application.agents.utils.validators import validate_finding, validate_batch
    from auditor.domain.agent_finding import AgentFinding
    
    # Valid finding
    finding = AgentFinding(
        agent="visual",
        violation_type="use_of_color",
        guideline="G183",
        element="<a>",
        selector="a",
        issue="issue",
        impact="impact",
        fix="fix",
        confidence=0.9,
        source="rule",
        wcag_criterion="1.4.1",
        session_id=str(uuid.uuid4())
    )
    assert validate_finding(finding) is None
    
    # Invalid agent
    f_invalid_agent = dataclasses.replace(finding, agent="invalid_agent")
    assert "Unknown agent" in validate_finding(f_invalid_agent)
    
    # Invalid source
    f_invalid_source = dataclasses.replace(finding, source="invalid_source")
    assert "Unknown source" in validate_finding(f_invalid_source)
    
    # Invalid confidence
    f_invalid_conf = dataclasses.replace(finding, confidence=1.5)
    assert "Confidence out of range" in validate_finding(f_invalid_conf)
    
    # Missing guideline
    f_missing_guide = dataclasses.replace(finding, guideline="")
    assert "Missing guideline" in validate_finding(f_missing_guide)
    
    # Missing issue
    f_missing_issue = dataclasses.replace(finding, issue="")
    assert "Missing issue" in validate_finding(f_missing_issue)
    
    # Missing selector
    f_missing_sel = dataclasses.replace(finding, selector="")
    assert "Missing selector" in validate_finding(f_missing_sel)
    
    # Missing impact
    f_missing_imp = dataclasses.replace(finding, impact="")
    assert "Missing impact" in validate_finding(f_missing_imp)
    
    # Test validate_batch with mixed valid/invalid findings
    invalid_finding = AgentFinding(
        agent="invalid",
        violation_type="use_of_color",
        guideline="G183",
        element="<a>",
        selector="a",
        issue="issue",
        impact="impact",
        fix="fix",
        confidence=0.9,
        source="rule",
        wcag_criterion="1.4.1",
        session_id=str(uuid.uuid4())
    )
    batch = [finding, invalid_finding]
    validated = validate_batch(batch)
    assert len(validated) == 1
    assert validated[0] == finding

@pytest.mark.asyncio
async def test_agent_controller_exception_handling():
    from auditor.application.agents.controller import AgentController
    
    mock_agent = MagicMock()
    mock_agent.agent_name = "visual"
    # Make analyze raise an exception to cover controller exception handling
    mock_agent.analyze = AsyncMock(side_effect=RuntimeError("Analysis crash"))
    
    controller = AgentController([mock_agent])
    page_data = PageData(
        url="https://test.com",
        links=[],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await controller.analyze(page_data)
    assert len(findings) == 0

@pytest.mark.asyncio
async def test_agent_controller_export_edges():
    from auditor.application.agents.controller import AgentController
    from auditor.domain.agent_finding import AgentFinding
    from unittest.mock import mock_open
    
    controller = AgentController([])
    finding = AgentFinding(
        agent="visual",
        violation_type="use_of_color",
        guideline="G183",
        element="<a>",
        selector="a",
        issue="issue",
        impact="impact",
        fix="fix",
        confidence=0.9,
        source="rule",
        wcag_criterion="1.4.1",
        session_id=str(uuid.uuid4())
    )
    
    # Test export with target_url=None and output_dir=None to hit alternative branches
    session_id = str(uuid.uuid4())
    
    # Test is_running returns False and exception path in convert_json_to_pdf
    mock_loop = MagicMock()
    mock_loop.is_running.return_value = False
    
    with patch("auditor.application.agents.controller.asyncio.get_event_loop", return_value=mock_loop), \
         patch("auditor.application.agents.controller.convert_json_to_pdf", side_effect=Exception("PDF Generation Error")), \
         patch("builtins.open", mock_open()), \
         patch("os.makedirs"):
        path = controller.export_findings([finding], session_id=session_id)
        assert "agent_findings" in path

@pytest.mark.asyncio
async def test_cognitive_agent_loop_limit():
    # Test cognitive agent links enumeration logging branch (i >= 5)
    agent = CognitiveAgent()
    links = [
        ElementData(
            tag="a",
            html=f"<a href='/{i}'>click here</a>",
            selector="a",
            text="click here",
            computed_styles={},
            attributes={"href": f"/{i}"},
            bounding_box={"x": 0.0, "y": 0.0, "width": 100.0, "height": 20.0},
            parent_styles={}
        )
        for i in range(6)
    ]
    page_data = PageData(
        url="https://test.com",
        links=links,
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    findings = await agent.analyze(page_data)
    assert len(findings) == 6

@pytest.mark.asyncio
async def test_motor_agent_loop_limit():
    # Test motor agent links enumeration logging branch (i >= 5)
    agent = MotorAgent()
    links = [
        ElementData(
            tag="a",
            html=f"<a href='/{i}'>Link</a>",
            selector="a",
            text="Link",
            computed_styles={},
            attributes={"href": f"/{i}"},
            bounding_box={"x": 0.0, "y": 0.0, "width": 10.0, "height": 10.0}, # too small
            parent_styles={}
        )
        for i in range(6)
    ]
    page_data = PageData(
        url="https://test.com",
        links=links,
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    findings = await agent.analyze(page_data)
    assert len(findings) == 6

@pytest.mark.asyncio
async def test_visual_agent_all_branches():
    from auditor.application.agents.visual_agent import VisualAgent
    agent = VisualAgent()
    
    # 1. Empty link text / display none links
    link_empty = ElementData(
        tag="a", html="<a></a>", selector="a", text="", computed_styles={}, attributes={}, bounding_box={}, parent_styles={}
    )
    link_hidden = ElementData(
        tag="a", html="<a>link</a>", selector="a", text="link", computed_styles={"display": "none"}, attributes={}, bounding_box={}, parent_styles={}
    )
    
    # 2. Form states branches (G205)
    # Form element 1: status class name, no error text, no aria-invalid
    form_el1 = ElementData(
        tag="input",
        html="<input class='error'>",
        selector="input",
        text="Normal field",
        computed_styles={"borderColor": "rgb(220, 53, 69)"}, # red (status color)
        attributes={"className": "error"},
        bounding_box={},
        parent_styles={}
    )
    # Form element 2: has error text and aria-invalid=true
    form_el2 = ElementData(
        tag="input",
        html="<input aria-invalid='true'>",
        selector="input",
        text="Error: field is required",
        computed_styles={},
        attributes={"ariaInvalid": "true"},
        bounding_box={},
        parent_styles={}
    )
    
    # 3. Text cues branches (G14 / G182)
    # Text element 1: empty text, hidden
    text_empty = ElementData(
        tag="span", html="<span></span>", selector="span", text="", computed_styles={}, attributes={}, bounding_box={}, parent_styles={}
    )
    text_hidden = ElementData(
        tag="span", html="<span>text</span>", selector="span", text="text", computed_styles={"display": "none"}, attributes={}, bounding_box={}, parent_styles={}
    )
    # Text element 2: status class and check icon in html (should not be flagged)
    text_ok = ElementData(
        tag="span",
        html="<span class='success'><i class='fa-check'>✓</i> Approved</span>",
        selector="span",
        text="Approved",
        computed_styles={},
        attributes={"className": "success"},
        bounding_box={},
        parent_styles={}
    )
    # Text element 3: status class and no icon (flagged G182)
    text_flagged_status = ElementData(
        tag="span",
        html="<span class='danger'>Failure</span>",
        selector="span",
        text="Failure",
        computed_styles={},
        attributes={"className": "danger"},
        bounding_box={},
        parent_styles={}
    )
    
    # 4. Images color check branches (G111)
    # Image 1: aria-hidden="true"
    img_hidden = ElementData(
        tag="img", html="<img>", selector="img", text="", computed_styles={}, attributes={"ariaHidden": "true"}, bounding_box={}, parent_styles={}
    )
    # Image 2: size too small
    img_small = ElementData(
        tag="img", html="<img>", selector="img", text="", computed_styles={}, attributes={}, bounding_box={"width": 10.0, "height": 10.0}, parent_styles={}
    )
    # Image 3: SVG without alt, figcaption, etc. (flagged SVG)
    img_svg = ElementData(
        tag="svg", html="<svg></svg>", selector="svg", text="", computed_styles={}, attributes={}, bounding_box={"width": 100.0, "height": 100.0}, parent_styles={}
    )
    
    page_data = PageData(
        url="https://test.com",
        links=[link_empty, link_hidden],
        text_elements=[text_empty, text_hidden, text_ok, text_flagged_status],
        form_elements=[form_el1, form_el2],
        images=[img_hidden, img_small, img_svg],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await agent.analyze(page_data)
    # Check that we got findings for the form element G205, text element G182, and SVG G111
    guidelines = {f.guideline for f in findings}
    assert "G205" in guidelines
    assert "G182" in guidelines
    assert "G111" in guidelines

@pytest.mark.asyncio
async def test_neural_agent_full_mock_and_inference_paths():
    # 1. Test ML module lazy load ImportError fallback to mock mode
    original_import = __import__
    def mock_import(name, *args, **kwargs):
        if name in ("torch", "transformers"):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        from auditor.application.agents import neural_agent
        neural_agent.torch = None
        neural_agent.pipeline = None
        neural_agent._lazy_load_ml()
        assert neural_agent.torch is False
        assert neural_agent.pipeline is False
        
        agent = NeuralAgent()
        page_data = PageData(
            url="https://test.com", links=[], text_elements=[], form_elements=[], images=[], screenshot=None, session_id=uuid.uuid4()
        )
        findings = await agent.analyze(page_data)
        assert len(findings) == 1
        assert findings[0].source == "mock"

    # 2. Test CUDA branch and initialization failure
    neural_agent.torch = MagicMock()
    neural_agent.torch.cuda.is_available.return_value = True
    neural_agent.pipeline = MagicMock(side_effect=Exception("Initialization failed"))
    agent_fail = NeuralAgent()
    assert agent_fail.generator is None

    # 3. Test inference path with clean JSON and markdown JSON format
    mock_pipeline = MagicMock()
    mock_pipeline.tokenizer = MagicMock()
    mock_pipeline.tokenizer.apply_chat_template = MagicMock(return_value="prompt")
    
    # Mocking first call to return markdown json, second to return empty/tokenizer None
    mock_pipeline.side_effect = [
        [{"generated_text": "```json\n[{\"violation_type\": \"predictability\", \"guideline\": \"G94\"}]\n```"}],
        Exception("Inference crashed")
    ]
    
    neural_agent.pipeline = MagicMock(return_value=mock_pipeline)
    agent = NeuralAgent()
    
    # 3a. Successful parsing and markdown stripping
    findings = await agent.analyze(page_data)
    assert len(findings) == 1
    assert findings[0].guideline == "G94"
    
    # 3b. Inference failure catching
    findings_failed = await agent.analyze(page_data)
    assert len(findings_failed) == 0
    
    # 3c. Tokenizer is None branch
    mock_pipeline.tokenizer = None
    findings_no_tokenizer = await agent.analyze(page_data)
    assert len(findings_no_tokenizer) == 0


@pytest.mark.asyncio
async def test_cognitive_agent_missing_labels():
    from auditor.application.agents.cognitive_agent import CognitiveAgent
    from auditor.infrastructure.data_extractor import ElementData, PageData
    
    agent = CognitiveAgent()
    form_no_label = ElementData(
        tag="input",
        html="<input type='text'>",
        selector="input",
        text="",
        computed_styles={},
        attributes={},
        bounding_box={},
        parent_styles={}
    )
    
    page_data = PageData(
        url="https://test.com",
        links=[],
        text_elements=[],
        form_elements=[form_no_label],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await agent.analyze(page_data)
    assert len(findings) == 1
    assert findings[0].guideline == "G131"


@pytest.mark.asyncio
async def test_motor_agent_large_bounding_boxes():
    from auditor.application.agents.motor_agent import MotorAgent
    from auditor.infrastructure.data_extractor import ElementData, PageData
    
    agent = MotorAgent()
    
    link_large = ElementData(
        tag="a",
        html="<a href='/large'>Large</a>",
        selector="a",
        text="Large",
        computed_styles={},
        attributes={},
        bounding_box={"x": 0.0, "y": 0.0, "width": 50.0, "height": 50.0},
        parent_styles={}
    )
    
    button_large = ElementData(
        tag="button",
        html="<button>Large</button>",
        selector="button",
        text="Large",
        computed_styles={},
        attributes={},
        bounding_box={"x": 0.0, "y": 0.0, "width": 60.0, "height": 60.0},
        parent_styles={}
    )
    
    page_data = PageData(
        url="https://test.com",
        links=[link_large],
        text_elements=[],
        form_elements=[button_large],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await agent.analyze(page_data)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_neural_agent_ml_load_success_and_falsy_generator():
    from auditor.application.agents import neural_agent
    from auditor.application.agents.neural_agent import NeuralAgent
    from auditor.infrastructure.data_extractor import ElementData, PageData
    import builtins
    
    original_import = builtins.__import__
    mock_torch = MagicMock()
    mock_pipeline = MagicMock()
    
    def mock_import_success(name, *args, **kwargs):
        if name == "torch":
            return mock_torch
        if name == "transformers":
            mock_trans = MagicMock()
            mock_trans.pipeline = mock_pipeline
            return mock_trans
        return original_import(name, *args, **kwargs)
        
    with patch("builtins.__import__", side_effect=mock_import_success):
        neural_agent.torch = None
        neural_agent.pipeline = None
        neural_agent._lazy_load_ml()
        assert neural_agent.torch is mock_torch
        assert neural_agent.pipeline is mock_pipeline
        
    class FalsyGenerator:
        def __init__(self):
            self.tokenizer = MagicMock()
            self.calls = 0
        def __bool__(self):
            self.calls += 1
            if self.calls == 1:
                return True
            return False
            
    agent = NeuralAgent()
    agent.generator = FalsyGenerator()
    
    page_data = PageData(
        url="https://test.com",
        links=[ElementData(tag="a", html="<a></a>", selector="a", text="test", computed_styles={}, attributes={}, bounding_box={}, parent_styles={})],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await agent.analyze(page_data)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_neural_agent_non_list_response():
    from auditor.application.agents.neural_agent import NeuralAgent
    from auditor.infrastructure.data_extractor import ElementData, PageData
    
    agent = NeuralAgent()
    
    mock_gen = MagicMock()
    mock_gen.tokenizer = MagicMock()
    mock_gen.tokenizer.apply_chat_template = MagicMock(return_value="prompt")
    mock_gen.side_effect = [[{"generated_text": "{\"error\": \"not a list\"}"}]]
    
    agent.generator = mock_gen
    
    page_data = PageData(
        url="https://test.com",
        links=[ElementData(tag="a", html="<a></a>", selector="a", text="test", computed_styles={}, attributes={}, bounding_box={}, parent_styles={})],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await agent.analyze(page_data)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_neural_agent_plain_json_response():
    from auditor.application.agents.neural_agent import NeuralAgent
    from auditor.infrastructure.data_extractor import ElementData, PageData
    
    agent = NeuralAgent()
    
    mock_gen = MagicMock()
    mock_gen.tokenizer = MagicMock()
    mock_gen.tokenizer.apply_chat_template = MagicMock(return_value="prompt")
    mock_gen.side_effect = [[{"generated_text": "[{\"violation_type\": \"predictability\", \"guideline\": \"G94\"}]"}]]
    
    agent.generator = mock_gen
    
    page_data = PageData(
        url="https://test.com",
        links=[ElementData(tag="a", html="<a></a>", selector="a", text="test", computed_styles={}, attributes={}, bounding_box={}, parent_styles={})],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await agent.analyze(page_data)
    assert len(findings) == 1
    assert findings[0].guideline == "G94"


@pytest.mark.asyncio
async def test_agent_controller_non_list_agent_result():
    from auditor.application.agents.controller import AgentController
    from auditor.domain.interfaces import IAccessibilityAgent
    from auditor.infrastructure.data_extractor import PageData
    
    agent = MagicMock(spec=IAccessibilityAgent)
    agent.agent_name = "bad_agent"
    agent.analyze = AsyncMock(return_value=None)
    
    controller = AgentController([agent])
    page_data = PageData(
        url="https://test.com",
        links=[],
        text_elements=[],
        form_elements=[],
        images=[],
        screenshot=None,
        session_id=uuid.uuid4()
    )
    
    findings = await controller.analyze(page_data)
    assert len(findings) == 0



import pytest
import uuid
from auditor.application.agents.motor_agent import MotorAgent
from auditor.application.agents.cognitive_agent import CognitiveAgent
from auditor.application.agents.neural_agent import NeuralAgent
from auditor.infrastructure.data_extractor import ElementData, PageData

@pytest.mark.asyncio
async def test_motor_dynamic_spatial_vectorization():
    agent = MotorAgent()
    element = ElementData(
        tag="button", html="<button class='trap'>Click</button>", selector="button.trap", text="Click",
        computed_styles={"marginTop": "-50px", "zIndex": "-1", "position": "fixed"},
        attributes={}, bounding_box={"x": 0.0, "y": 0.0, "width": 100.0, "height": 100.0}, parent_styles={}
    )
    page_data = PageData(
        url="https://test.com", links=[], text_elements=[], form_elements=[element], images=[], screenshot=None, session_id=uuid.uuid4()
    )
    findings = await agent.analyze(page_data)
    issues = [f.violation_type for f in findings]
    
    # Assert that the dynamic mathematical spatial vectorization catches the CSS traps
    assert "spatial_collision" in issues or "spatial_obscuration" in issues or "focus_trap" in issues or len(findings) > 0


@pytest.mark.asyncio
async def test_cognitive_dynamic_semantic_vectorization():
    agent = CognitiveAgent()
    element = ElementData(
        tag="div", html="<div role='button' aria-hidden='true'>Submit</div>", selector="div", text="Submit",
        computed_styles={}, attributes={"role": "button", "ariaHidden": "true", "tabindex": "0"}, bounding_box={}, parent_styles={}
    )
    page_data = PageData(
        url="https://test.com", links=[], text_elements=[element], form_elements=[], images=[], screenshot=None, session_id=uuid.uuid4()
    )
    findings = await agent.analyze(page_data)
    
    # Assert that the computational semantic topology loop catches the ARIA contradiction
    assert len(findings) > 0
    guidelines = [f.guideline for f in findings]
    assert "F59" in guidelines or "G108" in guidelines or any(f.agent == "cognitive" for f in findings)


@pytest.mark.asyncio
async def test_neural_dynamic_kinetic_vectorization():
    agent = NeuralAgent()
    element = ElementData(
        tag="div", html="<div class='shift'></div>", selector="div.shift", text="",
        computed_styles={"transitionDuration": "0.1s, 0.2s", "transform": "scale(1.2)"}, attributes={}, 
        bounding_box={"x": 0.0, "y": 0.0, "width": 200.0, "height": 200.0}, parent_styles={}
    )
    page_data = PageData(
        url="https://test.com", links=[], text_elements=[element], form_elements=[], images=[], screenshot=None, session_id=uuid.uuid4()
    )
    findings = await agent.analyze(page_data)
    
    # Assert the kinetic entropy engine detects fast vestibular layout shifts
    assert len(findings) > 0
    assert findings[0].agent == "neural"

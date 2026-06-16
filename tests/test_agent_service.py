import pytest
from auditor.application.agent_service import AgentService, get_agent_service
from auditor.application.agents.controller import AgentController

@pytest.mark.asyncio
async def test_agent_service_singleton():
    """Verifies AgentService enforces the singleton design pattern."""
    srv1 = get_agent_service()
    srv2 = get_agent_service()
    
    assert srv1 is srv2
    assert srv1._initialized is True

@pytest.mark.asyncio
async def test_agent_service_lazy_load_controller():
    """Verifies that visual, motor, and cognitive agents are loaded on first access."""
    # Reset singleton state to test loading clean instance
    AgentService._instance = None
    
    srv = get_agent_service()
    assert srv.controller is None
    
    controller = await srv.get_controller()
    assert isinstance(controller, AgentController)
    assert srv.controller is controller
    
    # Assert standard agents loaded
    assert len(controller.agents) == 4
    agent_names = [a.agent_name for a in controller.agents]
    assert "visual" in agent_names
    assert "motor" in agent_names
    assert "cognitive" in agent_names
    assert "neural" in agent_names


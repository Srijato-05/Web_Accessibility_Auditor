"""
AGENT SERVICE: SINGLETON LIFECYCLE MANAGEMENT
=============================================

Role: Manages the persistence and reuse of specialized accessibility agents.
This service ensures that high-memory agents (like NeuralAgent) are 
instantiated once and shared across multiple audit missions.
"""

import asyncio
from typing import List, Optional
from auditor.application.agents.controller import AgentController
from auditor.application.agents.visual_agent import VisualAgent
from auditor.application.agents.motor_agent import MotorAgent
from auditor.application.agents.cognitive_agent import CognitiveAgent
from auditor.shared.logging import auditor_logger

class AgentService:
    """
    Singleton manager for the Agentic Accessibility Hub.
    """
    _instance: Optional['AgentService'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.logger = auditor_logger.getChild("AgentService")
        self.controller: Optional[AgentController] = None
        self._initialized = True

    async def get_controller(self) -> AgentController:
        """
        Returns the persistent AgentController instance.
        Lazy-loads agents on first access.
        """
        async with self._lock:
            if self.controller is None:
                self.logger.info("Initializing Singleton Agentic Hub...")
                
                # Standard Agents
                agents = [
                    VisualAgent(),
                    MotorAgent(),
                    CognitiveAgent()
                ]
                
                # Neural Agent (Disabled for Ultra-Fast Performance Scan)
                # From user request: "add only one mode and the fastest one"
                # To re-enable, uncomment the lines below.
                """
                try:
                    from auditor.application.agents.neural_agent import NeuralAgent
                    self.logger.info("Loading Neural Forensic Agent (Qwen-1.5B)...")
                    agents.append(NeuralAgent())
                except Exception as e:
                    self.logger.error(f"Neural Agent loading failed: {e}")
                """

                self.controller = AgentController(agents)
                self.logger.info(f"Agentic Hub ONLINE with {len(agents)} deterministic agents.")
            
            return self.controller

# Global accessor
def get_agent_service() -> AgentService:
    return AgentService()

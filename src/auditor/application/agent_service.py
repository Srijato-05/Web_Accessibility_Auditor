"""
AGENT SERVICE: SINGLETON LIFECYCLE MANAGEMENT
=============================================

Role: Manages the persistence and reuse of specialized accessibility agents.
This service ensures that agents are instantiated once and shared across multiple audit missions.
"""

import asyncio
from typing import List, Optional
from auditor.application.agents.controller import AgentController
from auditor.application.agents.visual_agent import VisualAgent
from auditor.application.agents.motor_agent import MotorAgent
from auditor.application.agents.cognitive_agent import CognitiveAgent
from auditor.application.agents.neural_agent import NeuralAgent
from auditor.shared.logging import auditor_logger

class AgentService:
    """
    Singleton manager for the Agentic Accessibility Hub.
    """
    _instance: Optional['AgentService'] = None

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
        self._lock = asyncio.Lock()
        self._initialized = True

    async def get_controller(self) -> AgentController:
        """
        Returns the persistent AgentController instance.
        Lazy-loads agents on first access.
        """
        async with self._lock:
            if self.controller is None:
                self.logger.info("Initializing Singleton Agentic Hub...")
                
                # Load all Advanced Heuristic Agents
                agents = [
                    VisualAgent(),
                    MotorAgent(),
                    CognitiveAgent(),
                    NeuralAgent()
                ]
                
                self.controller = AgentController(agents)
                self.logger.info(f"Agentic Hub ONLINE with {len(agents)} advanced forensic agents.")
            
            return self.controller

# Global accessor
def get_agent_service() -> AgentService:
    return AgentService()

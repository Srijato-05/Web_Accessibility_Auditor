"""
AGENT CONTROLLER
=================

Central router that dispatches page data to all registered accessibility
agents and collects their findings. Agents run concurrently.

Output is validated before being returned.
"""

import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from auditor.domain.interfaces import IAccessibilityAgent # type: ignore
from auditor.domain.agent_finding import AgentFinding # type: ignore
from auditor.infrastructure.data_extractor import PageData # type: ignore
from auditor.application.agents.utils.validators import validate_batch # type: ignore
from auditor.shared.paths import EXPORTS_DIR # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore
from auditor.infrastructure.pdf_reporter import convert_json_to_pdf # type: ignore


class AgentController:
    """
    Routes analysis to disability-specific agents and aggregates results.

    Usage:
        controller = AgentController([VisualAgent(), MotorAgent(), CognitiveAgent()])
        findings = await controller.analyze(page_data)
    """

    def __init__(self, agents: List[IAccessibilityAgent]) -> None:
        self.agents = agents
        self.logger = auditor_logger.getChild("AgentController")

    async def analyze(self, page_data: PageData, include_agents: Optional[List[str]] = None) -> List[AgentFinding]:
        """
        Dispatch page data to all agents concurrently.
        Returns validated, structured findings from all agents.
        
        Args:
            page_data: The extracted data from the target page.
            include_agents: Optional list of agent names to include. 
                           If None, all registered agents are used.
        """
        active_agents = self.agents
        if include_agents is not None:
            active_agents = [a for a in self.agents if a.agent_name in include_agents]

        self.logger.info(
            f"Dispatching to {len(active_agents)} active agents: "
            f"{[a.agent_name for a in active_agents]}"
        )

        tasks = [agent.analyze(page_data) for agent in active_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings: List[AgentFinding] = []
        for i, result in enumerate(results):
            agent_name = active_agents[i].agent_name
            if isinstance(result, Exception):
                self.logger.error(
                    f"Agent '{agent_name}' failed: {result}"
                )
                continue
            if isinstance(result, list):
                self.logger.info(
                    f"Agent '{agent_name}' returned {len(result)} findings"
                )
                all_findings.extend(result)

        validated = validate_batch(all_findings)
        self.logger.info(
            f"Agent analysis complete: "
            f"{len(validated)} valid findings "
            f"(of {len(all_findings)} total)"
        )

        return validated

    def findings_to_json(self, findings: List[AgentFinding]) -> List[Dict[str, Any]]:
        """Convert all findings to the structured JSON output format."""
        return [f.to_dict() for f in findings]

    def export_findings(
        self,
        findings: List[AgentFinding],
        session_id: str,
        target_url: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> str:
        """Export findings to a JSON file. Returns the file path."""
        if output_dir is None:
            output_dir = str(EXPORTS_DIR)
            
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if target_url:
            import re
            cleaned = re.sub(r"^https?://(www\.)?", "", target_url)
            cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned).strip("_")
            base_name = f"{cleaned}_{timestamp}"
        else:
            id_match = re.match(r"^(.{1,8})", str(session_id))
            safe_id = id_match.group(1) if id_match else "agent"
            base_name = f"agent_findings_{safe_id}_{timestamp}"
            
        filepath = os.path.join(str(output_dir), f"{base_name}.json")

        output: Dict[str, Any] = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "total_findings": len(findings),
            "by_agent": {},
            "by_guideline": {},
            "findings": self.findings_to_json(findings),
        }

        for f in findings:
            output["by_agent"][f.agent] = output["by_agent"].get(f.agent, 0) + 1
            output["by_guideline"][f.guideline] = (
                output["by_guideline"].get(f.guideline, 0) + 1
            )

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2, ensure_ascii=False)

        self.logger.info(f"Agent findings exported to: {filepath}")
        
        # Generate PDF in a background thread to avoid blocking the event loop
        try:
            pdf_path = filepath.replace(".json", ".pdf")
            
            # Use current loop for non-blocking execution
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Correct way for async thread dispatch
                asyncio.create_task(asyncio.to_thread(convert_json_to_pdf, filepath, pdf_path))
            else:
                # Fallback for CLI/Standalone scripts
                convert_json_to_pdf(filepath, pdf_path)
                
        except Exception as e:
            self.logger.error(f"Failed to initiate PDF generation: {e}")

        return filepath

# No-op for cleanup

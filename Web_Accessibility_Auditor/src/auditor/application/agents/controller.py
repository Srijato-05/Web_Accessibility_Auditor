"""
AGENT CONTROLLER
=================

Central router that dispatches page data to all registered accessibility
agents and collects their findings. Agents run concurrently.

Output is validated before being returned.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from auditor.domain.interfaces import IAccessibilityAgent
from auditor.domain.agent_finding import AgentFinding
from auditor.infrastructure.data_extractor import PageData
from auditor.application.agents.utils.validators import validate_batch
from auditor.shared.logging import auditor_logger


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

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """
        Dispatch page data to all agents concurrently.
        Returns validated, structured findings from all agents.
        """
        self.logger.info(
            f"Dispatching to {len(self.agents)} agents: "
            f"{[a.agent_name for a in self.agents]}"
        )

        tasks = [agent.analyze(page_data) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings: List[AgentFinding] = []
        for i, result in enumerate(results):
            agent_name = self.agents[i].agent_name
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
        target_url: str = None,
        output_dir: str = "reports/exports",
    ) -> str:
        """Export findings to a JSON file. Returns the file path."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if target_url:
            import re
            cleaned = re.sub(r"^https?://(www\.)?", "", target_url)
            cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned).strip("_")
            base_name = f"{cleaned}_{timestamp}"
        else:
            base_name = f"agent_findings_{session_id[:8]}_{timestamp}"
            
        filepath = os.path.join(output_dir, f"{base_name}.json")

        output = {
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
        
        # Optionally generate a PDF (Isolated to prevent async loop conflicts)
        try:
            import multiprocessing
            pdf_path = filepath.replace(".json", ".pdf")
            p = multiprocessing.Process(
                target=_background_pdf_gen, 
                args=(filepath, pdf_path)
            )
            p.daemon = False
            p.start()
        except Exception as e:
            self.logger.error(f"Failed to initiate PDF generation: {e}")

        return filepath

def _background_pdf_gen(json_path: str, pdf_path: str):
    """Internal helper to bootstrap the PDF generation process with correct pathing."""
    import sys
    import os
    
    # Bootstrap sys.path for the subprocess
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _root not in sys.path:
        sys.path.insert(0, _root)
        
    try:
        from auditor.infrastructure.pdf_reporter import convert_json_to_pdf
        convert_json_to_pdf(json_path, pdf_path)
    except Exception as e:
        print(f"CRITICAL: Subprocess PDF Generation Failed: {e}")

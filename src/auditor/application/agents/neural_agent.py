"""
NEURAL ACCESSIBILITY AGENT
==========================
Uses a local LLM via Hugging Face Transformers to detect complex
semantic and cognitive barriers.
"""

import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import json
from typing import List, Optional, Any, cast, Dict
import asyncio
import re
from auditor.domain.agent_finding import AgentFinding # type: ignore
from auditor.infrastructure.data_extractor import PageData # type: ignore
from auditor.domain.interfaces import IAccessibilityAgent # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

# Lazy Loading for Heavy AI Libraries
torch = None
pipeline = None

def _lazy_load_ml():
    global torch, pipeline
    if torch is None or pipeline is None:
        try:
            import torch as _torch # type: ignore
            from transformers import pipeline as _pipeline # type: ignore
            torch = _torch
            pipeline = _pipeline
        except ImportError:
            torch = False
            pipeline = False

class NeuralAgent(IAccessibilityAgent):
    """
    Agentic AI Auditor (Local Mode).
    Specializes in Link Purpose, Semantic Clarity, and Cluttered Layouts.
    """

    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct") -> None:
        self.logger = auditor_logger.getChild("Agent.Neural")
        self.generator = None
        self.model_id = model_id
        
        # Trigger lazy load only when instance is created
        _lazy_load_ml()
        
        if not pipeline:
            self.logger.warning("Neural Agent: transformers not installed or failed to load. Running in MOCK mode.")
            return

        try:
            self.logger.info(f"Neural Agent: Loading local model {self.model_id}...")
            # Auto-detects GPU (cuda) or falls back to cpu
            is_cuda = False
            if hasattr(torch, 'cuda') and torch.cuda.is_available(): # type: ignore
                is_cuda = True
                
            device = 0 if is_cuda else -1
            self.generator = pipeline(
                "text-generation", 
                model=self.model_id, 
                model_kwargs={"dtype": torch.bfloat16 if is_cuda else torch.float32}, # type: ignore
                device=device
            )
            self.logger.info("Neural Agent: Local Transformers Pipeline Initialized.")
        except Exception as e:
            self.logger.critical(f"Neural Agent Initialization Failed: {e}")

    @property
    def agent_name(self) -> str:
        return "neural"

    async def analyze(self, page_data: PageData) -> List[AgentFinding]:
        """Performs AI-powered accessibility analysis."""
        self.logger.info(f"Neural Agent analyzing: {page_data.url}")
        
        if not self.generator:
            return self._get_mock_findings(page_data)

        # 1. Prepare data for Prompt
        links_summary = [
            {"text": link.text, "html": link.html[:80]} 
            for link in page_data.links[:50] # Top 50 links
        ]
        
        # 2. Build Chat Prompt
        messages = [
            {"role": "system", "content": "You are a web accessibility auditor analyzing HTML links. Identify vague link texts (WCAG 2.4.4) or semantic confusion. Output ONLY a valid JSON array of objects. Do not wrap it in markdown. The objects must have keys: 'violation_type', 'guideline', 'element', 'selector', 'issue', 'impact', 'fix', 'confidence', 'wcag_criterion'."},
            {"role": "user", "content": f"Analyze these elements:\n{json.dumps(links_summary, indent=2)}"}
        ]
        
        try:
            # 3. Synchronous Gen wrapped in an asyncio thread to not block event loop
            gen = cast(Any, self.generator)
            if not hasattr(gen, 'tokenizer') or gen.tokenizer is None:
                return []
                
            prompt = gen.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            def run_inference(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
                if not gen:
                    return []
                return cast(List[Dict[str, Any]], gen(
                    prompt, 
                    max_new_tokens=500, 
                    temperature=0.1, 
                    do_sample=False,
                    return_full_text=False
                ))
                
            response = await asyncio.to_thread(run_inference)
            raw_text = response[0]["generated_text"].strip()
            
            # Clean up potential markdown formatting the model might spit out anyway
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()
            
            ai_data = json.loads(raw_text)
            
            findings = []
            if isinstance(ai_data, list):
                for item in ai_data:
                    findings.append(AgentFinding(
                        agent=self.agent_name,
                        violation_type=item.get("violation_type", "predictability"),
                        guideline=item.get("guideline", "G94"),
                        element=item.get("element", "unknown"),
                        selector=item.get("selector", "a"),
                        issue=item.get("issue", "Semantic ambiguity detected by AI"),
                        impact=item.get("impact", "High"),
                        fix=item.get("fix", "Review context"),
                        confidence=float(item.get("confidence", 0.8)),
                        source="ml",
                        wcag_criterion=item.get("wcag_criterion", "2.4.4"),
                        session_id=page_data.session_id
                    ))
            return findings

        except Exception as e:
            self.logger.error(f"Neural Agent Local Inference Failed: {e}")
            return []

    def _get_mock_findings(self, page_data: PageData) -> List[AgentFinding]:
        """Fallback findings if transformers fails to initialize."""
        return []

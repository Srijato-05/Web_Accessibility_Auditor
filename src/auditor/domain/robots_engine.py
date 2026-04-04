"""
AUDITOR ROBOTS.TXT ADHERENCE ENGINE (R-Z10)
==========================================

Role: Autonomous adherence to crawling metadata.
Responsibilities:
  - Fetching and parsing robots.txt via urllib.robotparser.
  - Verifying if a target URL is permissible for audit.
  - Extracting sitemap locations for discovery engines.
"""

import logging
import httpx # type: ignore
from urllib.robotparser import RobotFileParser
from typing import List, Optional

# IDE PATH RECONCILIATION
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from auditor.shared.logging import auditor_logger # type: ignore

class RobotsAdherenceEngine:
    """
    Deterministic metadata compliance engine for the Auditor platform.
    """
    
    def __init__(self, user_agent: str = "Auditor.Autonomous"):
        self.user_agent = user_agent
        self.parser = RobotFileParser()
        self.logger = auditor_logger.getChild("Robots")
        self._is_ready = False

    async def initialize(self, base_url: str):
        """Initializes the engine by fetching robots.txt from the domain root."""
        robots_url = f"{base_url.rstrip('/')}/robots.txt"
        self.logger.info(f"Synchronizing Robots Metadata: {robots_url}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(robots_url)
                if resp.status_code == 200:
                    self.parser.parse(resp.text.splitlines())
                    self._is_ready = True
                else:
                    self.logger.warning(f"Robots.txt missing or unreachable [{resp.status_code}]. Assuming permissive defaults.")
                    self._is_ready = True # Permissive default
        except Exception as e:
            self.logger.error(f"Robots synchronization failure: {e}")
            self._is_ready = True # Permissive default on failure

    def is_allowed(self, url: str) -> bool:
        """Determines if the Auditor is permitted to audit the given URL."""
        if not self._is_ready: return True
        return self.parser.can_fetch(self.user_agent, url)

    def get_sitemaps(self) -> List[str]:
        """Extracts sitemap URLs discovered in robots.txt."""
        if not self._is_ready: return []
        return self.parser.site_maps() or []

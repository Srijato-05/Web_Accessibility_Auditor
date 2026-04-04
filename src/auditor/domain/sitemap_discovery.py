"""
AUDITOR SITEMAP DISCOVERY ENGINE (D-Z10)
========================================

Role: Autonomous target extraction from XML structures.
Responsibilities:
  - Fetching sitemap.xml (or nested indices).
  - Parsing loc tags using BeautifulSoup.
  - De-duplicating and normalizing discovered URLs.
"""

import logging
import httpx # type: ignore
from typing import List, Set
from bs4 import BeautifulSoup # type: ignore

# IDE PATH RECONCILIATION
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from auditor.shared.logging import auditor_logger # type: ignore

class SitemapDiscoveryEngine:
    """
    High-fidelity XML sitemap parser for autonomous target discovery.
    """
    
    def __init__(self):
        self.logger = auditor_logger.getChild("Sitemap")
        self._headers = {"User-Agent": "Auditor.Autonomous/0.1.0"}

    async def discover_urls(self, sitemap_url: str) -> Set[str]:
        """Recursively discovers all URLs from a sitemap or index."""
        discovered: Set[str] = set()
        to_process = {sitemap_url}
        processed = set()
        
        async with httpx.AsyncClient(headers=self._headers, timeout=30.0, follow_redirects=True) as client:
            while to_process:
                current = to_process.pop()
                if current in processed: continue
                
                self.logger.info(f"Analyzing Sitemap: {current}")
                try:
                    resp = await client.get(current)
                    resp.raise_for_status()
                    
                    soup = BeautifulSoup(resp.content, "xml")
                    
                    # 1. Handle Sitemap Index
                    indices = [loc.text for loc in soup.find_all("sitemap")]
                    to_process.update([i for i in indices if i not in processed])
                    
                    # 2. Handle standard URL entries
                    urls = [loc.text for loc in soup.find_all("url")]
                    for url_node in soup.find_all("url"):
                        loc = url_node.find("loc")
                        if loc: discovered.add(loc.text.strip())
                        
                    processed.add(current)
                except Exception as e:
                    self.logger.warning(f"Sitemap processing error [{current}]: {e}")
                    
        self.logger.info(f"Discovery Complete. Identified {len(discovered)} unique targets.")
        return discovered

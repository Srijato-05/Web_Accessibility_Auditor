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
        self._headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}

    async def discover_urls(self, sitemap_url: str) -> Set[str]:
        """Recursively discovers all URLs from a sitemap or index using Apex Stealth."""
        from playwright.async_api import async_playwright
        discovered: Set[str] = set()
        to_process = {sitemap_url}
        processed = set()
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self._headers["User-Agent"])
                
                # Apex Stealth Injection
                stealth_code = """
                    (() => {
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.__APEX_STEALTH_ACTIVE__ = true;
                    })();
                """
                await context.add_init_script(stealth_code)
                page = await context.new_page()
                
                while to_process:
                    current = to_process.pop()
                    if current in processed: continue
                    
                    self.logger.info(f"Analyzing Sitemap: {current} (Stealth: Active)")
                    try:
                        resp = await page.goto(current, wait_until="networkidle", timeout=60000)
                        if resp and resp.status == 200:
                            content = await page.content()
                            soup = BeautifulSoup(content, "xml")
                            
                            # 1. Handle Sitemap Index
                            indices = [loc.text for loc in soup.find_all("sitemap")]
                            for idx in indices:
                                if idx not in processed:
                                    to_process.add(idx)
                            
                            # 2. Handle standard URL entries
                            for url_node in soup.find_all("url"):
                                loc = url_node.find("loc")
                                if loc: 
                                    discovered.add(loc.text.strip())
                                    
                            processed.add(current)
                        else:
                            status = resp.status if resp else "Unknown"
                            self.logger.warning(f"Sitemap unreachable [{current}] Status: {status}")
                    except Exception as e:
                        self.logger.warning(f"Sitemap processing error [{current}]: {e}")
                
                await browser.close()
        except Exception as top_e:
            self.logger.error(f"Sitemap Engine Critical Failure: {top_e}")
            
        self.logger.info(f"Discovery Complete. Identified {len(discovered)} unique targets.")
        return discovered
                    
        self.logger.info(f"Discovery Complete. Identified {len(discovered)} unique targets.")
        return discovered

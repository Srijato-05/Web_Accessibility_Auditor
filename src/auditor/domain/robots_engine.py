"""
AUDITOR ROBOTS.TXT ADHERENCE ENGINE (R-Z10)
==========================================

Role: Autonomous adherence to crawling metadata.
Responsibilities:
  - Fetching and parsing robots.txt via urllib.robotparser.
  - Verifying if a target URL is permissible for audit.
  - Extracting sitemap locations for discovery engines.
"""

from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from typing import List

# IDE PATH RECONCILIATION
import os
import sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from auditor.shared.logging import auditor_logger # type: ignore

class RobotsAdherenceEngine:
    """
    Deterministic metadata compliance engine for the Auditor platform.
    """
    
    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"):
        self.user_agent = user_agent
        self.parser = RobotFileParser()
        self.logger = auditor_logger.getChild("Robots")
        self._is_ready = False

    async def initialize(self, base_url: str):
        """Initializes the engine by fetching robots.txt from the domain root using Apex Stealth."""
        from playwright.async_api import async_playwright
        parsed = urlparse(base_url)
        root_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{root_url}/robots.txt"
        self.logger.info(f"Synchronizing Robots Metadata: {robots_url} (Stealth: Active)")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self.user_agent)
                
                # Apex Stealth Injection
                stealth_code = """
                    (() => {
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.__APEX_STEALTH_ACTIVE__ = true;
                    })();
                """
                await context.add_init_script(stealth_code)
                page = await context.new_page()
                
                resp = await page.goto(robots_url, wait_until="networkidle", timeout=30000)
                if resp and resp.status == 200:
                    content = await page.content()
                    # Strip HTML if the server returned a page instead of text (some do for 404s/403s)
                    # But robots.txt should be plain text.
                    text = await page.evaluate("() => document.body.innerText")
                    lines = text.splitlines()
                    self.parser.parse(lines)
                    self.logger.info(f"Compliance Metadata Synchronized: {len(lines)} rules imported.")
                    self._is_ready = True
                else:
                    status = resp.status if resp else "Unknown"
                    self.logger.warning(f"Robots.txt unreachable [{status}]. Assuming permissive defaults.")
                    self.parser.parse([])
                    self._is_ready = True
                await browser.close()
        except Exception as e:
            self.logger.error(f"Robots synchronization failure: {e}")
            self.parser.parse([]) # Explicitly allow all
            self._is_ready = True

    def is_allowed(self, url: str) -> bool:
        """Determines if the Auditor is permitted to audit the given URL."""
        if not self._is_ready: 
            return True
        
        # If parser is initialized but has no rules, default to True
        try:
            return self.parser.can_fetch(self.user_agent, url)
        except Exception:
            return True

    def get_sitemaps(self) -> List[str]:
        """Extracts sitemap URLs discovered in robots.txt."""
        if not self._is_ready: return []
        return self.parser.site_maps() or []

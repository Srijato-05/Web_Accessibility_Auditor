from typing import List, Optional, Any, cast
from playwright.async_api import async_playwright, Browser, BrowserContext, Page # type: ignore
from auditor.domain.crawler import ILinkExtractor # type: ignore

class PlaywrightLinkExtractor(ILinkExtractor):
    """Infrastructure implementation of ILinkExtractor using Playwright."""

    def __init__(self):
        self.playwright_mgr: Optional[Any] = None
        self.browser: Optional[Browser] = None

    async def start(self):
        """Initializes the persistent browser instance for link extraction."""
        if not self.browser:
            mgr = await async_playwright.start()
            self.playwright_mgr = mgr
            # Using casting to satisfy the type checker for the dynamic 'chromium' attribute
            self.browser = await cast(Any, mgr).chromium.launch(headless=True)

    async def teardown(self):
        """Gracefully terminates the browser and playwright manager."""
        mgr = self.playwright_mgr
        br = self.browser
        if br:
            try: await br.close()
            except: pass
        if mgr:
            try: await mgr.stop()
            except: pass
        self.browser = None
        self.playwright_mgr = None

    async def extract_links(self, url: str) -> List[str]:
        """Scrape all <a> tags from the page using Apex Stealth Masking."""
        if not self.browser:
            await self.start()
        
        br = self.browser
        if not br:
             return []
             
        try:
            # Persona: Desktop-Windows-Chrome Signature
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            
            context = await br.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
            )
                
            # Injection: Apex Stealth Masking (Cycle 7 Forensic Suit)
            stealth_code = """
                (() => {
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    Object.defineProperty(navigator, 'plugins', {get: () => ({length: 5})});
                    window.__APEX_STEALTH_ACTIVE__ = true;
                })();
            """
            await context.add_init_script(stealth_code)
            
            page = await context.new_page()
            
            try:
                print(f"[Crawler] Discovering links on: {url} (Stealth: Active)")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extract all href attributes
                links = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
                return list(set(cast(List[str], links))) # Unique links from page
            except Exception as e:
                print(f"[Crawler] Discovery Error on {url}: {e}")
                return []
            finally:
                if 'page' in locals() and page:
                    try: await page.close()
                    except: pass
                if 'context' in locals() and context:
                    try: await context.close()
                    except: pass
        except Exception as e:
            print(f"[Crawler] Critical Session Error on {url}: {e}")
            return []
        
        return [] # Fallback to satisfy static analysis return path requirements

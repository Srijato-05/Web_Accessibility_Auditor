from typing import List
from playwright.async_api import async_playwright
from auditor.domain.crawler import ILinkExtractor

class PlaywrightLinkExtractor(ILinkExtractor):
    """Infrastructure implementation of ILinkExtractor using Playwright."""

    async def extract_links(self, url: str) -> List[str]:
        """Scrape all <a> tags from the page using Apex Stealth Masking."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Persona: Desktop-Windows-Chrome Signature
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            
            context = await browser.new_context(
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
                return list(set(links)) # Unique links from page
            except Exception as e:
                print(f"[Crawler] Discovery Error on {url}: {e}")
                return []
            finally:
                await browser.close()

from typing import List
from playwright.async_api import async_playwright
from auditor.domain.crawler import ILinkExtractor

class PlaywrightLinkExtractor(ILinkExtractor):
    """Infrastructure implementation of ILinkExtractor using Playwright."""

    async def extract_links(self, url: str) -> List[str]:
        """Scrape all <a> tags from the page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"[Crawler] Discovering links on: {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Extract all href attributes
                links = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
                return list(set(links)) # Unique links from page
            except Exception as e:
                print(f"[Crawler] Discovery Error on {url}: {e}")
                return []
            finally:
                await browser.close()

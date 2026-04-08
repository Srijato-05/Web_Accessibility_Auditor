import asyncio
from playwright.async_api import async_playwright

async def debug_scan():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.india.gov.in/"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Navigation failed: {e}")
            return
        
        print("Waiting for networkidle...")
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
        except:
            print("Networkidle timed out.")
            
        await asyncio.sleep(5) # Extra buffer
        
        # Check standard DOM
        links = await page.evaluate("() => document.querySelectorAll('a').length")
        text_len = await page.evaluate("() => document.body.innerText.length")
        title = await page.title()
        print(f"Title: {title}")
        print(f"Standard DOM: {links} links, {text_len} chars of text")
        
        # Check for iframes
        iframes = await page.query_selector_all('iframe')
        print(f"Iframes found: {len(iframes)}")
        
        # Get a snippet of HTML
        html = await page.content()
        print(f"HTML Length: {len(html)}")
        if "india.gov.in" in html:
            print("Target string found in HTML.")
        else:
            print("WARNING: Target string NOT found in HTML!")
            print(f"HTML Preview: {html[:1000]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scan())

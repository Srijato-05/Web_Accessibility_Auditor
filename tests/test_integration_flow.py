import pytest
import asyncio
import threading
import uuid
from uuid import uuid4
from http.server import SimpleHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock, AsyncMock
from sqlmodel.ext.asyncio.session import AsyncSession

# Core imports to test
from auditor.infrastructure.playwright_engine import PlaywrightEngine
from auditor.infrastructure.audit_repository import SqlAlchemyAuditRepository
from auditor.application.audit_service import AuditService
from auditor.application.crawl_service import CrawlService
from auditor.domain.crawler import LinkDiscoveryService
from auditor.infrastructure.link_extractor import PlaywrightLinkExtractor

class MockHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Local HTTP handler serving intentional accessibility violations."""
    def log_message(self, format, *args):
        # Mute console request logging during tests
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Accessibility Sandbox Home</title></head>
            <body>
                <h1>Accessibility Sandbox Home</h1>
                <!-- VIOLATION 1: Image missing an alt attribute -->
                <img src="/assets/logo.png" />
                <a href="/about.html">About Page Link</a>
                <!-- VIOLATION 2: Button with terrible color contrast -->
                <button style="background-color: #ffffff; color: #fbfbfb;">Terrible Contrast</button>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/about.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Accessibility Sandbox About</title></head>
            <body>
                <h1>About the Sandbox</h1>
                <!-- VIOLATION 3: Input field without an associated label -->
                <input type="text" id="username_field" />
                <a href="/index.html">Back to Home</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def start_local_server(port=8089):
    """Starts a local HTTP server in a daemon thread."""
    server = HTTPServer(("127.0.0.1", port), MockHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

@pytest.mark.asyncio
async def test_end_to_end_audit_flow(temp_db_engine, mock_neo4j_driver):
    """
    Verifies the entire crawler & auditor integration pipeline.
    Spins up a local HTTP server, crawls it using Playwright,
    runs accessibility rule evaluations, and persists relational
    and graph metrics.
    """
    port = 8089
    server = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/"
    
    # 1. Setup repositories & adapters
    async with AsyncSession(temp_db_engine) as db_session:
        sql_repo = SqlAlchemyAuditRepository(db_session)
        browser_engine = PlaywrightEngine(uuid4())
        
        # Safe skip if Chromium is not available on test container
        try:
            await browser_engine.start()
        except Exception as e:
            server.shutdown()
            server.server_close()
            pytest.skip(f"Skipping integration flow test: Playwright launch failed: {e}")
            return
            
        # 2. Setup service layers
        audit_service = AuditService(browser_engine, sql_repo)
        link_extractor = PlaywrightLinkExtractor()
        crawler_service = LinkDiscoveryService(link_extractor)
        
        # Patch Neo4j graph driver with our test mock
        audit_service.tg_repo.driver = mock_neo4j_driver
        
        # 3. Setup crawl orchestrator
        crawl_service = CrawlService(
            audit_service=audit_service,
            crawler_service=crawler_service,
            max_depth=2,
            max_pages=3,
            concurrency=1
        )
        crawl_service.tg_repo.driver = mock_neo4j_driver
        
        try:
            # 4. Execute the crawl session
            session = await crawl_service.run(base_url)
            
            # 5. Core validation assertions
            assert session is not None
            assert session.status.value == "completed"
            assert len(session.violations) > 0
            
            # Check relational persistence (SQLite)
            saved_session = await sql_repo.get_session(session.id)
            assert saved_session is not None
            assert len(saved_session.violations) > 0
            
            # Check if violations contain our targeted missing alt or bad contrast rules
            rules_found = [v.rule_id for v in saved_session.violations]
            # Axe should flag standard image-alt or color-contrast or label violations
            assert any(r in ["image-alt", "color-contrast", "label"] for r in rules_found)
            
        finally:
            # Cleanup
            await browser_engine.teardown()
            await link_extractor.teardown()
            server.shutdown()
            server.server_close()

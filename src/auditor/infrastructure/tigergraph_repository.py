import os
import hashlib
import asyncio
from urllib.parse import urlparse
import pyTigerGraph as tg
from dotenv import load_dotenv

from auditor.shared.logging import auditor_logger
from auditor.domain.violation import Violation

load_dotenv()


class TigerGraphRepository:
    def __init__(self):
        self.logger = auditor_logger.getChild("TigerGraphRepo")
        self._semaphore = asyncio.Semaphore(5) # Throttling structural sync to avoid connection flood
        raw_host = os.getenv("TG_HOST")
        self.graphname = os.getenv("TG_GRAPHNAME", "AuditorGraph")
        self.secret = os.getenv("TG_SECRET")

        if not all([raw_host, self.secret]):
            self.logger.warning("TigerGraph credentials missing in .env")
            self.conn = None
            return

        parsed = urlparse(raw_host)
        self.host = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else raw_host

        if not self.host.startswith("http"):
            self.host = f"https://{self.host}"

        try:
            self.conn = tg.TigerGraphConnection(
                host=self.host,
                graphname=self.graphname,
                gsqlSecret=self.secret,
                tgCloud=True
            )

            self.conn.getToken()

            self.logger.info(f"Connected: {self.host} | Graph: {self.graphname}")

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.conn = None

    async def upsert_page_link_async(self, source_url, target_url, domain_url):
        if not self.conn:
            return
        async with self._semaphore:
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(
                        self._upsert_page_link_sync,
                        source_url,
                        target_url,
                        domain_url
                    ),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("TigerGraph API Timeout: Page link upsert skipped.")
            except Exception as e:
                self.logger.error(f"Async Page Link Error: {type(e).__name__} - {e}")

    def _upsert_page_link_sync(self, source_url, target_url, domain_url):
        try:
            self.conn.upsertVertex("Domain", domain_url, {"url": domain_url})
            self.conn.upsertVertex("Page", source_url, {"url": source_url})
            self.conn.upsertVertex("Page", target_url, {"url": target_url})

            self.conn.upsertEdge("Domain", domain_url, "DOMAIN_OWNS_PAGE", "Page", source_url)
            self.conn.upsertEdge("Page", source_url, "PAGE_LINKS_TO", "Page", target_url)

        except Exception as e:
            self.logger.error(f"Sync Page Link Error: {e}")

    async def upsert_component_violation_async(self, page_url, violation: Violation, node_html):
        if not self.conn:
            return
        async with self._semaphore:
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(
                        self._upsert_component_violation_sync,
                        page_url,
                        violation,
                        node_html
                    ),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("TigerGraph API Timeout: Component upsert skipped.")
            except Exception as e:
                self.logger.error(f"Async Component Error: {type(e).__name__} - {e}")

    def _upsert_component_violation_sync(self, page_url, violation: Violation, node_html):
        try:
            footprint = hashlib.sha256(node_html.encode("utf-8")).hexdigest()
            snippet_preview = node_html[:150]

            standard_id = "WCAG-2.2"
            if ".gov.in" in page_url or ".nic.in" in page_url:
                standard_id = "GIGW-3.0"
            elif "bank" in page_url or "sbi" in page_url or "hdfc" in page_url:
                standard_id = "RBI-Master-Circular"

            impact_val = (
                violation.impact.value
                if hasattr(violation.impact, "value")
                else str(violation.impact)
            )

            self.conn.upsertVertex(
                "Component",
                footprint,
                {
                    "footprint_hash": footprint,
                    "snippet": snippet_preview
                }
            )

            self.conn.upsertVertex(
                "Violation",
                violation.rule_id,
                {
                    "rule_id": violation.rule_id,
                    "impact": impact_val
                }
            )

            self.conn.upsertVertex(
                "ComplianceStandard",
                standard_id,
                {
                    "name": standard_id
                }
            )

            self.conn.upsertEdge("Page", page_url, "PAGE_CONTAINS", "Component", footprint)

            self.conn.upsertEdge(
                "Component",
                footprint,
                "COMPONENT_TRIGGERS",
                "Violation",
                violation.rule_id
            )

            self.conn.upsertEdge(
                "Violation",
                violation.rule_id,
                "VIOLATION_FAILS",
                "ComplianceStandard",
                standard_id
            )

        except Exception as e:
            self.logger.error(f"Sync Component Error: {e}")
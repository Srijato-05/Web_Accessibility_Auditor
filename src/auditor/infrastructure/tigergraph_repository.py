"""
TIGERGRAPH REPOSITORY: STRUCTURAL INTELLIGENCE ENGINE
=====================================================
Role: Maps the "structural contagion" of accessibility violations.
"""
import os
import hashlib
import asyncio
from typing import Optional
import pyTigerGraph as tg  # type: ignore
from dotenv import load_dotenv

from auditor.shared.logging import auditor_logger
from auditor.domain.violation import Violation

# Ensure environment variables are loaded (NO HARDCODING)
load_dotenv()


class TigerGraphRepository:
    """
    Asynchronous wrapper for TigerGraph Cloud interactions.
    Maps websites as graphs to find root-cause accessibility failures.

    All blocking pyTigerGraph SDK calls are offloaded to a thread via
    asyncio.to_thread so they never block the Playwright event loop.
    """

    def __init__(self):
        self.logger = auditor_logger.getChild("TigerGraphRepo")
        raw_host = os.getenv("TG_HOST")
        self.graphname = os.getenv("TG_GRAPHNAME", "AuditorGraph")
        self.secret = os.getenv("TG_SECRET")

        if not all([raw_host, self.secret]):
            self.logger.warning(
                "TigerGraph credentials missing in .env. Graph Intelligence disabled."
            )
            self.conn = None
            return

        # --- AUTO-CLEANING HOST URL ---
        # If user pasted a long URL like https://xyz.i.tgcloud.io/studio?tab=...
        # we extract just the base 'https://xyz.i.tgcloud.io'
        from urllib.parse import urlparse

        parsed = urlparse(raw_host)
        self.host = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else raw_host
        if not self.host.startswith("http"):
            self.host = f"https://{self.host}"

        try:
            # TigerGraph Savanna v4 requires gsqlSecret for token generation
            self.conn = tg.TigerGraphConnection(
                host=self.host,
                graphname=self.graphname,
                gsqlSecret=self.secret,
                tgCloud=True,
            )
            # WORKAROUND: Force ports if the library doesn't set them for Cloud
            if not hasattr(self.conn, "restppPort"):
                self.conn.restppPort = "443"
            if not hasattr(self.conn, "gsPort"):
                self.conn.gsPort = "443"
            
            # Fetch token — returns (token_string, expiry) tuple
            token_result = self.conn.getToken(self.secret)
            if isinstance(token_result, tuple):
                self.conn.apiToken = token_result[0]
            elif isinstance(token_result, list):
                self.conn.apiToken = token_result[0]
            else:
                self.conn.apiToken = token_result

            self.logger.info(
                f"TigerGraph Cloud Connected: {self.host} | Graph: {self.graphname}"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to TigerGraph: {e}")
            self.conn = None

    # ------------------------------------------------------------------
    # PAGE LINK GRAPH POPULATION
    # ------------------------------------------------------------------

    async def upsert_page_link_async(
        self, source_url: str, target_url: str, domain_url: str
    ) -> None:
        """Asynchronously pushes page discovery links to the graph."""
        if not self.conn:
            return
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    self._upsert_page_link_sync, source_url, target_url, domain_url
                ),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            self.logger.warning("TigerGraph API Timeout: Page link upsert skipped.")
        except Exception as e:
            self.logger.error(f"TigerGraph Async Page Link Upsert Failed: {e}")

    def _upsert_page_link_sync(
        self, source_url: str, target_url: str, domain_url: str
    ) -> None:
        try:
            self.conn.upsertVertex("Domain", domain_url, attributes={"url": domain_url})
            self.conn.upsertVertex("Page", source_url, attributes={"url": source_url})
            self.conn.upsertVertex("Page", target_url, attributes={"url": target_url})

            self.conn.upsertEdge("Domain", domain_url, "DOMAIN_OWNS_PAGE", "Page", source_url)
            self.conn.upsertEdge("Page", source_url, "PAGE_LINKS_TO", "Page", target_url)
        except Exception as e:
            self.logger.error(f"TigerGraph Link Upsert Failed: {e}")

    # ------------------------------------------------------------------
    # COMPONENT VIOLATION GRAPH POPULATION
    # ------------------------------------------------------------------

    async def upsert_component_violation_async(
        self, page_url: str, violation: Violation, node_html: str
    ) -> None:
        """Asynchronously maps a violation to a hashed HTML component in the graph."""
        if not self.conn:
            return
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    self._upsert_component_violation_sync, page_url, violation, node_html
                ),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            self.logger.warning("TigerGraph API Timeout: Component upsert skipped.")
        except Exception as e:
            self.logger.error(f"TigerGraph Async Component Upsert Failed: {e}")

    def _upsert_component_violation_sync(
        self, page_url: str, violation: Violation, node_html: str
    ) -> None:
        try:
            # 1. HASH THE HTML — proves 10,000 errors come from 1 shared component
            footprint = hashlib.sha256(node_html.encode("utf-8")).hexdigest()
            snippet_preview = node_html[:150]

            # 2. Dynamic Indian Standard Tagging
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

            # 3. Upsert Vertices
            self.conn.upsertVertex(
                "Component",
                footprint,
                attributes={"footprint_hash": footprint, "snippet": snippet_preview},
            )
            self.conn.upsertVertex(
                "Violation",
                violation.rule_id,
                attributes={"rule_id": violation.rule_id, "impact": impact_val},
            )
            self.conn.upsertVertex(
                "ComplianceStandard",
                standard_id,
                attributes={"name": standard_id},
            )

            # 4. Upsert Edges
            self.conn.upsertEdge("Page", page_url, "PAGE_CONTAINS", "Component", footprint)
            self.conn.upsertEdge(
                "Component", footprint, "COMPONENT_TRIGGERS", "Violation", violation.rule_id
            )
            self.conn.upsertEdge(
                "Violation",
                violation.rule_id,
                "VIOLATION_FAILS",
                "ComplianceStandard",
                standard_id,
            )
        except Exception as e:
            self.logger.error(f"TigerGraph Component Upsert Failed: {e}")

import os
import hashlib
import asyncio
import sys
from urllib.parse import urlparse
from typing import Any, cast, Optional, Dict, List

# IDE PATH RECONCILIATION: Ensuring import stability for external scripts
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from neo4j import GraphDatabase # type: ignore
except ImportError:
    # Fallback to prevent crash if library is not fully initialized
    GraphDatabase = None

from dotenv import load_dotenv # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore
from auditor.domain.violation import Violation # type: ignore

load_dotenv()


class Neo4jRepository:
    def __init__(self):
        self.logger = auditor_logger.getChild("Neo4jRepo")
        self._semaphore = asyncio.Semaphore(5)  # Throttling structural sync to avoid connection flood
        
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not GraphDatabase:
            self.logger.warning("Neo4j library not installed. Repository running offline.")
            self.driver = None
            return

        if not self.password:
            self.logger.warning("Neo4j password missing in environment. Repository running offline.")
            self.driver = None
            return

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verification ping
            self.driver.verify_connectivity()
            self.logger.info(f"Connected to Neo4j instance at {self.uri} as user {self.user}")
        except Exception as e:
            self.logger.error(f"Neo4j connection establishment failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def ping(self) -> bool:
        if not self.driver:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def upsert_page_link_async(self, source_url: str, target_url: str, domain_url: str):
        if not self.driver:
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
                self.logger.warning("Neo4j API Timeout: Page link upsert skipped.")
            except Exception as e:
                self.logger.error(f"Async Page Link Error: {type(e).__name__} - {e}")

    def _upsert_page_link_sync(self, source_url: str, target_url: str, domain_url: str):
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                query = """
                MERGE (d:Domain {url: $domain_url})
                MERGE (s:Page {url: $source_url})
                MERGE (t:Page {url: $target_url})
                MERGE (d)-[:DOMAIN_OWNS_PAGE]->(s)
                MERGE (s)-[:PAGE_LINKS_TO]->(t)
                """
                session.run(query, domain_url=domain_url, source_url=source_url, target_url=target_url)
        except Exception as e:
            self.logger.error(f"Sync Page Link Error: {e}")

    async def upsert_component_violation_async(self, page_url: str, violation: Violation, node_html: str):
        if not self.driver:
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
                self.logger.warning("Neo4j API Timeout: Component upsert skipped.")
            except Exception as e:
                self.logger.error(f"Async Component Error: {type(e).__name__} - {e}")

    def _upsert_component_violation_sync(self, page_url: str, violation: Violation, node_html: str):
        if not self.driver:
            return
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

            with self.driver.session() as session:
                query = """
                MERGE (p:Page {url: $page_url})
                MERGE (c:Component {id: $footprint})
                ON CREATE SET c.footprint_hash = $footprint, c.snippet = $snippet_preview
                MERGE (v:Violation {id: $rule_id})
                ON CREATE SET v.rule_id = $rule_id, v.impact = $impact_val
                MERGE (s:ComplianceStandard {id: $standard_id})
                ON CREATE SET s.name = $standard_id

                MERGE (p)-[:PAGE_CONTAINS]->(c)
                MERGE (c)-[:COMPONENT_TRIGGERS]->(v)
                MERGE (v)-[:VIOLATION_FAILS]->(s)
                """
                session.run(
                    query,
                    page_url=page_url,
                    footprint=footprint,
                    snippet_preview=snippet_preview,
                    rule_id=violation.rule_id,
                    impact_val=impact_val,
                    standard_id=standard_id
                )
        except Exception as e:
            self.logger.error(f"Sync Component Error: {e}")

    def get_graph_data(self) -> dict:
        if not self.driver:
            return {"nodes": [], "links": []}
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                """
                result = session.run(query)
                nodes = {}
                links = []

                for record in result:
                    n = record["n"]
                    if n:
                        # Extract unique node element identifier
                        node_ref = n.element_id if hasattr(n, "element_id") else n.id
                        labels = list(n.labels)
                        
                        if "Page" in labels:
                            nodes[node_ref] = {
                                "id": n.get("url"),
                                "label": n.get("url")[:30] + "...",
                                "type": "page"
                            }
                        elif "Component" in labels:
                            nodes[node_ref] = {
                                "id": n.get("id"),
                                "label": "DOM Element",
                                "type": "component"
                            }
                        elif "Violation" in labels:
                            impact = n.get("impact", "minor")
                            node_type = "violation_critical" if impact.lower() == "critical" else (
                                "violation_major" if impact.lower() in ("major", "serious") else "violation"
                            )
                            nodes[node_ref] = {
                                "id": n.get("id"),
                                "label": n.get("id"),
                                "type": node_type
                            }
                        elif "Domain" in labels:
                            nodes[node_ref] = {
                                "id": n.get("url"),
                                "label": n.get("url"),
                                "type": "page"
                            }
                        elif "ComplianceStandard" in labels:
                            nodes[node_ref] = {
                                "id": n.get("id"),
                                "label": n.get("name"),
                                "type": "page"
                            }

                    r = record["r"]
                    m = record["m"]
                    if r and m:
                        source_node = n
                        target_node = m
                        
                        source_id = source_node.get("url") if ("Page" in source_node.labels or "Domain" in source_node.labels) else source_node.get("id")
                        target_id = target_node.get("url") if ("Page" in target_node.labels or "Domain" in target_node.labels) else target_node.get("id")
                        
                        if source_id and target_id:
                            links.append({
                                "source": source_id,
                                "target": target_id
                            })

                # Deduplicate elements
                unique_nodes = list(nodes.values())
                seen_links = set()
                unique_links = []
                for l in links:
                    key = (l["source"], l["target"])
                    if key not in seen_links:
                        seen_links.add(key)
                        unique_links.append(l)

                return {"nodes": unique_nodes, "links": unique_links}
        except Exception as e:
            self.logger.error(f"Error fetching Neo4j graph data: {e}")
            return {"nodes": [], "links": []}

    def get_graph_insights(self) -> dict:
        if not self.driver:
            return {
              "impact_probability": "High",
              "top_node": "DOM Root",
              "component_id": "root",
              "reach": 0,
              "violations_prevented": 0,
              "structural_complexity": "O(1)",
              "recommended": True,
              "specific_fix": "None"
            }
        try:
            with self.driver.session() as session:
                counts_query = """
                OPTIONAL MATCH (p:Page) WITH count(p) as page_count
                OPTIONAL MATCH (c:Component) WITH page_count, count(c) as component_count
                OPTIONAL MATCH (v:Violation) WITH page_count, component_count, count(v) as violation_count
                RETURN page_count, component_count, violation_count
                """
                res = session.run(counts_query)
                record = res.single()
                if record:
                    page_count = record["page_count"] or 0
                    component_count = record["component_count"] or 0
                    violation_count = record["violation_count"] or 0
                else:
                    page_count, component_count, violation_count = 0, 0, 0

                top_node_query = """
                MATCH (c:Component)<-[:PAGE_CONTAINS]-(p:Page)
                WITH c, count(p) as page_reach
                ORDER BY page_reach DESC LIMIT 1
                RETURN c.snippet as snippet, c.id as footprint, page_reach
                """
                res2 = session.run(top_node_query)
                record2 = res2.single()
                if record2:
                    top_node = record2["snippet"] or "Dynamic Component"
                    if len(top_node) > 30:
                        top_node = top_node[:30] + "..."
                    component_id = record2["footprint"]
                    reach = record2["page_reach"]
                else:
                    top_node = "DOM Root"
                    component_id = "root"
                    reach = 0

                impact_prob = "Critical" if violation_count > 10 else ("Moderate" if violation_count > 0 else "Low")
                
                return {
                  "impact_probability": impact_prob,
                  "top_node": top_node,
                  "component_id": component_id,
                  "reach": reach,
                  "violations_prevented": violation_count,
                  "structural_complexity": f"O({component_count * max(1, page_count)})",
                  "recommended": violation_count > 0,
                  "specific_fix": "Patch core template component to fix child tree."
                }
        except Exception as e:
            self.logger.exception("Error fetching Neo4j graph insights")
            return {
              "impact_probability": "Unknown",
              "top_node": "Error",
              "component_id": "Error",
              "reach": 0,
              "violations_prevented": 0,
              "structural_complexity": "O(1)",
              "recommended": False,
              "specific_fix": ""
            }

    async def upsert_page_links_batch_async(self, batch: List[dict]):
        if not self.driver or not batch:
            return
        async with self._semaphore:
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(
                        self._upsert_page_links_batch_sync,
                        batch
                    ),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Neo4j API Timeout: Page links batch upsert skipped.")
            except Exception as e:
                self.logger.exception("Async Page Links Batch Error")

    def _upsert_page_links_batch_sync(self, batch: List[dict]):
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                query = """
                UNWIND $batch AS item
                MERGE (d:Domain {url: item.domain_url})
                MERGE (s:Page {url: item.source_url})
                MERGE (t:Page {url: item.target_url})
                MERGE (d)-[:DOMAIN_OWNS_PAGE]->(s)
                MERGE (s)-[:PAGE_LINKS_TO]->(t)
                """
                session.run(query, batch=batch)
        except Exception as e:
            self.logger.exception("Sync Page Links Batch Error")

    async def upsert_component_violations_batch_async(self, batch: List[dict]):
        if not self.driver or not batch:
            return
        async with self._semaphore:
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(
                        self._upsert_component_violations_batch_sync,
                        batch
                    ),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Neo4j API Timeout: Component batch upsert skipped.")
            except Exception as e:
                self.logger.exception("Async Component Batch Error")

    def _upsert_component_violations_batch_sync(self, batch: List[dict]):
        if not self.driver:
            return
        try:
            params = []
            for item in batch:
                page_url = item["page_url"]
                rule_id = item["rule_id"]
                impact = item["impact"]
                node_html = item["node_html"]
                
                footprint = hashlib.sha256(node_html.encode("utf-8")).hexdigest()
                snippet_preview = node_html[:150]

                standard_id = "WCAG-2.2"
                if ".gov.in" in page_url or ".nic.in" in page_url:
                    standard_id = "GIGW-3.0"
                elif "bank" in page_url or "sbi" in page_url or "hdfc" in page_url:
                    standard_id = "RBI-Master-Circular"

                params.append({
                    "page_url": page_url,
                    "footprint": footprint,
                    "snippet_preview": snippet_preview,
                    "rule_id": rule_id,
                    "impact_val": impact,
                    "standard_id": standard_id
                })

            with self.driver.session() as session:
                query = """
                UNWIND $batch AS item
                MERGE (p:Page {url: item.page_url})
                MERGE (c:Component {id: item.footprint})
                ON CREATE SET c.footprint_hash = item.footprint, c.snippet = item.snippet_preview
                MERGE (v:Violation {id: item.rule_id})
                ON CREATE SET v.rule_id = item.rule_id, v.impact = item.impact_val
                MERGE (s:ComplianceStandard {id: item.standard_id})
                ON CREATE SET s.name = item.standard_id

                MERGE (p)-[:PAGE_CONTAINS]->(c)
                MERGE (c)-[:COMPONENT_TRIGGERS]->(v)
                MERGE (v)-[:VIOLATION_FAILS]->(s)
                """
                session.run(query, batch=params)
        except Exception as e:
            self.logger.exception("Sync Component Batch Error")


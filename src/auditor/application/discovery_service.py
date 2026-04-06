"""
AUDITOR DISCOVERY SERVICE (S-Z10)
=================================

Role: Orchestration of autonomous target discovery.
Responsibilities:
  - Coordinating Robots.txt and Sitemap investigation.
  - Filtering URLs based on adherence metadata.
  - Pushing validated targets to the Redis cluster.
"""

from typing import List, Set
from itertools import islice
from auditor.domain.target_repository import ITargetRepository # type: ignore
from auditor.domain.models import AuditTarget # type: ignore
from auditor.domain.sitemap_discovery import SitemapDiscoveryEngine # type: ignore
from auditor.domain.robots_engine import RobotsAdherenceEngine # type: ignore
from auditor.domain.crawler import LinkDiscoveryService # type: ignore
from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

class DiscoveryService:
    """
    High-level orchestrator for autonomous audit target discovery.
    """
    
    def __init__(self, redis_queue: RedisTaskQueue, crawler_service: LinkDiscoveryService, target_repository: ITargetRepository):
        self.sitemap_engine = SitemapDiscoveryEngine()
        self.robots_engine = RobotsAdherenceEngine()
        self.crawler = crawler_service
        self.queue = redis_queue
        self.target_repo = target_repository
        self.logger = auditor_logger.getChild("DiscoveryService")

    async def run_discovery_session(self, base_url: str):
        """Discovers and dispatches all permissible URLs from the target domain."""
        self.logger.info(f"--- [ INITIATING AUTONOMOUS DISCOVERY: {base_url} ] ---")
        
        # 1. Initialize Robots Adherence
        await self.robots_engine.initialize(base_url)
        
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        root_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # 2. Extract Sitemaps
        sitemaps = self.robots_engine.get_sitemaps()
        if not sitemaps:
            # Fallback to standard sitemap.xml if not in robots.txt
            sitemaps = [f"{root_url}/sitemap.xml"]
            
        all_discovered: Set[str] = set()
        for sitemap_url in sitemaps:
            urls = await self.sitemap_engine.discover_urls(sitemap_url)
            all_discovered.update(urls)
            
        # 3. Fallback: Recursive Link Crawling (Cycle 1)
        if not all_discovered:
            self.logger.warning(f"Sitemap discovery zeroed on {base_url}. BRIDGING GAP via RECURSIVE FALLBACK.")
            fallback_urls: List[str] = await self.crawler.extract_links(base_url)
            self.logger.info(f"Recursive Mission Successful: Extracted {len(fallback_urls)} targets through anti-bot shielding.")
            if fallback_urls:
                 sample_targets = list(islice(fallback_urls, 5))
                 self.logger.debug(f"Fallback Sample: {sample_targets}")
            all_discovered.update(fallback_urls)
            
        # 4. Filter and Dispatch
        metrics = {"dispatched": 0, "filtered": 0}
        for url in all_discovered:
            if self.robots_engine.is_allowed(url):
                # Phase XIII: Persistent Discovery
                try:
                    target = AuditTarget(url=url)
                    await self.target_repo.add_domain(target)
                except Exception:
                    self.logger.debug(f"Target already exists in ledger: {url}")
                
                await self.queue.push_task("single_url_audit", {"url": url})
                metrics["dispatched"] += 1
            else:
                metrics["filtered"] += 1
                if metrics["filtered"] <= 5:
                    self.logger.info(f"Discovery Filtered: {url} (Blocked by Robots compliance)")

        if metrics["filtered"] > 0:
            self.logger.warning(f"Compliance Filter active: Blocked {metrics['filtered']} mission targets.")
                
        self.logger.info(f"--- [ DISCOVERY MISSION COMPLETE: Dispatched {metrics['dispatched']} tasks ] ---")
        return {"dispatched": metrics["dispatched"], "discovered": len(all_discovered)}

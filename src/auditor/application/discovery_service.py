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
from auditor.domain.sitemap_discovery import SitemapDiscoveryEngine # type: ignore
from auditor.domain.robots_engine import RobotsAdherenceEngine # type: ignore
from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

class DiscoveryService:
    """
    High-level orchestrator for autonomous audit target discovery.
    """
    
    def __init__(self, redis_queue: RedisTaskQueue):
        self.sitemap_engine = SitemapDiscoveryEngine()
        self.robots_engine = RobotsAdherenceEngine()
        self.queue = redis_queue
        self.logger = auditor_logger.getChild("DiscoveryService")

    async def run_discovery_session(self, base_url: str):
        """Discovers and dispatches all permissible URLs from the target domain."""
        self.logger.info(f"--- [ INITIATING AUTONOMOUS DISCOVERY: {base_url} ] ---")
        
        # 1. Initialize Robots Adherence
        await self.robots_engine.initialize(base_url)
        
        # 2. Extract Sitemaps
        sitemaps = self.robots_engine.get_sitemaps()
        if not sitemaps:
            # Fallback to standard sitemap.xml if not in robots.txt
            sitemaps = [f"{base_url.rstrip('/')}/sitemap.xml"]
            
        all_discovered: Set[str] = set()
        for sitemap_url in sitemaps:
            urls = await self.sitemap_engine.discover_urls(sitemap_url)
            all_discovered.update(urls)
            
        # 3. Filter and Dispatch
        dispatch_count = 0
        for url in all_discovered:
            if self.robots_engine.is_allowed(url):
                await self.queue.push_task("full_site_audit", {"url": url})
                dispatch_count += 1
            else:
                self.logger.debug(f"Discovery Filtered: {url} (Blocked by Robots.txt)")
                
        self.logger.info(f"--- [ DISCOVERY MISSION COMPLETE: Dispatched {dispatch_count} tasks ] ---")
        return {"dispatched": dispatch_count, "discovered": len(all_discovered)}

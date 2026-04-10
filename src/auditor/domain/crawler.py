import os
import sys

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from abc import ABC, abstractmethod
from typing import List, Set
from urllib.parse import urlparse, urljoin

class ILinkExtractor(ABC):
    """Port for extracting internal links from a page."""
    
    @abstractmethod
    async def extract_links(self, url: str) -> List[str]:
        """Navigate to URL and return all unique internal links."""
        return []

class LinkDiscoveryService:
    """Domain Service to manage the discovery and queueing of URLs for auditing."""
    
    def __init__(self, link_extractor: ILinkExtractor):
        self.link_extractor = link_extractor
        self.visited: Set[str] = set()
        self.queue: List[str] = []

    def is_internal(self, base_url: str, target_url: str) -> bool:
        """Verify if target_url belongs to the same domain as base_url (advanced matching)."""
        base_netloc = urlparse(base_url).netloc.lower()
        target_netloc = urlparse(target_url).netloc.lower()
        
        # Strip www. for canonical domain comparison
        base_clean = base_netloc.replace("www.", "")
        target_clean = target_netloc.replace("www.", "")
        
        if not target_netloc:
            return True
            
        # Match if domains are identical after cleaning, or if target is a subdomain
        return base_clean == target_clean or target_netloc.endswith(f".{base_clean}")

    def normalize_url(self, base_url: str, target_url: str) -> str:
        """Normalize target_url relative to base_url."""
        # Remove fragments and queries for canonical discovery
        absolute_url = urljoin(base_url, target_url)
        parsed = urlparse(absolute_url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    async def extract_links(self, url: str) -> List[str]:
        """Perform discovery and extraction on a single URL."""
        raw_links = await self.link_extractor.extract_links(url)
        unique_internal = []
        
        for link in raw_links:
            normalized = self.normalize_url(url, link)
            if self.is_internal(url, normalized) and normalized not in self.visited:
                unique_internal.append(normalized)
        
        return unique_internal

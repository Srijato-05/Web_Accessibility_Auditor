from abc import ABC, abstractmethod
from typing import List, Set
from urllib.parse import urlparse, urljoin

class ILinkExtractor(ABC):
    """Port for extracting internal links from a page."""
    
    @abstractmethod
    async def extract_links(self, url: str) -> List[str]:
        """Navigate to URL and return all unique internal links."""
        pass

class LinkDiscoveryService:
    """Domain Service to manage the discovery and queueing of URLs for auditing."""
    
    def __init__(self, link_extractor: ILinkExtractor):
        self.link_extractor = link_extractor
        self.visited: Set[str] = set()
        self.queue: List[str] = []

    def is_internal(self, base_url: str, target_url: str) -> bool:
        """Verify if target_url belongs to the same domain as base_url."""
        base_domain = urlparse(base_url).netloc
        target_domain = urlparse(target_url).netloc
        return base_domain == target_domain or not target_domain

    def normalize_url(self, base_url: str, target_url: str) -> str:
        """Normalize target_url relative to base_url."""
        # Remove fragments and queries for canonical discovery
        absolute_url = urljoin(base_url, target_url)
        parsed = urlparse(absolute_url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    async def discover_links(self, url: str) -> List[str]:
        """Perform discovery on a single URL."""
        raw_links = await self.link_extractor.extract_links(url)
        unique_internal = []
        
        for link in raw_links:
            normalized = self.normalize_url(url, link)
            if self.is_internal(url, normalized) and normalized not in self.visited:
                unique_internal.append(normalized)
        
        return unique_internal

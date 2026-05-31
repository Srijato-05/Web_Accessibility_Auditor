import pytest
from uuid import uuid4
from datetime import datetime
from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.models import AuditTarget, DomainStatus
from auditor.domain.crawler import ILinkExtractor, LinkDiscoveryService
from auditor.domain.interfaces import IBrowserEngine, IAuditRepository
from auditor.domain.target_repository import ITargetRepository

def test_audit_session_exceptions():
    session = AuditSession(target_url="https://example.com")
    # Start twice to trigger ValueError
    session.start()
    with pytest.raises(ValueError):
        session.start()
        
    # Complete session twice to trigger ValueError
    session.complete()
    with pytest.raises(ValueError):
        session.complete()
        
    # Fail session
    session.fail("Some error")
    assert session.status == SessionStatus.FAILED
    assert session.error_message == "Some error"

def test_audit_target():
    target = AuditTarget(url="https://example.com")
    target.mark_crawling()
    assert target.status == DomainStatus.CRAWLING
    target.mark_active()
    assert target.status == DomainStatus.ACTIVE
    assert isinstance(target.last_audit_at, datetime)
    target.mark_failed("Network timeout")
    assert target.status == DomainStatus.FAILED

class DummyLinkExtractor(ILinkExtractor):
    async def extract_links(self, url: str):
        # Trigger abstract base method fallback
        return await super().extract_links(url)

@pytest.mark.asyncio
async def test_crawler_interfaces_and_helpers():
    extractor = DummyLinkExtractor()
    res = await extractor.extract_links("https://example.com")
    assert res == []
    
    discovery = LinkDiscoveryService(extractor)
    # Target netloc empty (relative path check)
    assert discovery.is_internal("https://example.com", "/relative-path") is True
    
    # Non-internal domain check
    assert discovery.is_internal("https://example.com", "https://google.com") is False

class DummyBrowserEngine(IBrowserEngine):
    async def scan_url(self, url: str):
        return await super().scan_url(url)

class DummyAuditRepository(IAuditRepository):
    async def save_session(self, session: AuditSession):
        pass
    async def get_session(self, session_id):
        pass
    async def save_violations(self, violations):
        pass
    async def list_recent_sessions(self, limit):
        return await super().list_recent_sessions(limit)

class DummyTargetRepository(ITargetRepository):
    async def add_domain(self, domain):
        pass
    async def get_active_domains(self):
        return await super().get_active_domains()
    async def update_domain(self, domain):
        pass

@pytest.mark.asyncio
async def test_interfaces_fallbacks():
    be = DummyBrowserEngine()
    assert await be.scan_url("https://example.com") == []
    
    ar = DummyAuditRepository()
    assert await ar.list_recent_sessions(5) == []
    
    tr = DummyTargetRepository()
    assert await tr.get_active_domains() == []

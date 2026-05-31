import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.application.crawl_service import CrawlService
from auditor.domain.audit_session import AuditSession, SessionStatus
from auditor.domain.exceptions import AuditFailedError

@pytest.mark.asyncio
async def test_crawl_service_page_links_batching():
    # Setup mocks
    audit_service = MagicMock()
    audit_service.repository = MagicMock()
    audit_service.repository.save_session = AsyncMock()
    audit_service.repository.save_violations = AsyncMock()
    audit_service.repository.db_session = MagicMock()
    audit_service.repository.db_session.commit = AsyncMock()
    crawler_service = MagicMock()
    
    mock_session = MagicMock()
    mock_session.status.value = "completed"
    mock_session.id = "test-session-id"
    
    audit_service.execute_audit = AsyncMock(return_value=mock_session)
    crawler_service.extract_links = AsyncMock(side_effect=[
        ["https://example.com/about", "https://example.com/contact"], # Page 1 returns two links
        [], # Page 2 returns no links
        []  # Page 3 returns no links
    ])
    
    # Instantiate CrawlService
    crawl_service = CrawlService(
        audit_service=audit_service,
        crawler_service=crawler_service,
        max_depth=2,
        max_pages=3,
        concurrency=1
    )
    # Mock Neo4j repository methods
    crawl_service.tg_repo = MagicMock()
    crawl_service.tg_repo.upsert_page_links_batch_async = AsyncMock()
    
    # Run crawl
    with patch.object(crawl_service, "audit_service", audit_service), \
         patch.object(crawl_service, "crawler_service", crawler_service), \
         patch("auditor.application.crawl_service.AuditReporter", return_value=MagicMock(generate_summary_report=AsyncMock())):
        
        await crawl_service.run("https://example.com")
        
        # Verify batching: upsert_page_links_batch_async should be called once with correct parameters
        crawl_service.tg_repo.upsert_page_links_batch_async.assert_called_once()
        batch_arg = crawl_service.tg_repo.upsert_page_links_batch_async.call_args[0][0]
        
        assert len(batch_arg) == 2
        assert batch_arg[0]["source_url"] == "https://example.com"
        assert batch_arg[0]["target_url"] == "https://example.com/about"
        assert batch_arg[0]["domain_url"] == "https://example.com"

@pytest.mark.asyncio
async def test_crawl_service_filtering_and_errors():
    from auditor.infrastructure.data_extractor import PageData, ElementData
    from auditor.domain.violation import Violation, ImpactLevel
    from uuid import uuid4
    
    audit_service = MagicMock()
    audit_service.repository = MagicMock()
    audit_service.repository.save_session = AsyncMock()
    audit_service.repository.save_violations = AsyncMock()
    audit_service.repository.db_session = MagicMock() # db_session commit path
    
    crawler_service = MagicMock()
    crawler_service.extract_links = AsyncMock(return_value=["https://example.com/other", "https://external.com"])
    
    crawl_service = CrawlService(
        audit_service=audit_service,
        crawler_service=crawler_service,
        max_depth=2,
        max_pages=10,
        concurrency=2
    )
    crawl_service.tg_repo = MagicMock()
    crawl_service.tg_repo.upsert_page_links_batch_async = AsyncMock()
    
    # 1. Test helper methods
    assert crawl_service._normalize_url("https://example.com/page/") == "https://example.com/page"
    assert crawl_service._is_internal("https://example.com", "https://example.com/about") is True
    assert crawl_service._is_internal("https://example.com", "https://other.com/about") is False
    assert crawl_service._is_asset_filtered("https://example.com/style.css") is True
    assert crawl_service._is_asset_filtered("https://example.com/about") is False
    
    # 2. Test run loop with a mixture of filtering, depth limit, AuditFailedError, and general exceptions
    v = Violation(
        rule_id="img-alt", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="", session_id=uuid4(), tags=[], compliance_level="", category="", severity_matrix="", url="https://example.com"
    )
    s = AuditSession(target_url="https://example.com")
    s.status = SessionStatus.COMPLETED
    s.violations = [v]
    
    # Second call (https://example.com/other): raises AuditFailedError
    # Third call (https://example.com/failed): raises Exception
    audit_service.execute_audit = AsyncMock(side_effect=[
        s,
        AuditFailedError("Audit failed"),
        RuntimeError("Unknown crash")
    ])
    
    queue = asyncio.PriorityQueue()
    await queue.put((0, "https://example.com", 0))
    await queue.put((30, "https://example.com/too-deep", 3))
    await queue.put((10, "https://example.com/image.png", 1))
    await queue.put((10, "https://example.com/other", 1))
    await queue.put((10, "https://example.com/failed", 1))
    
    with patch("auditor.application.crawl_service.AuditReporter", MagicMock()):
        tasks = []
        while not queue.empty():
            priority, url, depth = await queue.get()
            if depth > crawl_service.max_depth:
                continue
            if crawl_service._is_asset_filtered(url):
                crawl_service.filtered_count += 1
                continue
            crawl_service.discovered_count += 1
            task = asyncio.create_task(crawl_service._process_audit_session(url, depth, queue))
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
        assert crawl_service.filtered_count == 1
        assert crawl_service.success_count == 1
        assert crawl_service.failed_count == 2


@pytest.mark.asyncio
async def test_crawl_service_run_success_with_violations():
    from auditor.domain.violation import Violation, ImpactLevel
    from uuid import uuid4
    
    audit_service = MagicMock()
    audit_service.repository = MagicMock()
    audit_service.repository.save_session = AsyncMock()
    audit_service.repository.save_violations = AsyncMock()
    audit_service.repository.db_session = MagicMock()
    audit_service.repository.db_session.commit = AsyncMock()
    
    crawler_service = MagicMock()
    crawler_service.extract_links = AsyncMock(return_value=["https://example.com/about"])
    
    v = Violation(
        rule_id="img-alt", impact=ImpactLevel.MINOR, agent="visual", description="desc", help_url="", session_id=uuid4(), tags=[], compliance_level="", category="", severity_matrix="", url="https://example.com"
    )
    s = AuditSession(target_url="https://example.com")
    s.status = SessionStatus.COMPLETED
    s.violations = [v]
    
    audit_service.execute_audit = AsyncMock(return_value=s)
    
    crawl_service = CrawlService(
        audit_service=audit_service,
        crawler_service=crawler_service,
        max_depth=1,
        max_pages=2,
        concurrency=1
    )
    crawl_service.tg_repo = MagicMock()
    crawl_service.tg_repo.upsert_page_links_batch_async = AsyncMock()
    
    mock_reporter = MagicMock()
    mock_reporter.generate_summary_report = AsyncMock()
    with patch("auditor.application.crawl_service.AuditReporter", return_value=mock_reporter):
        master = await crawl_service.run("https://example.com")
        assert master is not None
        assert master.status == SessionStatus.COMPLETED
        assert len(master.violations) > 0


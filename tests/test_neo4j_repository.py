import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch
from auditor.infrastructure.neo4j_repository import Neo4jRepository
from neo4j.exceptions import ServiceUnavailable, CypherSyntaxError

@pytest.mark.asyncio
async def test_upsert_page_links_batch_sync(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    batch = [
        {"domain_url": "https://example.com", "source_url": "https://example.com/page1", "target_url": "https://example.com/page2"},
        {"domain_url": "https://example.com", "source_url": "https://example.com/page2", "target_url": "https://example.com/page3"}
    ]
    
    repo._upsert_page_links_batch_sync(batch)
    
    session = mock_neo4j_driver.session()
    session.run.assert_called_once()
    args, kwargs = session.run.call_args
    assert "UNWIND $batch AS item" in args[0]
    assert "PAGE_LINKS_TO" in args[0]
    assert kwargs["batch"] == batch

@pytest.mark.asyncio
async def test_upsert_component_violations_batch_sync(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    batch = [
        {
            "page_url": "https://example.gov.in/home",
            "rule_id": "image-alt",
            "impact": "critical",
            "node_html": '<img src="test.jpg" />'
        },
        {
            "page_url": "https://example.com/bank-login",
            "rule_id": "color-contrast",
            "impact": "serious",
            "node_html": '<div class="btn">Login</div>'
        }
    ]
    
    repo._upsert_component_violations_batch_sync(batch)
    
    session = mock_neo4j_driver.session()
    session.run.assert_called_once()
    args, kwargs = session.run.call_args
    assert "UNWIND $batch AS item" in args[0]
    assert "ComplianceStandard" in args[0]
    
    params = kwargs["batch"]
    assert len(params) == 2
    assert params[0]["standard_id"] == "GIGW-3.0"
    assert params[1]["standard_id"] == "RBI-Master-Circular"

@pytest.mark.asyncio
async def test_upsert_page_links_batch_async_timeout():
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    
    async def mock_wait_for(coro, timeout):
        coro.close()
        raise asyncio.TimeoutError()
        
    with patch("asyncio.wait_for", side_effect=mock_wait_for), \
         patch.object(repo.logger, "warning") as mock_warn:
        await repo.upsert_page_links_batch_async([{"dummy": "data"}])
        mock_warn.assert_called_once_with("Neo4j API Timeout: Page links batch upsert skipped.")

@pytest.mark.asyncio
async def test_neo4j_service_unavailable(mock_neo4j_driver):
    """Verifies that transient Neo4j driver connection drop exceptions do not crash the service thread."""
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    session = mock_neo4j_driver.session()
    # Simulate a connection drop / offline DB
    session.run.side_effect = ServiceUnavailable("Neo4j Bolt connection refused")
    
    with patch.object(repo.logger, "exception") as mock_exc:
        repo._upsert_page_links_batch_sync([{"dummy": "data"}])
        mock_exc.assert_called_once()
        assert "Sync Page Links Batch Error" in mock_exc.call_args[0][0]

@pytest.mark.asyncio
async def test_neo4j_cypher_syntax_error(mock_neo4j_driver):
    """Verifies that query execution syntax errors are caught, logged, and return gracefully."""
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    session = mock_neo4j_driver.session()
    session.run.side_effect = CypherSyntaxError("Invalid UNWIND schema syntax")
    
    with patch.object(repo.logger, "exception") as mock_exc:
        repo._upsert_component_violations_batch_sync([{"page_url": "http://test.com", "rule_id": "test", "impact": "low", "node_html": "<div>"}])
        mock_exc.assert_called_once()
        assert "Sync Component Batch Error" in mock_exc.call_args[0][0]

def test_neo4j_init_missing_lib():
    with patch("auditor.infrastructure.neo4j_repository.GraphDatabase", None), \
         patch("auditor.infrastructure.neo4j_repository.auditor_logger.getChild") as mock_get_child:
        mock_log = MagicMock()
        mock_get_child.return_value = mock_log
        repo = Neo4jRepository()
        assert repo.driver is None
        mock_log.warning.assert_called_with("Neo4j library not installed. Repository running offline.")

def test_neo4j_init_missing_password():
    with patch("os.getenv", side_effect=lambda k, d=None: "" if k == "NEO4J_PASSWORD" else d), \
         patch("auditor.infrastructure.neo4j_repository.auditor_logger.getChild") as mock_get_child:
        mock_log = MagicMock()
        mock_get_child.return_value = mock_log
        repo = Neo4jRepository()
        assert repo.driver is None
        mock_log.warning.assert_called_with("Neo4j password missing in environment. Repository running offline.")

def test_neo4j_init_connection_fail():
    mock_driver_func = MagicMock(side_effect=Exception("Connection refused"))
    with patch("os.getenv", return_value="some_password"), \
         patch("auditor.infrastructure.neo4j_repository.GraphDatabase.driver", mock_driver_func), \
         patch("auditor.infrastructure.neo4j_repository.auditor_logger.getChild") as mock_get_child:
        mock_log = MagicMock()
        mock_get_child.return_value = mock_log
        repo = Neo4jRepository()
        assert repo.driver is None
        mock_log.error.assert_called()

def test_neo4j_close_and_ping(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    assert repo.ping() is True
    repo.close()
    mock_neo4j_driver.close.assert_called_once()
    
    # Test ping on connection fail
    mock_neo4j_driver.verify_connectivity.side_effect = Exception("Ping failed")
    assert repo.ping() is False

@pytest.mark.asyncio
async def test_neo4j_upsert_page_link(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    await repo.upsert_page_link_async("http://source", "http://target", "http://domain")
    session = mock_neo4j_driver.session()
    session.run.assert_called_once()
    args, kwargs = session.run.call_args
    assert "MERGE (d:Domain {url: $domain_url})" in args[0]

@pytest.mark.asyncio
async def test_neo4j_upsert_component_violation(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    from auditor.domain.violation import Violation, ImpactLevel
    from uuid import uuid4
    violation = Violation(
        rule_id="image-alt",
        impact=ImpactLevel.CRITICAL,
        agent="axe",
        description="Missing alt",
        help_url="http://help",
        session_id=uuid4(),
        tags=[],
        compliance_level="A",
        category="perceivable",
        severity_matrix="High",
        url="http://page"
    )
    
    await repo.upsert_component_violation_async("http://page", violation, "<img>")
    session = mock_neo4j_driver.session()
    session.run.assert_called_once()
    args, kwargs = session.run.call_args
    assert "MERGE (c:Component {id: $footprint})" in args[0]

def test_neo4j_get_graph_data(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    # Mock records returned by session.run
    mock_n = MagicMock()
    mock_n.labels = {"Page"}
    mock_n.get.side_effect = lambda k: "http://test.com" if k == "url" else None
    mock_n.element_id = "node1"
    
    mock_m = MagicMock()
    mock_m.labels = {"ComplianceStandard"}
    mock_m.get.side_effect = lambda k: "GIGW-3.0" if k == "id" else ("GIGW" if k == "name" else None)
    mock_m.element_id = "node2"
    
    mock_r = MagicMock()
    
    mock_record1 = {"n": mock_n, "r": mock_r, "m": mock_m}
    mock_record2 = {"n": mock_m, "r": None, "m": None}
    
    session = mock_neo4j_driver.session()
    session.run.return_value = [mock_record1, mock_record2]
    
    data = repo.get_graph_data()
    assert len(data["nodes"]) == 2
    assert len(data["links"]) == 1

def test_neo4j_get_graph_insights(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    session = mock_neo4j_driver.session()
    
    mock_counts_record = MagicMock()
    mock_counts_record.get.side_effect = lambda k: 2 if k in ("page_count", "component_count", "violation_count") else None
    mock_counts_record.__getitem__.side_effect = lambda k: 2 if k in ("page_count", "component_count", "violation_count") else None
    
    mock_top_record = MagicMock()
    mock_top_record.get.side_effect = lambda k: "<img>" if k == "snippet" else ("footprint" if k == "footprint" else 2)
    mock_top_record.__getitem__.side_effect = lambda k: "<img>" if k == "snippet" else ("footprint" if k == "footprint" else 2)
    
    # session.run calls: first counts_query, second top_node_query
    mock_counts_res = MagicMock()
    mock_counts_res.single.return_value = mock_counts_record
    
    mock_top_res = MagicMock()
    mock_top_res.single.return_value = mock_top_record
    
    session.run.side_effect = [mock_counts_res, mock_top_res]
    
    insights = repo.get_graph_insights()
    assert insights["top_node"] == "<img>"
    assert insights["reach"] == 2
    assert insights["violations_prevented"] == 2

@pytest.mark.asyncio
async def test_neo4j_async_timeouts_and_errors(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    async def mock_wait_for(coro, timeout):
        raise asyncio.TimeoutError()
        
    with patch("asyncio.wait_for", side_effect=mock_wait_for):
        # Component upsert timeout
        from auditor.domain.violation import Violation, ImpactLevel
        from uuid import uuid4
        violation = Violation(
            rule_id="image-alt", impact=ImpactLevel.CRITICAL, agent="axe",
            description="Missing alt", help_url="http://help", session_id=uuid4(),
            tags=[], compliance_level="A", category="perceivable", severity_matrix="High", url="http://page"
        )
        await repo.upsert_component_violation_async("http://page", violation, "<img>")
        
        # Component batch timeout
        await repo.upsert_component_violations_batch_async([{"page_url": "http://page", "rule_id": "image-alt", "impact": "critical", "node_html": "<img>"}])


@pytest.mark.asyncio
async def test_neo4j_init_connection_scenarios():
    mock_driver = MagicMock()
    with patch("neo4j.GraphDatabase.driver", return_value=mock_driver) as mock_drv_cls, \
         patch.dict(os.environ, {"NEO4J_PASSWORD": "test_password"}):
        repo = Neo4jRepository()
        assert repo.driver == mock_driver
        mock_driver.verify_connectivity.assert_called_once()
        
    with patch("neo4j.GraphDatabase.driver", side_effect=Exception("Connection refused")), \
         patch.dict(os.environ, {"NEO4J_PASSWORD": "test_password"}):
        repo = Neo4jRepository()
        assert repo.driver is None


@pytest.mark.asyncio
async def test_neo4j_ping(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    assert repo.ping() is True
    
    mock_neo4j_driver.verify_connectivity.side_effect = Exception("Offline")
    assert repo.ping() is False
    
    repo.driver = None
    assert repo.ping() is False


@pytest.mark.asyncio
async def test_neo4j_async_success_paths(mock_neo4j_driver):
    repo = Neo4jRepository()
    repo.driver = mock_neo4j_driver
    
    await repo.upsert_page_link_async("https://site.com/a", "https://site.com/b", "https://site.com")
    session = mock_neo4j_driver.session()
    session.run.assert_called_once()
    session.run.reset_mock()
    
    from auditor.domain.violation import Violation, ImpactLevel
    from uuid import uuid4
    v = Violation(
        rule_id="img-alt", impact=ImpactLevel.MINOR, agent="axe", description="desc",
        help_url="http", session_id=uuid4(), tags=[], compliance_level="A",
        category="p", severity_matrix="Low", url="http"
    )
    await repo.upsert_component_violation_async("https://site.com/a", v, "<img>")
    session.run.assert_called_once()
    session.run.reset_mock()


@pytest.mark.asyncio
async def test_neo4j_no_driver_bypass():
    repo = Neo4jRepository()
    repo.driver = None
    
    await repo.upsert_page_link_async("https://a.com", "https://b.com", "https://a.com")
    repo._upsert_page_link_sync("https://a.com", "https://b.com", "https://a.com")
    
    from auditor.domain.violation import Violation, ImpactLevel
    from uuid import uuid4
    v = Violation(
        rule_id="img-alt", impact=ImpactLevel.MINOR, agent="axe", description="desc",
        help_url="http", session_id=uuid4(), tags=[], compliance_level="A",
        category="p", severity_matrix="Low", url="http"
    )
    await repo.upsert_component_violation_async("https://a.com", v, "<img>")
    repo._upsert_component_violation_sync("https://a.com", v, "<img>")
    
    repo.close()



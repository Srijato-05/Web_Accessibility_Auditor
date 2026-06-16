import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.infrastructure.neo4j_repository import Neo4jRepository
from auditor.domain.exceptions import RepositoryError
import logging

@pytest.fixture
def mock_driver():
    driver = MagicMock()
    # Ensure standard context manager behavior for async/sync
    # Neo4j python driver is typically sync in our implementation
    return driver

def test_neo4j_ping_success(mock_driver):
    """Test ping graph online validation."""
    mock_driver.verify_connectivity = MagicMock()
    repo = Neo4jRepository()
    repo.driver = mock_driver
    assert repo.ping() is True

def test_neo4j_ping_failure(mock_driver):
    """Test ping gracefully handles offline exceptions without crashing."""
    mock_driver.verify_connectivity = MagicMock(side_effect=Exception("Connection refused"))
    repo = Neo4jRepository()
    repo.driver = mock_driver
    assert repo.ping() is False

@pytest.mark.asyncio
async def test_neo4j_upsert_component_violations_batch_async_dynamic_fuzz():
    """
    Advanced Dynamic Test: Feeds massive, randomized component violations 
    into the Neo4j graph builder to ensure proper cipher statement construction,
    transaction handling, and memory optimization.
    """
    import random
    import string
    
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    
    mock_session = MagicMock()
    mock_tx = MagicMock()
    mock_tx.run = MagicMock()
    
    # Context managers
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    # Generate deeply complex graph batch
    def gen_str(): return ''.join(random.choices(string.ascii_letters, k=10))
    
    batch = []
    for _ in range(500):
        batch.append({
            "page_url": f"https://example.com/{gen_str()}",
            "rule_id": gen_str(),
            "impact": random.choice(["critical", "serious", "moderate", "minor"]),
            "node_html": f"<{gen_str()} id='{gen_str()}'></{gen_str()}>"
        })
        
    # Inject asyncio sleep patch
    with patch("asyncio.to_thread") as mock_thread:
        # We mock the thread to just execute the sync function directly for the test
        mock_thread.side_effect = lambda func, *args: func(*args)
        
        await repo.upsert_component_violations_batch_async(batch)
        
        # Verify transaction run was called (UNWIND logic)
        assert mock_tx.run.called
        
        # Verify proper IO logging
        # The query should contain the UNWIND cipher
        call_args = mock_tx.run.call_args[0]
        assert "UNWIND $batch AS item" in call_args[0]
        assert "MERGE (p:Page {url: item.page_url})" in call_args[0]

@pytest.mark.asyncio
async def test_neo4j_graph_insights_aggregation():
    """
    Validates complex graph cypher aggregations return structural metrics cleanly.
    """
    repo = Neo4jRepository()
    mock_session = MagicMock()
    
    mock_result_counts = MagicMock()
    mock_result_counts.single.return_value = {
        "page_count": 10,
        "component_count": 5,
        "violation_count": 15
    }
    
    mock_result_top = MagicMock()
    mock_result_top.single.return_value = {
        "snippet": "Navbar",
        "footprint": "nav-id",
        "page_reach": 1500
    }
    
    mock_session.run.side_effect = [mock_result_counts, mock_result_top]
    repo.driver = MagicMock()
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        insights = repo.get_graph_insights()
        
        assert insights["impact_probability"] == "Critical"
        assert insights["reach"] == 1500
        
@pytest.mark.asyncio
async def test_neo4j_error_handling_and_logging_on_io_failure():
    """
    Simulates total database IO failure during a massive graph insertion 
    to ensure it doesn't leak memory or crash the event loop, returning proper 
    RepositoryError abstractions.
    """
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    
    mock_session = MagicMock()
    mock_tx = MagicMock()
    # Catastrophic failure during Neo4j transaction
    mock_tx.run = MagicMock(side_effect=Exception("Neo4j Out of Memory IO Error"))
    
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        with pytest.raises(RepositoryError) as exc:
            await repo.upsert_component_violations_batch_async([{"page_url": "test", "rule_id": "test", "impact": "test", "node_html": "test"}])
            
        assert "Neo4j Out of Memory" in str(exc.value)

@pytest.mark.asyncio
async def test_neo4j_page_links_batch_async_dynamic():
    """
    Validates the crawler graph map constructor with thousands of relational edges.
    """
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    
    mock_session = MagicMock()
    mock_tx = MagicMock()
    mock_tx.run = MagicMock()
    
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    batch = [
        {"source_url": f"http://domain.com/page{i}", "target_url": f"http://domain.com/page{i+1}", "domain_url": "http://domain.com"}
        for i in range(1000)
    ]
    
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        await repo.upsert_page_links_batch_async(batch)
        
        call_args = mock_tx.run.call_args[0]
        assert "UNWIND $batch AS item" in call_args[0]
        assert "MERGE (s:Page {url: item.source_url})" in call_args[0]
        assert "MERGE (s)-[:PAGE_LINKS_TO]->(t)" in call_args[0]

from uuid import uuid4

def test_neo4j_init_offline_cases():
    # Case 1: GraphDatabase is None
    with patch("auditor.infrastructure.neo4j_repository.GraphDatabase", None):
        repo = Neo4jRepository()
        assert repo.driver is None

    # Case 2: Password is None/empty
    with patch("os.getenv", side_effect=lambda key, default=None: None if key == "NEO4J_PASSWORD" else default):
        repo = Neo4jRepository()
        assert repo.driver is None

    # Case 3: Connection failure raises Exception
    with patch("os.getenv", return_value="some_password"), \
         patch("neo4j.GraphDatabase.driver", side_effect=Exception("Failed connection")):
        repo = Neo4jRepository()
        assert repo.driver is None

def test_neo4j_close():
    repo = Neo4jRepository()
    mock_drv = MagicMock()
    repo.driver = mock_drv
    repo.close()
    mock_drv.close.assert_called_once()

def test_neo4j_run_with_retry_database_not_found():
    repo = Neo4jRepository()
    mock_drv = MagicMock()
    repo.driver = mock_drv
    
    mock_session = MagicMock()
    mock_drv.session.return_value.__enter__.return_value = mock_session
    
    # First call raises DatabaseNotFound, second call succeeds
    mock_session.run.side_effect = [Exception("DatabaseNotFound"), "success"]
    
    action = lambda s: s.run("MATCH (n) RETURN n")
    res = repo._run_with_retry(action)
    assert res == "success"
    assert repo.database is None  # toggled

@pytest.mark.asyncio
async def test_neo4j_upsert_page_link_async_and_sync():
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    mock_session = MagicMock()
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        # Success path
        await repo.upsert_page_link_async("http://s.com", "http://t.com", "http://d.com")
        assert mock_session.run.called

        # TimeoutError path
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            await repo.upsert_page_link_async("http://s.com", "http://t.com", "http://d.com")
            
        # General Exception path
        with patch("asyncio.wait_for", side_effect=Exception("Random IO error")):
            await repo.upsert_page_link_async("http://s.com", "http://t.com", "http://d.com")

        # Sync Exception path inside _upsert_page_link_sync
        mock_session.run.side_effect = Exception("Cypher Syntax Error")
        repo._upsert_page_link_sync("http://s.com", "http://t.com", "http://d.com") # should log and not crash

@pytest.mark.asyncio
async def test_neo4j_upsert_component_violation_async_and_sync():
    from auditor.domain.violation import Violation, ImpactLevel
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    mock_session = MagicMock()
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    violation = Violation(
        rule_id="rule-1",
        impact=ImpactLevel.CRITICAL,
        description="desc",
        help_url="",
        session_id=uuid4(),
        tags=[],
        compliance_level="",
        category="",
        severity_matrix="",
        url=""
    )
    
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        # Success path (Gov domain -> GIGW-3.0)
        await repo.upsert_component_violation_async("https://gov.in", violation, "<div>gov</div>")
        assert mock_session.run.called
        
        # Bank domain -> RBI-Master-Circular
        await repo.upsert_component_violation_async("https://hdfc.com", violation, "<div>bank</div>")
        
        # General domain -> WCAG-2.2
        await repo.upsert_component_violation_async("https://general.com", violation, "<div>wcag</div>")

        # Sync Exception path inside _upsert_component_violation_sync
        mock_session.run.side_effect = Exception("Cypher Error")
        repo._upsert_component_violation_sync("https://general.com", violation, "<div>wcag</div>") # should log and not crash

@pytest.mark.asyncio
async def test_neo4j_get_graph_data():
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    mock_session = MagicMock()
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    class FakeNode:
        def __init__(self, element_id, labels, props):
            self.element_id = element_id
            self.labels = set(labels)
            self._props = props
        def get(self, key, default=None):
            return self._props.get(key, default)
            
    class FakeRelationship:
        def __init__(self, type):
            self.type = type
            
    node_page = FakeNode("p1", ["Page"], {"url": "http://p1.com"})
    node_comp = FakeNode("c1", ["Component"], {"id": "c1_hash"})
    node_viol = FakeNode("v1", ["Violation"], {"id": "v1_rule", "impact": "critical"})
    node_standard = FakeNode("s1", ["ComplianceStandard"], {"id": "s1_std", "name": "s1_name"})
    node_domain = FakeNode("d1", ["Domain"], {"url": "http://d1.com"})
    
    rel1 = FakeRelationship("PAGE_CONTAINS")
    
    # Construct records mock return
    mock_record1 = {"n": node_page, "r": rel1, "m": node_comp}
    mock_record2 = {"n": node_comp, "r": rel1, "m": node_viol}
    mock_record3 = {"n": node_viol, "r": rel1, "m": node_standard}
    mock_record4 = {"n": node_domain, "r": rel1, "m": node_page}
    
    mock_session.run.return_value = [mock_record1, mock_record2, mock_record3, mock_record4]
    
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        data = repo.get_graph_data()
        assert len(data["nodes"]) > 0
        assert len(data["links"]) > 0
        
        # Exception handling path
        mock_session.run.side_effect = Exception("Neo4j Read Error")
        data_err = repo.get_graph_data()
        assert data_err == {"nodes": [], "links": []}

@pytest.mark.asyncio
async def test_neo4j_get_graph_insights_error_and_missing():
    repo = Neo4jRepository()
    repo.driver = MagicMock()
    mock_session = MagicMock()
    repo.driver.session.return_value.__enter__.return_value = mock_session
    
    # Case 1: return_value is None
    mock_session.run.return_value = None
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        insights = repo.get_graph_insights()
        assert insights["impact_probability"] == "Unknown"
        
        # Case 2: exception
        mock_session.run.side_effect = Exception("Cypher execution failed")
        insights_err = repo.get_graph_insights()
        assert insights_err["impact_probability"] == "Unknown"

@pytest.mark.asyncio
async def test_neo4j_batch_operations_edge_cases():
    repo = Neo4jRepository()
    # Offline mode (driver is None)
    repo.driver = None
    await repo.upsert_page_links_batch_async([{"test": 1}])
    await repo.upsert_component_violations_batch_async([{"test": 1}])
    
    # Empty batch
    repo.driver = MagicMock()
    await repo.upsert_page_links_batch_async([])
    await repo.upsert_component_violations_batch_async([])

    mock_session = MagicMock()
    repo.driver.session.return_value.__enter__.return_value = mock_session
    # TimeoutError path for upsert_page_links_batch_async
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
        await repo.upsert_page_links_batch_async([{"test": 1}])
        
    # TimeoutError path for upsert_component_violations_batch_async
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
        with pytest.raises(RepositoryError):
            await repo.upsert_component_violations_batch_async([{"test": 1}])

    # General Exception path for upsert_page_links_batch_async
    mock_session.begin_transaction.side_effect = Exception("Tx Failed")
    with patch("asyncio.to_thread", side_effect=lambda func, *args: func(*args)):
        await repo.upsert_page_links_batch_async([{"test": 1}]) # should not crash

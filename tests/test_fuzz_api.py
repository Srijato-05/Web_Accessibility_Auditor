import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from auditor.main import app
import string
import random

client = TestClient(app)

def generate_random_string(length=1000):
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

@pytest.fixture(autouse=True)
def mock_db_init():
    with patch("auditor.presentation.api.init_db", AsyncMock()), \
         patch("auditor.main.os.makedirs"):
        yield

def test_fuzz_create_target_api():
    """Fuzz the POST /targets endpoint with extremely long URLs and malformed data."""
    
    mock_db = MagicMock()
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_db.exec = AsyncMock(return_value=mock_exec)
    mock_db.merge = AsyncMock()
    mock_db.commit = AsyncMock()
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_db
    
    # 1. Extremely long URL (potential buffer overflow or DB column limit trigger)
    long_url = "http://example.com/" + generate_random_string(5000)
    with patch("auditor.presentation.api.AsyncSession", return_value=mock_ctx):
        response = client.post("/api/targets", json={"url": long_url})
    # Our API validates safe URL, so it should either be 400 or handled cleanly
    assert response.status_code in [400, 422, 200]
    
    # 2. XSS payload in URL
    xss_url = "javascript:alert(1)"
    with patch("auditor.presentation.api.AsyncSession", return_value=mock_ctx):
        response = client.post("/api/targets", json={"url": xss_url})
    assert response.status_code in [400, 422] # Should be rejected by is_safe_url
    
    # 3. SQL Injection payload in URL
    sqli_url = "http://example.com/page?id=1'; DROP TABLE targets;--"
    with patch("auditor.presentation.api.AsyncSession", return_value=mock_ctx):
        # We mock DB to just see if the API accepts the payload structure without crashing 500
        response = client.post("/api/targets", json={"url": sqli_url})
        assert response.status_code in [200, 400]

def test_fuzz_batch_audit_api():
    """Fuzz batch audit orchestration endpoint."""
    
    # Send massive invalid json body
    massive_payload = {f"key_{i}": generate_random_string(100) for i in range(1000)}
    response = client.post("/api/batch/run", json=massive_payload)
    assert response.status_code == 422 # FastAPI should catch invalid schema
    
    # Send incorrect types
    response = client.post("/api/batch/run", json={"use_queue": "NOT_A_BOOLEAN_OR_INT"})
    assert response.status_code == 422

def test_fuzz_diff_api():
    """Fuzz the targets diff API with bad inputs."""
    
    # Pass SQL injection
    sqli_url = "http://test.com' OR 1=1"
    
    mock_diff = MagicMock()
    mock_diff.calculate_diff_by_target = AsyncMock(return_value={"status": "insufficient_data"})
    
    with patch("auditor.application.diff_service.AuditDiffService", return_value=mock_diff):
        response = client.get(f"/api/targets/diff?url={sqli_url}")
        assert response.status_code == 200
        mock_diff.calculate_diff_by_target.assert_called_with(sqli_url)
        
    # Pass extremely long url
    long_url = "http://test.com/" + ("A" * 10000)
    with patch("auditor.application.diff_service.AuditDiffService", return_value=mock_diff):
        response = client.get(f"/api/targets/diff?url={long_url}")
        assert response.status_code == 200

def test_fuzz_get_violation_api():
    """Fuzz the individual violation retrieval endpoint."""
    
    # Invalid UUID (too short)
    response = client.get("/api/violations/123")
    assert response.status_code == 400
    
    # SQLi in UUID
    response = client.get("/api/violations/123' OR '1'='1")
    assert response.status_code == 400
    
    # Valid UUID but completely random
    import uuid
    random_uuid = str(uuid.uuid4())
    
    mock_db = MagicMock()
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_db.exec = AsyncMock(return_value=mock_exec)
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_db
    
    with patch("auditor.presentation.api.AsyncSession", return_value=mock_ctx):
        response = client.get(f"/api/violations/{random_uuid}")
        assert response.status_code == 404

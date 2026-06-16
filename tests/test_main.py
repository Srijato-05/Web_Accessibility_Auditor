import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture
def mock_backup_manager():
    mgr = MagicMock()
    mgr.check_and_recover = MagicMock()
    mgr.create_backup = MagicMock()
    return mgr

def test_main_app_lifecycle(mock_backup_manager):
    with patch("auditor.infrastructure.backup_manager.DatabaseBackupManager", return_value=mock_backup_manager), \
         patch("auditor.main.init_db", AsyncMock()) as mock_init_db, \
         patch("auditor.presentation.api.cleanup_orphaned_targets", AsyncMock()) as mock_cleanup:
         
        from auditor.main import app
        with TestClient(app) as client:
            response = client.options("/api/scans", headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            })
            assert response.status_code == 200
            
            res = client.get("/")
            assert res.status_code == 200
            assert res.json() == {"status": "online"}
            
            res_fav = client.get("/favicon.ico")
            assert res_fav.status_code == 200
            
        mock_init_db.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_backup_manager.check_and_recover.assert_called_once()
        mock_backup_manager.create_backup.assert_called_once()

def test_main_app_lifecycle_exceptions(mock_backup_manager):
    mock_backup_manager.check_and_recover.side_effect = Exception("Backup fail")
    with patch("auditor.infrastructure.backup_manager.DatabaseBackupManager", return_value=mock_backup_manager), \
         patch("auditor.main.init_db", AsyncMock()) as mock_init_db, \
         patch("auditor.presentation.api.cleanup_orphaned_targets", AsyncMock(side_effect=Exception("Cleanup fail"))):
         
        from auditor.main import app
        with TestClient(app) as client:
            res = client.get("/")
            assert res.status_code == 200

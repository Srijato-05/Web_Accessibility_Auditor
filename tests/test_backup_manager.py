import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from auditor.infrastructure.backup_manager import DatabaseBackupManager

@pytest.fixture
def temp_db_dir(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = data_dir / "audit_results.db"
    
    # Create a dummy sqlite db
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO test (value) VALUES ('test1')")
    conn.commit()
    conn.close()
    
    # Patch DATA_DIR to use the temp directory
    import auditor.shared.paths
    import auditor.infrastructure.backup_manager
    monkeypatch.setattr(auditor.shared.paths, "DATA_DIR", data_dir)
    monkeypatch.setattr(auditor.infrastructure.backup_manager, "DATA_DIR", data_dir)
    
    return str(db_path)

def test_backup_manager_init(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir, max_backups=3)
    assert str(manager.db_path) == temp_db_dir
    assert manager.max_backups == 3
    assert os.path.exists(manager.backup_dir)

@patch("auditor.infrastructure.backup_manager.sqlite3.connect")
def test_create_backup_success(mock_connect, temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    
    mock_src_conn = MagicMock()
    mock_dst_conn = MagicMock()
    
    # Needs 3 connections: 1 for verify_integrity, 2 for src/dst connect in create_backup
    mock_connect.side_effect = [mock_src_conn, mock_src_conn, mock_dst_conn]
    
    # verify_integrity needs connection cursor to return "ok"
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("ok",)
    mock_src_conn.cursor.return_value = mock_cursor
    
    backup_path = manager.create_backup()
    
    assert backup_path is not None
    assert mock_src_conn.backup.called
    assert mock_src_conn.close.called
    assert mock_dst_conn.close.called

@patch("auditor.infrastructure.backup_manager.sqlite3.connect")
def test_create_backup_failure(mock_connect, temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    # verify_integrity fails, create_backup aborts and returns None
    mock_connect.side_effect = Exception("Simulated DB connection error")
    
    backup_path = manager.create_backup()
    assert backup_path is None

def test_check_database_integrity(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    is_valid = manager.verify_integrity(manager.db_path)
    assert is_valid is True

@patch("auditor.infrastructure.backup_manager.sqlite3.connect")
def test_check_database_integrity_corrupt(mock_connect, temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("corrupt_database",)
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    
    is_valid = manager.verify_integrity(manager.db_path)
    assert is_valid is False

def test_rotate_backups(temp_db_dir, tmp_path):
    manager = DatabaseBackupManager(db_path=temp_db_dir, max_backups=2)
    
    # Create fake backups
    for i in range(5):
        backup_file = os.path.join(manager.backup_dir, f"audit_results_backup_{i}.db")
        with open(backup_file, "w") as f:
            f.write("fake backup")
            
    # ensure files are written
    backups_before = manager._get_backup_files()
    assert len(backups_before) == 5
    
    manager._prune_old_backups()
    
    backups_after = manager._get_backup_files()
    assert len(backups_after) == 2

@patch("auditor.infrastructure.backup_manager.shutil.copy2")
def test_restore_from_backup_success(mock_copy, temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    
    # Create a fake backup file
    backup_file = os.path.join(manager.backup_dir, "audit_results_backup_valid.db")
    with open(backup_file, "w") as f:
        f.write("valid backup")
        
    # Remove original DB file to trigger recovery flow
    if os.path.exists(temp_db_dir):
        os.remove(temp_db_dir)
        
    with patch.object(manager, "verify_integrity", return_value=True):
        restored = manager.check_and_recover()
        assert restored is True
        assert mock_copy.called

def test_restore_from_backup_no_backups(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    # Ensure empty backup dir
    for f in os.listdir(manager.backup_dir):
        os.remove(os.path.join(manager.backup_dir, f))
        
    # Remove original DB file to trigger recovery flow
    if os.path.exists(temp_db_dir):
        os.remove(temp_db_dir)
        
    restored = manager.check_and_recover()
    assert restored is False

def test_create_backup_db_path_not_exists(tmp_path):
    manager = DatabaseBackupManager(db_path=tmp_path / "nonexistent.db")
    assert manager.create_backup() is None

def test_create_backup_exception_cleanup(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    with patch.object(manager, "verify_integrity", return_value=True), \
         patch("auditor.infrastructure.backup_manager.sqlite3.connect", side_effect=Exception("DB Error")), \
         patch("auditor.infrastructure.backup_manager.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "partial"
        partial_file = Path(manager.backup_dir) / "audit_results_backup_partial.db"
        partial_file.write_text("partial data")
        assert partial_file.exists()
        
        backup_path = manager.create_backup()
        assert backup_path is None
        assert not partial_file.exists()

def test_verify_integrity_not_exists_and_empty_file(tmp_path):
    manager = DatabaseBackupManager(db_path=tmp_path / "db.db")
    assert manager.verify_integrity(tmp_path / "nonexistent.db") is False
    
    empty_file = tmp_path / "empty.db"
    empty_file.write_text("")
    assert manager.verify_integrity(empty_file) is False

def test_verify_integrity_exception(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    with patch("auditor.infrastructure.backup_manager.sqlite3.connect", side_effect=sqlite3.Error("Conn error")):
        assert manager.verify_integrity(manager.db_path) is False

def test_check_and_recover_corrupt_db_and_isolate_fails(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    with patch.object(manager, "verify_integrity", side_effect=[False, True]), \
         patch.object(manager, "get_latest_valid_backup", return_value=Path(temp_db_dir)):
        with patch("pathlib.Path.rename", side_effect=Exception("Rename error")):
            assert manager.check_and_recover() is False

def test_check_and_recover_restore_fails_and_rollback(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir)
    backup_file = Path(manager.backup_dir) / "audit_results_backup_valid.db"
    backup_file.write_text("backup data")
    
    with patch.object(manager, "verify_integrity", side_effect=[False, True, False]), \
         patch("shutil.copy2", side_effect=Exception("Copy error")):
        with patch("pathlib.Path.rename"):
            assert manager.check_and_recover() is False

def test_prune_old_backups_exception(temp_db_dir):
    manager = DatabaseBackupManager(db_path=temp_db_dir, max_backups=1)
    f1 = Path(manager.backup_dir) / "audit_results_backup_1.db"
    f2 = Path(manager.backup_dir) / "audit_results_backup_2.db"
    f1.write_text("1")
    f2.write_text("2")
    
    with patch("os.remove", side_effect=Exception("Remove error")):
        manager._prune_old_backups()

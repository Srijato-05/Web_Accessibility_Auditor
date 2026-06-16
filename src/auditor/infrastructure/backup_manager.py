"""
DATABASE BACKUP MANAGER: CRASH RESILIENCE & SNAPSHOT ENGINE (BM-Z10)
====================================================================

Role: Atomic database backups and auto-recovery.
Features:
  - Online SQLite Backup API integration (non-blocking).
  - Rotation of older snapshots (retains last N copies).
  - Integrity validation using SQLite PRAGMA checks.
  - Automatic restore on corruption detection.
"""

import os
import shutil
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from auditor.shared.paths import DATABASE_PATH, DATA_DIR
from auditor.shared.logging import auditor_logger

class DatabaseBackupManager:
    """
    Manages automated database snapshots, rotative backups, and disaster recovery.
    """
    
    def __init__(self, db_path: Path = DATABASE_PATH, backup_dir: Optional[Path] = None, max_backups: int = 7):
        self.db_path = Path(db_path)
        self.backup_dir = backup_dir or (DATA_DIR / "backups")
        self.max_backups = max_backups
        self.logger = auditor_logger.getChild("BackupManager")
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Optional[Path]:
        """
        Creates an atomic online backup of the SQLite database.
        Returns the path of the created backup file if successful.
        """
        if not self.db_path.exists():
            self.logger.warning(f"Cannot back up database: Source file does not exist at {self.db_path}")
            return None

        # Verify integrity before backup to avoid backing up corrupted database
        if not self.verify_integrity(self.db_path):
            self.logger.error("Database integrity check failed. Aborting backup creation to prevent copying corrupt state.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"audit_results_backup_{timestamp}.db"
        
        self.logger.info(f"Initiating atomic online backup to {backup_file.name}...")
        
        src_conn = None
        dst_conn = None
        try:
            # Using SQLite's online backup API to avoid read/write locks
            src_conn = sqlite3.connect(str(self.db_path))
            dst_conn = sqlite3.connect(str(backup_file))
            
            with dst_conn:
                src_conn.backup(dst_conn)
                
            self.logger.info(f"Online database backup created successfully: {backup_file.name}")
            
            # Prune old backups to free up disk space
            self._prune_old_backups()
            return backup_file
        except Exception as e:
            self.logger.exception(f"Failed to create database backup: {e}")
            # Clean up partial backup file if left on disk
            if backup_file.exists():
                try: os.remove(backup_file)
                except: pass
            return None
        finally:
            if dst_conn:
                dst_conn.close()
            if src_conn:
                src_conn.close()

    def verify_integrity(self, file_path: Path) -> bool:
        """
        Performs a SQLite integrity check on the given file path.
        """
        if not file_path.exists():
            return False
            
        # If the file size is 0, SQLite might treat it as a new DB, which passes integrity check.
        # But for us, 0-size means empty/invalid, so reject it.
        if file_path.stat().st_size == 0:
            return False
            
        conn = None
        try:
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if row and row[0] == "ok":
                return True
            else:
                self.logger.warning(f"Integrity check failed for {file_path.name}: {row}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking integrity of database file {file_path.name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def check_and_recover(self) -> bool:
        """
        Verifies database health. If corrupt or missing, restores from the latest valid backup.
        Returns True if database is healthy (or successfully recovered), False otherwise.
        """
        self.logger.debug("Running database health diagnostics...")
        
        db_exists = self.db_path.exists()
        db_healthy = db_exists and self.verify_integrity(self.db_path)
        
        if db_healthy:
            self.logger.debug("Database status: Healthy.")
            return True
            
        if not db_exists:
            self.logger.warning("Database file is missing. Attempting disaster recovery...")
        else:
            self.logger.critical("DATABASE CORRUPTION DETECTED. Commencing recovery from backup...")
            
        latest_backup = self.get_latest_valid_backup()
        if not latest_backup:
            self.logger.error("No valid backup files found. Disaster recovery cannot proceed.")
            return False
            
        self.logger.warning(f"Restoring database from snapshot: {latest_backup.name}")
        
        # Safe replacement: rename original database first if it exists
        temp_renamed = None
        if db_exists:
            try:
                temp_renamed = self.db_path.with_suffix(".corrupt_temp")
                if temp_renamed.exists():
                    os.remove(temp_renamed)
                self.db_path.rename(temp_renamed)
            except Exception as rename_err:
                self.logger.error(f"Failed to isolate corrupted database: {rename_err}")
                return False
                
        try:
            # Copy backup back to main path
            shutil.copy2(latest_backup, self.db_path)
            
            # Double check recovery result
            if self.verify_integrity(self.db_path):
                self.logger.info("Database successfully restored and validated.")
                if temp_renamed and temp_renamed.exists():
                    try: os.remove(temp_renamed)
                    except: pass
                return True
            else:
                raise RuntimeError("Restored database failed integrity validation.")
        except Exception as recovery_err:
            self.logger.critical(f"FATAL: Database restoration failed: {recovery_err}")
            # Rollback rename if possible
            if temp_renamed and temp_renamed.exists():
                try:
                    if self.db_path.exists():
                        os.remove(self.db_path)
                    temp_renamed.rename(self.db_path)
                except:
                    pass
            return False

    def get_latest_valid_backup(self) -> Optional[Path]:
        """
        Scans backups directory and returns the path to the newest valid backup file.
        """
        backups = self._get_backup_files()
        for backup in backups:
            if self.verify_integrity(backup):
                return backup
        return None

    def _get_backup_files(self) -> List[Path]:
        """
        Returns a list of backup files sorted by modification time, newest first.
        """
        files = list(self.backup_dir.glob("audit_results_backup_*.db"))
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return files

    def _prune_old_backups(self) -> None:
        """
        Removes oldest backup files if the total count exceeds the max retention limit.
        """
        backups = self._get_backup_files()
        if len(backups) <= self.max_backups:
            return
            
        to_delete = backups[self.max_backups:]
        self.logger.info(f"Pruning {len(to_delete)} stale backup files (retention limit: {self.max_backups})...")
        for f in to_delete:
            try:
                os.remove(f)
                self.logger.debug(f"Pruned backup: {f.name}")
            except Exception as e:
                self.logger.warning(f"Failed to prune backup file {f.name}: {e}")

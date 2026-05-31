import os
import pytest
import pathlib
from auditor.shared.paths import get_project_root, REPORTS_DIR, DATA_DIR, EXPORTS_DIR, LOGS_DIR

def test_project_root_discovery():
    root = get_project_root()
    assert isinstance(root, pathlib.Path)
    assert root.exists()
    assert (root / "pyproject.toml").exists()

def test_directories_creation():
    for d in [REPORTS_DIR, DATA_DIR, EXPORTS_DIR, LOGS_DIR]:
        assert isinstance(d, pathlib.Path)
        assert d.exists()
        assert d.is_dir()

def test_environment_variable_overrides(monkeypatch):
    test_db = "sqlite+aiosqlite:///./test_db.db"
    test_redis = "redis://test-redis-host:6379"
    
    monkeypatch.setenv("DATABASE_URL", test_db)
    monkeypatch.setenv("REDIS_URL", test_redis)
    
    # Re-import or reload paths module variables
    import importlib
    import auditor.shared.paths as paths
    importlib.reload(paths)
    
    assert paths.DATABASE_URL == test_db
    assert paths.REDIS_URL == test_redis

def test_boilerplate_path_reconciliation():
    import sys
    import importlib
    from auditor.shared.paths import get_project_root
    
    root_str = str(get_project_root().resolve())
    
    modules_to_reload = [
        "auditor.application.agents.cognitive_agent",
        "auditor.application.agents.controller",
        "auditor.application.agents.motor_agent",
        "auditor.application.agents.neural_agent",
        "auditor.application.agents.visual_agent",
        "auditor.application.agents.utils.validators",
        "auditor.application.audit_service",
        "auditor.application.batch_service",
        "auditor.application.crawl_service",
        "auditor.application.worker",
        "auditor.batch_audit",
        "auditor.batch_seeding",
        "auditor.domain.audit_session",
        "auditor.domain.crawler",
        "auditor.domain.interfaces",
        "auditor.domain.target_repository",
        "auditor.infrastructure.audit_repository",
        "auditor.infrastructure.data_extractor",
        "auditor.infrastructure.link_extractor",
        "auditor.infrastructure.neo4j_repository",
        "auditor.infrastructure.pdf_reporter",
        "auditor.infrastructure.persistence_models",
        "auditor.infrastructure.playwright_engine",
        "auditor.infrastructure.redis_task_queue",
        "auditor.infrastructure.target_repository",
        "auditor.main",
        "auditor.presentation.api",
        "auditor.shared.compliance_mapper",
        "auditor.single_url",
        "auditor.site_audit",
    ]
    
    original_path = list(sys.path)
    try:
        sys.path = [p for p in sys.path if os.path.abspath(p) != root_str and os.path.normpath(p) != root_str]
        
        for mod_name in modules_to_reload:
            try:
                mod = importlib.import_module(mod_name)
                importlib.reload(mod)
            except Exception:
                pass
    finally:
        sys.path = original_path

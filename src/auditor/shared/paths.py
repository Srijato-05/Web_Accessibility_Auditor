import os
import pathlib

def get_project_root() -> pathlib.Path:
    """
    Robust project root discovery. 
    Looks for markers like 'pyproject.toml' to find the top-level directory.
    """
    current = pathlib.Path(__file__).resolve().parent
    # Check parents until we find the marker or hit the filesystem root
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    
    # Fallback to a safe depth if marker missing (e.g. 3 levels up from shared/paths.py)
    return current.parent.parent.parent

# Centralized Path Registry
PROJECT_ROOT = get_project_root()
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = REPORTS_DIR / "data"
EXPORTS_DIR = REPORTS_DIR / "exports"
LOGS_DIR = REPORTS_DIR / "logs"

# Ensure directories exist
for d in [REPORTS_DIR, DATA_DIR, EXPORTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database Config
DATABASE_PATH = DATA_DIR / "audit_results.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

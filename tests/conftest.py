import sys
import os

# Normalize drive letters in sys.path to uppercase on Windows to avoid duplicate module loads
if sys.platform == "win32":
    sys.path[:] = [p[0].upper() + p[1:] if p and len(p) >= 2 and p[1] == ':' else p for p in sys.path]

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    res_loop = policy.new_event_loop()
    yield res_loop
    res_loop.close()

from auditor.infrastructure.task_model import task_metadata

@pytest_asyncio.fixture
async def temp_db_engine():
    """Provides a fresh in-memory SQLite database engine for testing SQLModel logic."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(task_metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
def mock_neo4j_driver():
    """Provides a fully mocked Neo4j driver interface."""
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value = session
    
    # Mock context manager
    session.__enter__.return_value = session
    session.__exit__.return_value = None
    
    # Mock session runs
    session.run.return_value = MagicMock()
    
    return driver

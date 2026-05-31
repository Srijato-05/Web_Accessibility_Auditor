import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import json
import csv
from tempfile import NamedTemporaryFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository
from auditor.infrastructure.persistence_models import TargetModel
from auditor.batch_seeding import seed_from_matrix, seed_from_file

@pytest.mark.asyncio
async def test_seed_from_matrix(temp_db_engine):
    """Verifies that seed_from_matrix registers new domains and skips duplicates."""
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        
        matrix = {
            "Government": ["https://india.gov.in", "https://mygov.in"],
            "Telecom": ["https://jio.com"]
        }
        
        # 1. First run: all targets added
        added, skipped = await seed_from_matrix(repo, matrix)
        await session.commit()
        
        assert added == 3
        assert skipped == 0
        
        # Verify persistence in SQLite
        res = await session.exec(select(TargetModel))
        rows = res.all()
        assert len(rows) == 3
        urls = [r.url for r in rows]
        assert "https://india.gov.in" in urls
        assert "https://jio.com" in urls
        
        # 2. Second run: all duplicates skipped
        added_dup, skipped_dup = await seed_from_matrix(repo, matrix)
        assert added_dup == 0
        assert skipped_dup == 3

@pytest.mark.asyncio
async def test_seed_from_json_file(temp_db_engine):
    """Verifies seeding targets from a valid JSON list file."""
    # Write temporary JSON file
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(["https://json1.com", "https://json2.com"], f)
        json_path = f.name
        
    try:
        async with AsyncSession(temp_db_engine) as session:
            repo = SqlAlchemyTargetRepository(session)
            added, skipped = await seed_from_file(repo, json_path)
            await session.commit()
            
            assert added == 2
            
            # Verify they exist
            res = await session.exec(select(TargetModel))
            rows = res.all()
            assert len(rows) == 2
            assert rows[0].url == "https://json1.com"
    finally:
        os.remove(json_path)

@pytest.mark.asyncio
async def test_seed_from_csv_file(temp_db_engine):
    """Verifies seeding targets from a valid CSV file."""
    # Write temporary CSV file
    with NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["https://csv1.com"])
        writer.writerow(["https://csv2.com"])
        csv_path = f.name
        
    try:
        async with AsyncSession(temp_db_engine) as session:
            repo = SqlAlchemyTargetRepository(session)
            added, skipped = await seed_from_file(repo, csv_path)
            await session.commit()
            
            assert added == 2
            
            # Verify they exist
            res = await session.exec(select(TargetModel))
            rows = res.all()
            assert len(rows) == 2
            assert rows[1].url == "https://csv2.com"
    finally:
        os.remove(csv_path)

@pytest.mark.asyncio
async def test_seed_from_missing_file(temp_db_engine):
    """Verifies that attempting to seed a non-existent file returns zeros and logs warning."""
    async with AsyncSession(temp_db_engine) as session:
        repo = SqlAlchemyTargetRepository(session)
        added, skipped = await seed_from_file(repo, "non_existent_file_path.csv")
        assert added == 0
        assert skipped == 0

@pytest.mark.asyncio
async def test_seed_from_json_dict_file(temp_db_engine):
    """Verifies seeding targets from a valid JSON dict file."""
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"category_a": ["https://dict1.com", "https://dict2.com"]}, f)
        json_path = f.name
        
    try:
        async with AsyncSession(temp_db_engine) as session:
            repo = SqlAlchemyTargetRepository(session)
            added, skipped = await seed_from_file(repo, json_path)
            await session.commit()
            assert added == 2
    finally:
        os.remove(json_path)

@pytest.mark.asyncio
async def test_seed_empty_file(temp_db_engine):
    """Verifies seeding targets from an empty file."""
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        f.write("")
        json_path = f.name
        
    try:
        async with AsyncSession(temp_db_engine) as session:
            repo = SqlAlchemyTargetRepository(session)
            # Should gracefully handle empty json error
            with pytest.raises(Exception):
                await seed_from_file(repo, json_path)
    finally:
        os.remove(json_path)

@pytest.mark.asyncio
async def test_batch_seeding_main(temp_db_engine):
    from unittest.mock import patch, MagicMock, AsyncMock
    import sys
    from auditor import batch_seeding
    
    # 1. Main with default arguments (runs all matrix targets)
    with patch("sys.argv", ["batch_seeding.py"]), \
         patch("auditor.batch_seeding.DATABASE_URL", f"sqlite+aiosqlite:///{os.devnull}"):
        mock_engine = MagicMock()
        with patch("auditor.batch_seeding.create_async_engine", return_value=mock_engine), \
             patch("auditor.batch_seeding.AsyncSession") as mock_session_cls:
             
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            
            with patch("auditor.batch_seeding.seed_from_matrix", AsyncMock(return_value=(10, 5))):
                await batch_seeding.main()
                
    # 2. Main with single category
    with patch("sys.argv", ["batch_seeding.py", "--category", "Telecom"]), \
         patch("auditor.batch_seeding.DATABASE_URL", f"sqlite+aiosqlite:///{os.devnull}"):
        with patch("auditor.batch_seeding.create_async_engine"), \
             patch("auditor.batch_seeding.AsyncSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            with patch("auditor.batch_seeding.seed_from_matrix", AsyncMock(return_value=(2, 0))):
                await batch_seeding.main()

    # 3. Main with invalid category
    with patch("sys.argv", ["batch_seeding.py", "--category", "InvalidCategory"]), \
         patch("auditor.batch_seeding.DATABASE_URL", f"sqlite+aiosqlite:///{os.devnull}"):
        with patch("auditor.batch_seeding.create_async_engine"), \
             patch("auditor.batch_seeding.AsyncSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            await batch_seeding.main()

    # 4. Main with file argument
    with NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(["https://main1.com"], f)
        json_path = f.name
    try:
        with patch("sys.argv", ["batch_seeding.py", "--file", json_path]), \
             patch("auditor.batch_seeding.DATABASE_URL", f"sqlite+aiosqlite:///{os.devnull}"):
            with patch("auditor.batch_seeding.create_async_engine"), \
                 patch("auditor.batch_seeding.AsyncSession") as mock_session_cls:
                mock_session = AsyncMock()
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                with patch("auditor.batch_seeding.seed_from_file", AsyncMock(return_value=(1, 0))):
                    await batch_seeding.main()
    finally:
        os.remove(json_path)


@pytest.mark.asyncio
async def test_batch_seeding_main_real_execution(temp_db_engine):
    from auditor import batch_seeding
    
    with patch("sys.argv", ["batch_seeding.py", "--category", "Telecom"]), \
         patch("auditor.batch_seeding.create_async_engine", return_value=temp_db_engine):
        await batch_seeding.main()


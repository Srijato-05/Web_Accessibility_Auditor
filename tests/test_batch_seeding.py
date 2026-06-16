import pytest
import os
import json
import csv
from unittest.mock import MagicMock, AsyncMock, patch
from auditor.batch_seeding import seed_from_matrix, seed_from_file, main

@pytest.mark.asyncio
async def test_seed_from_matrix():
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.side_effect = lambda url: MagicMock() if "exists" in url else None
    
    matrix = {
        "TestCategory": ["http://exists.com", "http://new.com"]
    }
    
    added, skipped = await seed_from_matrix(mock_repo, matrix)
    assert added == 1
    assert skipped == 1
    assert mock_repo.add_domain.called

@pytest.mark.asyncio
async def test_seed_from_file(tmp_path):
    mock_repo = AsyncMock()
    mock_repo.get_domain_by_url.return_value = None
    
    added, skipped = await seed_from_file(mock_repo, "non_existent.json")
    assert added == 0
    assert skipped == 0
    
    json_list_path = tmp_path / "targets_list.json"
    with open(json_list_path, "w") as f:
        json.dump(["http://a.com", "http://b.com"], f)
        
    added, skipped = await seed_from_file(mock_repo, str(json_list_path))
    assert added == 2
    
    json_dict_path = tmp_path / "targets_dict.json"
    with open(json_dict_path, "w") as f:
        json.dump({"sector1": ["http://c.com"]}, f)
        
    added, skipped = await seed_from_file(mock_repo, str(json_dict_path))
    assert added == 1
    
    csv_path = tmp_path / "targets.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["http://d.com"])
        writer.writerow(["invalid_line"])
        
    added, skipped = await seed_from_file(mock_repo, str(csv_path))
    assert added == 1
    
    empty_json = tmp_path / "empty.json"
    with open(empty_json, "w") as f:
        json.dump({}, f)
    added, skipped = await seed_from_file(mock_repo, str(empty_json))
    assert added == 0

@pytest.mark.asyncio
async def test_batch_seeding_main_cli():
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_begin_ctx = AsyncMock()
    mock_begin_ctx.__aenter__.return_value = mock_conn
    mock_engine.begin.return_value = mock_begin_ctx
    
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    
    with patch("sys.argv", ["batch_seeding.py"]), \
         patch("auditor.batch_seeding.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_seeding.AsyncSession", return_value=mock_ctx), \
         patch("auditor.batch_seeding.seed_from_matrix", AsyncMock(return_value=(5, 2))):
        await main()

    with patch("sys.argv", ["batch_seeding.py", "--category", "Government"]), \
         patch("auditor.batch_seeding.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_seeding.AsyncSession", return_value=mock_ctx), \
         patch("auditor.batch_seeding.seed_from_matrix", AsyncMock(return_value=(1, 0))):
        await main()

    with patch("sys.argv", ["batch_seeding.py", "--category", "InvalidCategory"]), \
         patch("auditor.batch_seeding.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_seeding.AsyncSession", return_value=mock_ctx), \
         patch("builtins.print") as mock_print:
        await main()
        mock_print.assert_any_call("[Error] Category not found: InvalidCategory")

    with patch("sys.argv", ["batch_seeding.py", "--file", "targets.json"]), \
         patch("auditor.batch_seeding.create_async_engine", return_value=mock_engine), \
         patch("auditor.batch_seeding.AsyncSession", return_value=mock_ctx), \
         patch("auditor.batch_seeding.seed_from_file", AsyncMock(return_value=(3, 0))):
        await main()

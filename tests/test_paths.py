import os
import pathlib
from unittest.mock import patch, MagicMock
from auditor.shared.paths import get_project_root

def test_get_project_root_with_marker(tmp_path):
    marker_file = tmp_path / "pyproject.toml"
    marker_file.touch()
    
    fake_file_path = tmp_path / "src" / "auditor" / "shared" / "paths.py"
    fake_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with patch("pathlib.Path.resolve") as mock_resolve:
        mock_resolve.return_value = fake_file_path
        root = get_project_root()
        assert root == tmp_path

def test_get_project_root_fallback(tmp_path):
    fake_file_path = tmp_path / "src" / "auditor" / "shared" / "paths.py"
    fake_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with patch("pathlib.Path.resolve") as mock_resolve:
        mock_resolve.return_value = fake_file_path
        root = get_project_root()
        assert root == tmp_path

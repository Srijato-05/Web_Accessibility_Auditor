import logging
import json
import pytest
from unittest.mock import patch
from auditor.shared.logging import AuditorFormatter, AuditorJSONFormatter

def test_auditor_formatter():
    formatter = AuditorFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Hello info log",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    
    # Assert ansi color codes and components are present
    assert "Hello info log" in formatted
    assert "INFO" in formatted
    assert "test_logger" in formatted
    assert "\x1b[38;5;121m" in formatted # Green color code

def test_auditor_json_formatter_standard():
    formatter = AuditorJSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname="test.py",
        lineno=15,
        msg="Warning message",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["level"] == "WARNING"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Warning message"
    assert "timestamp" in parsed
    assert "session_id" not in parsed
    assert "exception" not in parsed

def test_auditor_json_formatter_with_session():
    formatter = AuditorJSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=20,
        msg="Error message",
        args=(),
        exc_info=None
    )
    record.session_id = "test-session-uuid"
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["session_id"] == "test-session-uuid"

def test_auditor_json_formatter_with_exception():
    formatter = AuditorJSONFormatter()
    try:
        raise ValueError("Simulated DB Connection Drop")
    except Exception as e:
        import sys
        exc_info = sys.exc_info()
        
    record = logging.LogRecord(
        name="test_logger",
        level=logging.CRITICAL,
        pathname="test.py",
        lineno=25,
        msg="Critical failure",
        args=(),
        exc_info=exc_info
    )
    
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    
    assert "exception" in parsed
    assert "ValueError: Simulated DB Connection Drop" in parsed["exception"]

def test_setup_auditor_logging():
    from auditor.shared.logging import setup_auditor_logging
    logger = logging.getLogger("auditor")
    orig_handlers = list(logger.handlers)
    
    try:
        logger.handlers = []
        with patch("os.makedirs") as mock_makedirs, \
             patch("logging.FileHandler") as mock_fh, \
             patch("logging.StreamHandler") as mock_sh:
            
            mock_fh.return_value.level = logging.INFO
            mock_sh.return_value.level = logging.INFO
            
            new_logger = setup_auditor_logging(level=logging.DEBUG)
            
            assert new_logger.level == logging.DEBUG
            assert mock_makedirs.call_count >= 3
            mock_fh.assert_called_once_with("reports/logs/auditor.log")
            mock_sh.assert_called_once()
    finally:
        logger.handlers = orig_handlers

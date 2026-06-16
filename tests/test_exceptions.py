import pytest
from auditor.domain.exceptions import (
    AuditorException,
    NavigationError,
    ExtractionError,
    EvaluationError,
    RepositoryError,
    AuditFailedError,
    InvalidTargetError,
    AuthenticationError
)

def test_auditor_exception_base():
    """Verify base class captures context correctly."""
    ctx = {"url": "http://test.com", "depth": 2}
    exc = AuditorException("Base failure", context=ctx)
    
    assert exc.message == "Base failure"
    assert exc.context == ctx
    assert "Base failure" in str(exc)
    assert str(exc) == "Base failure | Context: {'url': 'http://test.com', 'depth': 2}"

def test_navigation_error():
    """Verify NavigationError specifics."""
    exc = NavigationError("Timeout exceeded", context={"url": "test.com"})
    assert isinstance(exc, AuditorException)
    assert "Timeout exceeded" in str(exc)
    assert exc.context["url"] == "test.com"

def test_extraction_error():
    """Verify ExtractionError semantics."""
    exc = ExtractionError("DOM tree invalid", context={"selector": "body > div"})
    assert exc.message == "DOM tree invalid"
    assert exc.context["selector"] == "body > div"

def test_evaluation_error():
    """Verify EvaluationError semantics."""
    exc = EvaluationError("Axe-core crashed")
    assert exc.context is None
    assert str(exc) == "Axe-core crashed"

def test_repository_error():
    """Verify Database/Repository error specifics."""
    exc = RepositoryError("Lock timeout", context={"table": "audit_sessions"})
    assert "Lock timeout" in str(exc)
    assert exc.context["table"] == "audit_sessions"

def test_audit_failed_error():
    """Verify top-level AuditFailedError."""
    exc = AuditFailedError("Complete system collapse")
    assert isinstance(exc, Exception)
    assert "collapse" in str(exc)

def test_invalid_target_error():
    """Verify invalid URL/Target errors."""
    exc = InvalidTargetError("URL scheme missing", context={"url": "google.com"})
    assert exc.message == "URL scheme missing"

def test_authentication_error():
    """Verify auth failure errors."""
    exc = AuthenticationError("Invalid JWT token provided", context={"token_header": "Bearer xxxx"})
    assert "Invalid JWT" in str(exc)
    assert exc.context["token_header"] == "Bearer xxxx"

def test_exception_chaining():
    """Verify we can chain standard exceptions."""
    try:
        try:
            raise ZeroDivisionError("division by zero")
        except ZeroDivisionError as original:
            raise EvaluationError("Math engine failed", context={"op": "div"}) from original
    except EvaluationError as e:
        assert isinstance(e.__cause__, ZeroDivisionError)
        assert e.context["op"] == "div"

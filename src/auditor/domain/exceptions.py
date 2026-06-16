class AuditorException(Exception):
    """Base exception for the Auditor Platform."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(f"{message} | Context: {context}" if context else message)
        self.message = message
        self.context = context
class EngineError(AuditorException):
    """Raised when the Browser Engine fails an operation."""
    pass

class AuditFailedError(EngineError):
    """Raised when the accessibility scan cannot be completed."""
    pass

class NavigationError(EngineError):
    """Raised when the browser cannot reach the target URL."""
    pass

class RepositoryError(AuditorException):
    """Raised when the persistence layer fails to commit or retrieve data."""
    pass

class BatchError(AuditorException):
    """Raised when an autonomous batch operation fails."""
    pass

class DomainBlockedError(NavigationError):
    """Raised when the target domain detects and blocks the scanner."""
    pass

class ExtractionError(AuditorException):
    pass

class EvaluationError(AuditorException):
    pass

class InvalidTargetError(AuditorException):
    pass

class AuthenticationError(AuditorException):
    pass

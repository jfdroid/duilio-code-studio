"""
Custom Exceptions
=================
Domain-specific exceptions for better error handling.
"""

from typing import Optional


class DuilioException(Exception):
    """Base exception for all DuilioCode errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class FileNotFoundError(DuilioException):
    """Raised when a file or directory is not found."""
    
    def __init__(self, path: str):
        super().__init__(
            message=f"File not found: {path}",
            status_code=404,
            detail=f"The path '{path}' does not exist"
        )
        self.path = path


class FileOperationError(DuilioException):
    """Raised when a file operation fails."""
    
    def __init__(self, operation: str, path: str, reason: str):
        super().__init__(
            message=f"Failed to {operation}: {path}",
            status_code=500,
            detail=f"Error during {operation} on '{path}': {reason}"
        )
        self.operation = operation
        self.path = path
        self.reason = reason


class OllamaConnectionError(DuilioException):
    """Raised when connection to Ollama fails."""
    
    def __init__(self, detail: str = "Could not connect to Ollama"):
        super().__init__(
            message="Ollama connection failed",
            status_code=503,
            detail=detail
        )


class WorkspaceError(DuilioException):
    """Raised for workspace-related errors."""
    
    def __init__(self, message: str, path: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            detail=f"Workspace error: {message}" + (f" (path: {path})" if path else "")
        )
        self.path = path


class ValidationError(DuilioException):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error: {message}",
            status_code=422,
            detail=f"Invalid {field}: {message}"
        )
        self.field = field

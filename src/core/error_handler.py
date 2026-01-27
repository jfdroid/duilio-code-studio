"""
Error Handler
=============
Centralized error handling for the application.
Replaces scattered try/except blocks with consistent error handling.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from core.logger import get_logger
try:
    from core.exceptions import ValidationError, FileNotFoundError, WorkspaceError
except ImportError:
    # Fallback if exceptions not defined
    class ValidationError(Exception):
        def __init__(self, field: str, detail: str, status_code: int = 400):
            self.field = field
            self.detail = detail
            self.status_code = status_code
            super().__init__(detail)
    
    class FileNotFoundError(Exception):
        def __init__(self, path: str):
            self.path = path
            super().__init__(f"File not found: {path}")
    
    class WorkspaceError(Exception):
        def __init__(self, message: str, path: Optional[str] = None):
            self.message = message
            self.path = path
            super().__init__(message)


class ErrorHandler:
    """
    Centralized error handler.
    
    Provides consistent error handling, logging, and HTTP response formatting.
    """
    
    def __init__(self):
        self.logger = get_logger()
    
    def handle_validation_error(
        self,
        error: ValidationError,
        context: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Handle validation errors.
        
        Args:
            error: ValidationError instance
            context: Optional context for logging
            
        Returns:
            HTTPException with appropriate status code
        """
        self.logger.warning(
            f"Validation error: {error.detail}",
            context=context or {},
            field=error.field if hasattr(error, 'field') else None
        )
        
        return HTTPException(
            status_code=error.status_code if hasattr(error, 'status_code') else status.HTTP_400_BAD_REQUEST,
            detail=error.detail
        )
    
    def handle_file_not_found(
        self,
        error: FileNotFoundError,
        context: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Handle file not found errors.
        
        Args:
            error: FileNotFoundError instance
            context: Optional context for logging
            
        Returns:
            HTTPException with 404 status
        """
        self.logger.warning(
            f"File not found: {error.path}",
            context=context or {},
            path=error.path if hasattr(error, 'path') else None
        )
        
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {error.path if hasattr(error, 'path') else 'Unknown'}"
        )
    
    def handle_workspace_error(
        self,
        error: WorkspaceError,
        context: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Handle workspace errors.
        
        Args:
            error: WorkspaceError instance
            context: Optional context for logging
            
        Returns:
            HTTPException with appropriate status code
        """
        self.logger.error(
            f"Workspace error: {error.message}",
            context=context or {},
            workspace_path=error.path if hasattr(error, 'path') else None
        )
        
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.message
        )
    
    def handle_generic_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> HTTPException:
        """
        Handle generic errors.
        
        Args:
            error: Exception instance
            context: Optional context for logging
            status_code: HTTP status code (default: 500)
            
        Returns:
            HTTPException with appropriate status code
        """
        self.logger.error(
            f"Unexpected error: {str(error)}",
            context=context or {},
            exc_info=True
        )
        
        # Don't expose internal error details in production
        detail = str(error) if status_code < 500 else "Internal server error"
        
        return HTTPException(
            status_code=status_code,
            detail=detail
        )
    
    def handle(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Handle any error type.
        
        Automatically routes to appropriate handler based on error type.
        
        Args:
            error: Exception instance
            context: Optional context for logging
            
        Returns:
            HTTPException with appropriate status code and detail
        """
        if isinstance(error, ValidationError):
            return self.handle_validation_error(error, context)
        elif isinstance(error, FileNotFoundError):
            return self.handle_file_not_found(error, context)
        elif isinstance(error, WorkspaceError):
            return self.handle_workspace_error(error, context)
        else:
            return self.handle_generic_error(error, context)


# Singleton instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create ErrorHandler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Convenience function to handle errors.
    
    Args:
        error: Exception instance
        context: Optional context for logging
        
    Returns:
        HTTPException
    """
    handler = get_error_handler()
    return handler.handle(error, context)

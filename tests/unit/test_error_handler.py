"""
Unit Tests for Error Handler
=============================
Test centralized error handling logic.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.error_handler import ErrorHandler, get_error_handler, handle_error
from core.exceptions import ValidationError, FileNotFoundError, WorkspaceError
from fastapi import HTTPException


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_get_error_handler_singleton(self):
        """Test that get_error_handler returns singleton."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        assert handler1 is handler2
        assert isinstance(handler1, ErrorHandler)
    
    def test_handle_validation_error(self):
        """Test handling ValidationError."""
        handler = ErrorHandler()
        error = ValidationError("field", "Invalid value")
        
        http_exc = handler.handle_validation_error(error)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 422  # ValidationError uses 422
        assert "Invalid value" in http_exc.detail
    
    def test_handle_file_not_found_error(self):
        """Test handling FileNotFoundError."""
        handler = ErrorHandler()
        error = FileNotFoundError("/path/to/file.txt")
        
        http_exc = handler.handle_file_not_found(error)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 404
        assert "File not found" in http_exc.detail
    
    def test_handle_workspace_error(self):
        """Test handling WorkspaceError."""
        handler = ErrorHandler()
        error = WorkspaceError("Invalid workspace", "/path/to/workspace")
        
        http_exc = handler.handle_workspace_error(error)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert http_exc.detail == "Invalid workspace"
    
    def test_handle_generic_error(self):
        """Test handling generic Exception."""
        handler = ErrorHandler()
        error = ValueError("Something went wrong")
        
        # Mock logger to avoid exc_info conflict
        import unittest.mock
        with unittest.mock.patch.object(handler.logger, 'error'):
            http_exc = handler.handle_generic_error(error)
            
            assert isinstance(http_exc, HTTPException)
            assert http_exc.status_code == 500
            # In production mode, detail is "Internal server error", in dev it shows the error
            assert http_exc.detail in ["Something went wrong", "Internal server error"]
    
    def test_handle_auto_routing(self):
        """Test that handle() routes to appropriate handler."""
        handler = ErrorHandler()
        
        # ValidationError
        validation_error = ValidationError("field", "Invalid")
        http_exc = handler.handle(validation_error)
        assert http_exc.status_code == 422  # ValidationError uses 422
        
        # FileNotFoundError
        file_error = FileNotFoundError("/path/to/file")
        http_exc = handler.handle(file_error)
        assert http_exc.status_code == 404
        
        # WorkspaceError
        workspace_error = WorkspaceError("Invalid workspace")
        http_exc = handler.handle(workspace_error)
        assert http_exc.status_code == 400
        
        # Generic error (mock logger to avoid exc_info conflict)
        import unittest.mock
        generic_error = ValueError("Generic error")
        with unittest.mock.patch.object(handler.logger, 'error'):
            http_exc = handler.handle(generic_error)
            assert http_exc.status_code == 500
            # Detail can be either the error message or "Internal server error" depending on mode
            assert isinstance(http_exc.detail, str)
    
    def test_handle_with_context(self):
        """Test that handle() accepts context for logging."""
        handler = ErrorHandler()
        error = ValidationError("field", "Invalid")
        
        # Should not raise, context is optional
        http_exc = handler.handle(error, context={"endpoint": "test"})
        assert isinstance(http_exc, HTTPException)


class TestHandleErrorConvenience:
    """Test handle_error convenience function."""
    
    def test_handle_error_function(self):
        """Test that handle_error() function works."""
        error = ValidationError("field", "Invalid")
        
        http_exc = handle_error(error)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 422  # ValidationError uses 422
    
    def test_handle_error_with_context(self):
        """Test handle_error() with context."""
        error = ValidationError("field", "Invalid")
        
        http_exc = handle_error(error, context={"endpoint": "test"})
        
        assert isinstance(http_exc, HTTPException)

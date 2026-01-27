"""
Security Utilities
==================
Input sanitization, XSS prevention, and security helpers.
"""

import re
import html
from typing import Any, Dict, List, Optional
from pathlib import Path


class InputSanitizer:
    """
    Sanitize user inputs to prevent XSS, path traversal, and injection attacks.
    """
    
    # Dangerous patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',
        r'\.\.\\',
        r'\.\.',
        r'//',
        r'\\\\',
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(\'|"|;|--|\#)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
    ]
    
    @classmethod
    def sanitize_path(cls, path: str, workspace_path: Optional[str] = None) -> str:
        """
        Sanitize file path to prevent path traversal attacks.
        
        Args:
            path: File path to sanitize
            workspace_path: Optional workspace root to validate against
            
        Returns:
            Sanitized path
            
        Raises:
            ValueError: If path contains dangerous patterns
        """
        if not path:
            raise ValueError("Path cannot be empty")
        
        # Check for path traversal
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                raise ValueError(f"Path traversal detected in: {path}")
        
        # Normalize path
        normalized = Path(path).resolve()
        
        # If workspace_path provided, ensure path is within workspace
        if workspace_path:
            workspace_root = Path(workspace_path).resolve()
            try:
                normalized.relative_to(workspace_root)
            except ValueError:
                raise ValueError(f"Path outside workspace: {path}")
        
        return str(normalized)
    
    @classmethod
    def sanitize_text(cls, text: str, allow_html: bool = False) -> str:
        """
        Sanitize text input to prevent XSS attacks.
        
        Args:
            text: Text to sanitize
            allow_html: If True, only remove dangerous tags (default: False, escape all HTML)
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                # Remove dangerous content
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Escape HTML if not allowed
        if not allow_html:
            text = html.escape(text)
        
        return text
    
    @classmethod
    def sanitize_sql_input(cls, value: Any) -> str:
        """
        Sanitize input for SQL queries (parameterized queries should be used instead).
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized string
        """
        if value is None:
            return ""
        
        value_str = str(value)
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_str, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous SQL pattern detected")
        
        # Escape single quotes
        value_str = value_str.replace("'", "''")
        
        return value_str
    
    @classmethod
    def validate_model_name(cls, model_name: str) -> str:
        """
        Validate and sanitize model name.
        
        Args:
            model_name: Model name to validate
            
        Returns:
            Sanitized model name
            
        Raises:
            ValueError: If model name is invalid
        """
        if not model_name:
            raise ValueError("Model name cannot be empty")
        
        # Model names should only contain: letters, numbers, colons, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9:_\-]+$', model_name):
            raise ValueError(f"Invalid model name format: {model_name}")
        
        return model_name.strip()
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], allowed_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sanitize dictionary input, removing dangerous keys and sanitizing values.
        
        Args:
            data: Dictionary to sanitize
            allowed_keys: Optional list of allowed keys (whitelist)
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Check if key is allowed
            if allowed_keys and key not in allowed_keys:
                continue
            
            # Sanitize key
            key = cls.sanitize_text(str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, allowed_keys)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_text(str(item)) if isinstance(item, str) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized

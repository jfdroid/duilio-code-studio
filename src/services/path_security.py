"""
Path Security Service
=====================
Enhanced security validation for file paths to prevent path traversal attacks.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from core.logger import get_logger

import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
logger = get_logger()


class PathSecurity:
    """
    Security validation for file paths.
    
    Prevents:
    - Path traversal attacks (../, ..\\)
    - Access outside workspace
    - Symlink attacks
    - Null byte injection
    """
    
    # Dangerous patterns
    PATH_TRAVERSAL_PATTERNS = [
        '../', '..\\', '..%2F', '..%5C',  # URL encoded
        '%2E%2E%2F', '%2E%2E%5C',  # Double encoded
        '....//', '....\\\\',  # Double dots
    ]
    
    # Null byte patterns
    NULL_BYTE_PATTERNS = ['\x00', '%00', '\\0']
    
    # Dangerous characters
    DANGEROUS_CHARS = ['\x00', '\r', '\n', '\t']
    
    @classmethod
    def validate_path(
        cls,
        file_path: str,
        workspace_path: Optional[str] = None,
        allow_absolute: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate path for security issues.
        
        Args:
            file_path: Path to validate
            workspace_path: Optional workspace root
            allow_absolute: Allow absolute paths outside workspace
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "Path cannot be empty"
        
        # Check for null bytes
        for pattern in cls.NULL_BYTE_PATTERNS:
            if pattern in file_path:
                logger.log_security_event(
                    "null_byte_injection",
                    f"Null byte detected in path: {file_path}",
                    blocked=True
                )
                return False, "Path contains null byte (security risk)"
        
        # Check for dangerous characters
        for char in cls.DANGEROUS_CHARS:
            if char in file_path:
                logger.log_security_event(
                    "dangerous_char",
                    f"Dangerous character detected in path: {file_path}",
                    blocked=True
                )
                return False, f"Path contains dangerous character: {repr(char)}"
        
        # Check for path traversal patterns
        path_normalized = file_path.replace('\\', '/')
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if pattern in path_normalized:
                logger.log_security_event(
                    "path_traversal",
                    f"Path traversal detected in path: {file_path}",
                    blocked=True
                )
                return False, f"Path traversal detected: {pattern}"
        
        # If workspace is provided, check if path is within workspace
        if workspace_path:
            workspace_abs = os.path.abspath(workspace_path)
            
            # Resolve path
            try:
                if os.path.isabs(file_path):
                    file_abs = os.path.abspath(file_path)
                else:
                    file_abs = os.path.abspath(os.path.join(workspace_path, file_path))
                
                # Check if path is within workspace
                try:
                    rel_path = os.path.relpath(file_abs, workspace_abs)
                    if rel_path.startswith('..'):
                        if not allow_absolute:
                            logger.log_security_event(
                                "path_outside_workspace",
                                f"Path outside workspace: {file_path}",
                                workspace_path=workspace_path,
                                blocked=True
                            )
                            return False, "Path is outside workspace (security risk)"
                except ValueError:
                    # Different drives (Windows), check if absolute is allowed
                    if not allow_absolute:
                        logger.log_security_event(
                            "path_different_drive",
                            f"Path on different drive: {file_path}",
                            workspace_path=workspace_path,
                            blocked=True
                        )
                        return False, "Path is on different drive (security risk)"
                
                # Check for symlink attacks (if path exists, check if it's a symlink)
                if os.path.exists(file_abs):
                    if os.path.islink(file_abs):
                        # Resolve symlink and check if it's still within workspace
                        real_path = os.path.realpath(file_abs)
                        try:
                            rel_real = os.path.relpath(real_path, workspace_abs)
                            if rel_real.startswith('..'):
                                logger.log_security_event(
                                    "symlink_attack",
                                    f"Symlink pointing outside workspace: {file_path} -> {real_path}",
                                    workspace_path=workspace_path,
                                    blocked=True
                                )
                                return False, "Symlink points outside workspace (security risk)"
                        except ValueError:
                            logger.log_security_event(
                                "symlink_attack",
                                f"Symlink pointing to different drive: {file_path} -> {real_path}",
                                workspace_path=workspace_path,
                                blocked=True
                            )
                            return False, "Symlink points to different drive (security risk)"
            except Exception as e:
                logger.error(
                    f"Error validating path: {file_path}",
                    context={"error": str(e), "workspace_path": workspace_path}
                )
                return False, f"Error validating path: {str(e)}"
        
        return True, None
    
    @classmethod
    def sanitize_path(cls, file_path: str) -> str:
        """
        Sanitize path by removing dangerous patterns.
        
        Note: This is a fallback - prefer validate_path and reject invalid paths.
        """
        sanitized = file_path
        
        # Remove null bytes
        for pattern in cls.NULL_BYTE_PATTERNS:
            sanitized = sanitized.replace(pattern, '')
        
        # Remove dangerous characters
        for char in cls.DANGEROUS_CHARS:
            sanitized = sanitized.replace(char, '')
        
        # Remove path traversal patterns (basic)
        sanitized = sanitized.replace('../', '').replace('..\\', '')
        
        return sanitized
    
    @classmethod
    def is_safe_filename(cls, filename: str) -> bool:
        """
        Check if filename is safe (no path traversal, no dangerous chars).
        """
        if not filename:
            return False
        
        # Check for path separators
        if '/' in filename or '\\' in filename:
            return False
        
        # Check for null bytes
        if '\x00' in filename:
            return False
        
        # Check for path traversal
        if '..' in filename:
            return False
        
        return True

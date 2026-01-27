"""
Input Validators
================
Centralized validation for all inputs.
"""

from pathlib import Path
from typing import Optional, Tuple
from .exceptions import ValidationError, FileNotFoundError, WorkspaceError
from .logger import get_logger


class WorkspacePathValidator:
    """Validate and normalize workspace paths."""
    
    @staticmethod
    def validate(path: str, must_exist: bool = True) -> Path:
        """
        Validate and normalize workspace path.
        
        Args:
            path: Path string to validate
            must_exist: If True, path must exist
            
        Returns:
            Normalized Path object
            
        Raises:
            ValidationError: If path is invalid
            FileNotFoundError: If path doesn't exist (when must_exist=True)
        """
        if not path:
            raise ValidationError("path", "Path cannot be empty")
        
        # Expand user home directory
        expanded_path = Path(path).expanduser().resolve()
        
        # Check for path traversal attempts
        if ".." in str(expanded_path):
            # Additional check: ensure resolved path is within reasonable bounds
            try:
                resolved = expanded_path.resolve()
                # Allow if it's a valid absolute path
                if not resolved.is_absolute():
                    raise ValidationError("path", f"Invalid path: {path}")
            except Exception as e:
                raise ValidationError("path", f"Invalid path format: {path}")
        
        if must_exist and not expanded_path.exists():
            raise FileNotFoundError(str(expanded_path))
        
        return expanded_path
    
    @staticmethod
    def validate_workspace(path: str) -> Path:
        """
        Validate workspace path (must be a directory).
        
        Args:
            path: Workspace path
            
        Returns:
            Normalized Path object
            
        Raises:
            WorkspaceError: If path is not a valid workspace
        """
        validated_path = WorkspacePathValidator.validate(path, must_exist=True)
        
        if not validated_path.is_dir():
            raise WorkspaceError(f"Path is not a directory: {path}", path=str(validated_path))
        
        return validated_path


class ModelNameValidator:
    """Validate model names."""
    
    VALID_MODEL_PATTERNS = [
        r'^[a-zA-Z0-9._-]+:[0-9]+[a-z]*$',  # qwen2.5-coder:14b
        r'^[a-zA-Z0-9._-]+$',  # qwen2.5-coder (without tag)
    ]
    
    @staticmethod
    def validate(model: str, available_models: Optional[list] = None) -> str:
        """
        Validate model name format.
        
        Args:
            model: Model name to validate
            available_models: Optional list of available models to check against
            
        Returns:
            Normalized model name
            
        Raises:
            ValidationError: If model name is invalid
        """
        if not model:
            raise ValidationError("model", "Model name cannot be empty")
        
        model = model.strip()
        
        # Check format
        import re
        is_valid = any(re.match(pattern, model) for pattern in ModelNameValidator.VALID_MODEL_PATTERNS)
        
        if not is_valid:
            raise ValidationError("model", f"Invalid model name format: {model}")
        
        # Check if model is available (if list provided)
        if available_models:
            model_names = [
                m.get("name", m) if isinstance(m, dict) else m 
                for m in available_models
            ]
            if model not in model_names:
                raise ValidationError("model", f"Model not available: {model}")
        
        return model


class FilePathValidator:
    """Validate file paths within workspace."""
    
    @staticmethod
    def validate(
        file_path: str, 
        workspace_path: Optional[str] = None,
        must_exist: bool = False
    ) -> Tuple[Path, Path]:
        """
        Validate file path, optionally within workspace.
        
        Args:
            file_path: File path to validate
            workspace_path: Optional workspace root
            must_exist: If True, file must exist
            
        Returns:
            Tuple of (file_path, workspace_path) as Path objects
            
        Raises:
            ValidationError: If path is invalid
            FileNotFoundError: If file doesn't exist (when must_exist=True)
        """
        if not file_path:
            raise ValidationError("file_path", "File path cannot be empty")
        
        file_path_obj = Path(file_path).expanduser()
        
        # If workspace provided, ensure file is within workspace
        if workspace_path:
            workspace_path_obj = WorkspacePathValidator.validate(workspace_path, must_exist=True)
            
            # Resolve relative to workspace
            if not file_path_obj.is_absolute():
                file_path_obj = workspace_path_obj / file_path_obj
            
            # Ensure file is within workspace (prevent path traversal)
            try:
                resolved_file = file_path_obj.resolve()
                resolved_workspace = workspace_path_obj.resolve()
                
                # Check if file is within workspace
                if not str(resolved_file).startswith(str(resolved_workspace)):
                    raise ValidationError(
                        "file_path", 
                        f"File path outside workspace: {file_path}"
                    )
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                raise ValidationError("file_path", f"Invalid file path: {file_path}")
            
            if must_exist and not file_path_obj.exists():
                raise FileNotFoundError(str(file_path_obj))
            
            return resolved_file, resolved_workspace
        
        # No workspace - just validate path
        if must_exist and not file_path_obj.exists():
            raise FileNotFoundError(str(file_path_obj))
        
        return file_path_obj, Path.cwd()


class TemperatureValidator:
    """Validate temperature values."""
    
    @staticmethod
    def validate(temperature: float) -> float:
        """
        Validate temperature value (0.0 to 2.0).
        
        Args:
            temperature: Temperature value
            
        Returns:
            Clamped temperature value
            
        Raises:
            ValidationError: If temperature is out of range
        """
        if not isinstance(temperature, (int, float)):
            raise ValidationError("temperature", "Temperature must be a number")
        
        if temperature < 0.0 or temperature > 2.0:
            raise ValidationError(
                "temperature", 
                f"Temperature must be between 0.0 and 2.0, got {temperature}"
            )
        
        return float(temperature)


class MaxTokensValidator:
    """Validate max_tokens values."""
    
    @staticmethod
    def validate(max_tokens: int, min_tokens: int = 1, max_tokens_limit: int = 32768) -> int:
        """
        Validate max_tokens value.
        
        Args:
            max_tokens: Maximum tokens value
            min_tokens: Minimum allowed value
            max_tokens_limit: Maximum allowed value
            
        Returns:
            Validated max_tokens value
            
        Raises:
            ValidationError: If max_tokens is out of range
        """
        if not isinstance(max_tokens, int):
            raise ValidationError("max_tokens", "max_tokens must be an integer")
        
        if max_tokens < min_tokens or max_tokens > max_tokens_limit:
            raise ValidationError(
                "max_tokens",
                f"max_tokens must be between {min_tokens} and {max_tokens_limit}, got {max_tokens}"
            )
        
        return max_tokens

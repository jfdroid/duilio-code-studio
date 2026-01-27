"""
Unit Tests for Validators
=========================
Test input validation logic in isolation.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.validators import (
    WorkspacePathValidator,
    ModelNameValidator,
    FilePathValidator,
    TemperatureValidator,
    MaxTokensValidator
)
from core.exceptions import ValidationError, FileNotFoundError, WorkspaceError


class TestWorkspacePathValidator:
    """Test workspace path validation."""
    
    def test_validate_empty_path(self):
        """Test that empty path raises ValidationError."""
        with pytest.raises(ValidationError):
            WorkspacePathValidator.validate("")
    
    def test_validate_none_path(self):
        """Test that None path raises ValidationError."""
        with pytest.raises(ValidationError):
            WorkspacePathValidator.validate(None)
    
    def test_validate_valid_path(self, tmp_path):
        """Test that valid path returns Path object."""
        result = WorkspacePathValidator.validate(str(tmp_path), must_exist=True)
        assert isinstance(result, Path)
        assert result.exists()
    
    def test_validate_home_directory(self):
        """Test that home directory (~) is expanded."""
        result = WorkspacePathValidator.validate("~", must_exist=True)
        assert isinstance(result, Path)
        assert result.is_absolute()
    
    def test_validate_workspace_not_directory(self, tmp_path):
        """Test that non-directory path raises WorkspaceError."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        
        with pytest.raises(WorkspaceError):
            WorkspacePathValidator.validate_workspace(str(file_path))


class TestModelNameValidator:
    """Test model name validation."""
    
    def test_validate_empty_model(self):
        """Test that empty model name raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelNameValidator.validate("")
    
    def test_validate_valid_model_with_tag(self):
        """Test that model with tag is valid."""
        result = ModelNameValidator.validate("qwen2.5-coder:14b")
        assert result == "qwen2.5-coder:14b"
    
    def test_validate_valid_model_without_tag(self):
        """Test that model without tag is valid."""
        result = ModelNameValidator.validate("qwen2.5-coder")
        assert result == "qwen2.5-coder"
    
    def test_validate_invalid_model_format(self):
        """Test that invalid format raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelNameValidator.validate("invalid@model#name")
    
    def test_validate_model_not_available(self):
        """Test that unavailable model raises ValidationError."""
        available_models = [{"name": "qwen2.5-coder:14b"}]
        
        with pytest.raises(ValidationError):
            ModelNameValidator.validate("nonexistent-model", available_models=available_models)
    
    def test_validate_model_available(self):
        """Test that available model passes validation."""
        available_models = [{"name": "qwen2.5-coder:14b"}]
        result = ModelNameValidator.validate("qwen2.5-coder:14b", available_models=available_models)
        assert result == "qwen2.5-coder:14b"


class TestTemperatureValidator:
    """Test temperature validation."""
    
    def test_validate_valid_temperature(self):
        """Test that valid temperature passes."""
        assert TemperatureValidator.validate(0.7) == 0.7
        assert TemperatureValidator.validate(0.0) == 0.0
        assert TemperatureValidator.validate(2.0) == 2.0
        assert TemperatureValidator.validate(1) == 1.0  # int converts to float
    
    def test_validate_temperature_below_zero(self):
        """Test that temperature below 0.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            TemperatureValidator.validate(-0.1)
    
    def test_validate_temperature_above_two(self):
        """Test that temperature above 2.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            TemperatureValidator.validate(2.1)
    
    def test_validate_temperature_not_number(self):
        """Test that non-number raises ValidationError."""
        with pytest.raises(ValidationError):
            TemperatureValidator.validate("0.7")
        
        with pytest.raises(ValidationError):
            TemperatureValidator.validate(None)


class TestMaxTokensValidator:
    """Test max_tokens validation."""
    
    def test_validate_valid_max_tokens(self):
        """Test that valid max_tokens passes."""
        assert MaxTokensValidator.validate(4096) == 4096
        assert MaxTokensValidator.validate(1) == 1
        assert MaxTokensValidator.validate(32768) == 32768
    
    def test_validate_max_tokens_below_minimum(self):
        """Test that max_tokens below minimum raises ValidationError."""
        with pytest.raises(ValidationError):
            MaxTokensValidator.validate(0)
    
    def test_validate_max_tokens_above_maximum(self):
        """Test that max_tokens above maximum raises ValidationError."""
        with pytest.raises(ValidationError):
            MaxTokensValidator.validate(32769)
    
    def test_validate_max_tokens_not_integer(self):
        """Test that non-integer raises ValidationError."""
        with pytest.raises(ValidationError):
            MaxTokensValidator.validate(4096.5)
        
        with pytest.raises(ValidationError):
            MaxTokensValidator.validate("4096")


class TestFilePathValidator:
    """Test file path validation."""
    
    def test_validate_empty_file_path(self):
        """Test that empty file path raises ValidationError."""
        with pytest.raises(ValidationError):
            FilePathValidator.validate("")
    
    def test_validate_file_path_within_workspace(self, tmp_path):
        """Test that file path within workspace is valid."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        file_path, workspace_path = FilePathValidator.validate(
            "file.txt",
            workspace_path=str(workspace),
            must_exist=False
        )
        
        assert isinstance(file_path, Path)
        assert isinstance(workspace_path, Path)
        assert str(file_path).startswith(str(workspace_path))
    
    def test_validate_file_path_outside_workspace(self, tmp_path):
        """Test that file path outside workspace raises ValidationError."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        outside_path = tmp_path / "outside" / "file.txt"
        outside_path.parent.mkdir()
        
        with pytest.raises(ValidationError):
            FilePathValidator.validate(
                str(outside_path),
                workspace_path=str(workspace),
                must_exist=False
            )
    
    def test_validate_file_path_must_exist(self, tmp_path):
        """Test that must_exist=True requires file to exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        with pytest.raises(FileNotFoundError):
            FilePathValidator.validate(
                "nonexistent.txt",
                workspace_path=str(workspace),
                must_exist=True
            )

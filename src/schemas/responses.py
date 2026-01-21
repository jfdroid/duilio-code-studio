"""
Response Schemas
================
Pydantic models for API responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """Generic status response."""
    
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class GenerateResponse(BaseModel):
    """Response from text/code generation."""
    
    response: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used")
    done: bool = Field(default=True)
    total_duration: Optional[int] = Field(None, description="Total time in nanoseconds")
    eval_count: Optional[int] = Field(None, description="Number of tokens generated")


class FileInfo(BaseModel):
    """Information about a file or directory."""
    
    name: str
    path: str
    is_dir: bool
    is_file: bool
    size: int = 0
    modified: Optional[str] = None
    extension: Optional[str] = None
    permissions: Optional[str] = None


class FileContent(BaseModel):
    """File content response."""
    
    path: str
    content: str
    encoding: str = "utf-8"
    size: int
    lines: int
    modified: Optional[str] = None
    language: Optional[str] = None


class DirectoryContents(BaseModel):
    """Directory listing response."""
    
    path: str
    items: List[FileInfo]
    total_files: int
    total_dirs: int
    total_size: int = 0


class SearchResult(BaseModel):
    """Search result item."""
    
    path: str
    name: str
    matches: List[Dict[str, Any]] = []
    relevance: float = 1.0


class WorkspaceResponse(BaseModel):
    """Workspace information response."""
    
    path: str
    exists: bool
    is_git: bool = False
    total_files: int = 0
    languages: List[str] = []


class ModelInfo(BaseModel):
    """Information about an Ollama model."""
    
    name: str
    display_name: str
    size: str
    modified_at: Optional[str] = None
    installed: bool = True
    details: Optional[Dict[str, Any]] = None


class ModelsResponse(BaseModel):
    """List of available models."""
    
    models: List[ModelInfo]
    default_model: str

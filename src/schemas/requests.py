"""
Request Schemas
===============
Pydantic models for API request validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request for text/code generation."""
    
    prompt: str = Field(..., description="The prompt for generation")
    model: str = Field(default="qwen2.5-coder:14b", description="Model to use")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    context: Optional[str] = Field(None, description="Conversation context")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Write a Python function to sort a list",
                "model": "qwen2.5-coder:14b",
                "temperature": 0.7
            }
        }


class ChatRequest(BaseModel):
    """Request for chat completion."""
    
    messages: List[dict] = Field(..., description="List of messages")
    model: str = Field(default="qwen2.5-coder:14b")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    stream: bool = Field(default=False, description="Enable streaming response")


class FileReadRequest(BaseModel):
    """Request to read a file."""
    
    path: str = Field(..., description="Path to the file")
    
    class Config:
        json_schema_extra = {
            "example": {"path": "~/projects/myapp/src/main.py"}
        }


class FileWriteRequest(BaseModel):
    """Request to write content to a file."""
    
    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content to write")
    create_backup: bool = Field(default=True, description="Create backup before overwriting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "~/projects/myapp/src/main.py",
                "content": "print('Hello World')",
                "create_backup": True
            }
        }


class FilesRequest(BaseModel):
    """Request for batch file operations."""
    
    paths: List[str] = Field(..., description="List of file paths")
    operation: str = Field(default="read", description="Operation: read, delete")


class DirectoryRequest(BaseModel):
    """Request to list directory contents."""
    
    path: str = Field(default="~", description="Directory path")
    show_hidden: bool = Field(default=False, description="Show hidden files")
    recursive: bool = Field(default=False, description="List recursively")
    max_depth: int = Field(default=3, ge=1, le=10)


class WorkspaceRequest(BaseModel):
    """Request to set workspace path."""
    
    path: str = Field(..., description="Workspace root path")


class SearchRequest(BaseModel):
    """Request to search files."""
    
    query: str = Field(..., description="Search query")
    path: str = Field(default=".", description="Search root path")
    extensions: Optional[List[str]] = Field(None, description="File extensions to search")
    max_results: int = Field(default=100, ge=1, le=1000)
    include_content: bool = Field(default=False, description="Search file contents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "def main",
                "path": "~/projects",
                "extensions": [".py", ".js"],
                "include_content": True
            }
        }

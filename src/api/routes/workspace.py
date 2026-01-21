"""
Workspace Routes
================
Workspace/project management endpoints.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from pathlib import Path

from services.workspace_service import WorkspaceService, get_workspace_service
from services.file_service import FileService, get_file_service
from core.exceptions import WorkspaceError


router = APIRouter(prefix="/api/workspace", tags=["Workspace"])


# === Request Models ===

class SetWorkspaceRequest(BaseModel):
    """Request to set workspace path."""
    path: str = Field(..., description="Workspace root path")


# === Endpoints ===

@router.get("")
@router.get("/")
async def get_workspace(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Get current workspace information.
    
    Returns workspace path, git status, languages, and file counts.
    """
    state = workspace.get_current()
    
    return {
        "path": state.path,
        "exists": state.exists,
        "is_git": state.is_git,
        "git_branch": state.git_branch,
        "total_files": state.total_files,
        "languages": state.languages,
        "home_directory": os.path.expanduser("~"),
        "recent_paths": state.recent_files[:10] if state.recent_files else []
    }


@router.post("")
@router.post("/")
async def set_workspace(
    request: SetWorkspaceRequest,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Set current workspace path.
    
    Scans the directory for project information.
    """
    try:
        state = workspace.set_workspace(request.path)
        
        return {
            "success": True,
            "path": state.path,
            "exists": state.exists,
            "is_git": state.is_git,
            "git_branch": state.git_branch,
            "total_files": state.total_files,
            "languages": state.languages,
            "home_directory": os.path.expanduser("~"),
            "recent_paths": state.recent_files[:10] if state.recent_files else []
        }
        
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=e.detail)


@router.get("/tree")
async def get_file_tree(
    path: str = Query(..., description="Root path"),
    depth: int = Query(default=3, ge=1, le=10),
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    Get file tree structure.
    
    Returns a nested tree of files and directories.
    """
    def build_tree(dir_path: Path, current_depth: int) -> Dict[str, Any]:
        result = {
            "name": dir_path.name or str(dir_path),
            "path": str(dir_path),
            "is_directory": True,
            "children": []
        }
        
        if current_depth > depth:
            return result
        
        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                # Skip hidden files and common non-content directories
                if item.name.startswith('.'):
                    continue
                if item.name in {'node_modules', '__pycache__', 'venv', '.venv', 'build', 'dist', '.git'}:
                    continue
                
                if item.is_dir():
                    child = build_tree(item, current_depth + 1)
                    result["children"].append(child)
                else:
                    result["children"].append({
                        "name": item.name,
                        "path": str(item),
                        "is_directory": False,
                        "size": item.stat().st_size if item.exists() else 0
                    })
        except PermissionError:
            pass
        except Exception as e:
            print(f"Error reading {dir_path}: {e}")
        
        return result
    
    expanded = os.path.expanduser(path)
    root = Path(expanded).resolve()
    
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
    
    return build_tree(root, 1)


@router.get("/recent")
async def get_recent_files(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Get recently accessed files."""
    return {
        "files": workspace.get_recent_files()
    }


@router.delete("/recent")
async def clear_recent_files(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Clear recent files list."""
    workspace.clear_recent_files()
    return {"success": True}


@router.get("/context")
async def get_project_context(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Get project context for AI.
    
    Returns structured information about the current project
    for use in AI prompts.
    """
    return workspace.get_project_context()

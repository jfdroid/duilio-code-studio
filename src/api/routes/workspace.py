"""
Workspace Routes
================
Workspace/project management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel, Field

from services.workspace_service import WorkspaceService, get_workspace_service
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
        "languages": state.languages
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
            "languages": state.languages
        }
        
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=e.detail)


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

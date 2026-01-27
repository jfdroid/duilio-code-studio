"""
File Routes
===========
File system operations endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from services.file_service import FileService, get_file_service
from services.workspace_service import WorkspaceService, get_workspace_service
from core.exceptions import FileNotFoundError as DuilioFileNotFoundError, FileOperationError


import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
router = APIRouter(prefix="/api/files", tags=["Files"])


# === Request Models ===

class ReadFileRequest(BaseModel):
    """Request to read a file."""
    path: str


class WriteFileRequest(BaseModel):
    """Request to write a file."""
    path: str
    content: str
    create_backup: bool = True


class CreateDirectoryRequest(BaseModel):
    """Request to create a directory."""
    path: str


class CreateFileRequest(BaseModel):
    """Request to create a file."""
    path: str
    is_directory: bool = False
    content: str = ""


class DeleteRequest(BaseModel):
    """Request to delete a file/directory."""
    path: str
    recursive: bool = False


class SearchRequest(BaseModel):
    """Request to search files."""
    query: str
    path: str = "."
    extensions: Optional[List[str]] = None
    include_content: bool = False
    max_results: int = 100


# === Endpoints ===

@router.get("/read")
async def read_file(
    path: str = Query(..., description="File path"),
    file_service: FileService = Depends(get_file_service),
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Read file contents.
    
    Returns file content with metadata (size, lines, language).
    """
    try:
        result = file_service.read_file(path)
        workspace.add_recent_file(result.path)
        
        return {
            "path": result.path,
            "content": result.content,
            "encoding": result.encoding,
            "size": result.size,
            "lines": result.lines,
            "modified": result.modified,
            "language": result.language
        }
        
    except DuilioFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)
    except FileOperationError as e:
        raise HTTPException(status_code=500, detail=e.detail)


@router.post("/read")
async def read_file_post(
    request: ReadFileRequest,
    file_service: FileService = Depends(get_file_service),
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Read file (POST version for complex paths)."""
    return await read_file(request.path, file_service, workspace)


@router.post("/write")
async def write_file(
    request: WriteFileRequest,
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    Write content to file.
    
    Creates parent directories if needed.
    Optionally creates backup of existing file.
    """
    try:
        result = file_service.write_file(
            path=request.path,
            content=request.content,
            create_backup=request.create_backup
        )
        return result
        
    except FileOperationError as e:
        raise HTTPException(status_code=500, detail=e.detail)


@router.get("/list")
async def list_directory(
    path: str = Query(default="~", description="Directory path"),
    show_hidden: bool = Query(default=False),
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    List directory contents.
    
    Returns files and subdirectories with metadata.
    """
    try:
        return file_service.list_directory(
            path=path,
            show_hidden=show_hidden
        )
    except DuilioFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)
    except FileOperationError as e:
        raise HTTPException(status_code=500, detail=e.detail)


@router.get("/info")
async def get_file_info(
    path: str = Query(..., description="File or directory path"),
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """Get file/directory information."""
    try:
        info = file_service.get_info(path)
        return {
            "name": info.name,
            "path": info.path,
            "is_dir": info.is_dir,
            "is_file": info.is_file,
            "size": info.size,
            "modified": info.modified,
            "extension": info.extension,
            "permissions": info.permissions
        }
    except DuilioFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)


@router.post("/mkdir")
async def create_directory(
    request: CreateDirectoryRequest,
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """Create directory (and parent directories)."""
    try:
        return file_service.create_directory(request.path)
    except FileOperationError as e:
        raise HTTPException(status_code=500, detail=e.detail)


@router.post("/create")
async def create_file(
    request: CreateFileRequest,
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    Create a new file or directory.
    
    Automatically creates parent directories if they don't exist.
    """
    import os
    from pathlib import Path
    
    try:
        # Expand path
        path = os.path.expanduser(request.path)
        
        if request.is_directory:
            # Create directory
            return file_service.create_directory(path)
        else:
            # Create parent directories if needed
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Create file with content
            result = file_service.write_file(
                path=path,
                content=request.content,
                create_backup=False
            )
            
            return {
                "success": True,
                "path": path,
                "message": f"File created: {path}",
                **result
            }
            
    except FileOperationError as e:
        raise HTTPException(status_code=500, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_file(
    request: DeleteRequest,
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """Delete file or directory."""
    try:
        return file_service.delete(
            path=request.path,
            recursive=request.recursive
        )
    except DuilioFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)
    except FileOperationError as e:
        raise HTTPException(status_code=500, detail=e.detail)


@router.post("/search")
async def search_files(
    request: SearchRequest,
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    Search for files.
    
    Searches by filename and optionally file contents.
    """
    try:
        results = file_service.search(
            query=request.query,
            path=request.path,
            extensions=request.extensions,
            include_content=request.include_content,
            max_results=request.max_results
        )
        return {
            "query": request.query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exists")
async def check_exists(
    path: str = Query(..., description="Path to check"),
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """Check if path exists."""
    exists = file_service.exists(path)
    is_file = file_service.is_file(path) if exists else False
    is_dir = file_service.is_directory(path) if exists else False
    
    return {
        "path": path,
        "exists": exists,
        "is_file": is_file,
        "is_directory": is_dir
    }


@router.get("/autocomplete")
async def autocomplete_path(
    partial: str = Query(..., description="Partial path to autocomplete"),
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    Autocomplete directory paths.
    
    Given a partial path, returns matching directories.
    Used for the Open Folder dialog.
    """
    import os
    from pathlib import Path
    
    # Expand ~ to home directory
    expanded = os.path.expanduser(partial)
    path = Path(expanded)
    
    # Determine parent directory and prefix to search
    if path.is_dir() and partial.endswith('/'):
        search_dir = path
        prefix = ""
    else:
        search_dir = path.parent
        prefix = path.name.lower()
    
    suggestions = []
    
    try:
        if search_dir.exists() and search_dir.is_dir():
            for item in sorted(search_dir.iterdir()):
                # Only show directories
                if not item.is_dir():
                    continue
                # Skip hidden directories (unless user typed a dot)
                if item.name.startswith('.') and not prefix.startswith('.'):
                    continue
                # Match prefix
                if prefix and not item.name.lower().startswith(prefix):
                    continue
                
                # Convert back to ~ notation if in home
                display_path = str(item)
                home = os.path.expanduser("~")
                if display_path.startswith(home):
                    display_path = "~" + display_path[len(home):]
                
                suggestions.append({
                    "path": display_path,
                    "name": item.name,
                    "is_dir": True
                })
                
                if len(suggestions) >= 20:
                    break
    except PermissionError:
        pass
    except Exception:
        pass
    
    return {
        "partial": partial,
        "suggestions": suggestions
    }

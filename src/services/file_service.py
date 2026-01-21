"""
File Service
============
Handles all file system operations.
Single Responsibility: File read/write/list operations.
"""

import os
import shutil
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from core.config import get_settings
from core.exceptions import FileNotFoundError, FileOperationError


# Language detection by extension
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".scala": "scala",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".dockerfile": "dockerfile",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
}


@dataclass
class FileInfo:
    """Information about a file or directory."""
    name: str
    path: str
    is_dir: bool
    is_file: bool
    size: int = 0
    modified: Optional[str] = None
    extension: Optional[str] = None
    permissions: Optional[str] = None


@dataclass
class FileContent:
    """Content and metadata of a file."""
    path: str
    content: str
    encoding: str
    size: int
    lines: int
    modified: Optional[str] = None
    language: Optional[str] = None


class FileService:
    """
    Service for file system operations.
    
    Responsibilities:
    - Read file contents
    - Write file contents (with backup)
    - List directory contents
    - Create/delete files and directories
    - File search
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.max_file_size = self.settings.MAX_FILE_SIZE
        self.create_backups = self.settings.CREATE_BACKUPS
    
    def _expand_path(self, path: str) -> Path:
        """Expand ~ and resolve path."""
        expanded = os.path.expanduser(path)
        return Path(expanded).resolve()
    
    def _get_language(self, path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = path.suffix.lower()
        return LANGUAGE_MAP.get(ext)
    
    def _get_permissions(self, path: Path) -> str:
        """Get file permissions as string."""
        try:
            mode = path.stat().st_mode
            return oct(mode)[-3:]
        except:
            return "---"
    
    def _is_binary(self, path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                return b'\x00' in chunk
        except:
            return False
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        return self._expand_path(path).exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        return self._expand_path(path).is_file()
    
    def is_directory(self, path: str) -> bool:
        """Check if path is a directory."""
        return self._expand_path(path).is_dir()
    
    def get_info(self, path: str) -> FileInfo:
        """
        Get information about a file or directory.
        
        Args:
            path: Path to file/directory
            
        Returns:
            FileInfo with metadata
            
        Raises:
            FileNotFoundError if path doesn't exist
        """
        p = self._expand_path(path)
        
        if not p.exists():
            raise FileNotFoundError(path)
        
        stat = p.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return FileInfo(
            name=p.name,
            path=str(p),
            is_dir=p.is_dir(),
            is_file=p.is_file(),
            size=stat.st_size if p.is_file() else 0,
            modified=modified,
            extension=p.suffix if p.is_file() else None,
            permissions=self._get_permissions(p)
        )
    
    def read_file(
        self,
        path: str,
        encoding: str = "utf-8"
    ) -> FileContent:
        """
        Read file contents.
        
        Args:
            path: Path to file
            encoding: Text encoding
            
        Returns:
            FileContent with content and metadata
            
        Raises:
            FileNotFoundError if file doesn't exist
            FileOperationError if read fails
        """
        p = self._expand_path(path)
        
        if not p.exists():
            raise FileNotFoundError(path)
        
        if not p.is_file():
            raise FileOperationError("read", path, "Path is a directory")
        
        # Check file size
        size = p.stat().st_size
        if size > self.max_file_size:
            raise FileOperationError(
                "read", path,
                f"File too large ({size} bytes). Max: {self.max_file_size}"
            )
        
        # Check if binary
        if self._is_binary(p):
            raise FileOperationError("read", path, "Binary files not supported")
        
        try:
            content = p.read_text(encoding=encoding)
            stat = p.stat()
            
            return FileContent(
                path=str(p),
                content=content,
                encoding=encoding,
                size=size,
                lines=content.count('\n') + 1,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                language=self._get_language(p)
            )
        except UnicodeDecodeError:
            raise FileOperationError("read", path, f"Cannot decode with {encoding}")
        except PermissionError:
            raise FileOperationError("read", path, "Permission denied")
        except Exception as e:
            raise FileOperationError("read", path, str(e))
    
    def write_file(
        self,
        path: str,
        content: str,
        create_backup: Optional[bool] = None,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Write content to file.
        
        Args:
            path: Path to file
            content: Content to write
            create_backup: Create backup of existing file
            encoding: Text encoding
            
        Returns:
            Dict with success status and metadata
            
        Raises:
            FileOperationError if write fails
        """
        p = self._expand_path(path)
        create_backup = create_backup if create_backup is not None else self.create_backups
        
        backup_path = None
        
        try:
            # Create parent directories
            p.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing file
            if p.exists() and create_backup:
                backup_path = f"{p}.backup"
                shutil.copy2(p, backup_path)
            
            # Write content
            p.write_text(content, encoding=encoding)
            
            return {
                "success": True,
                "path": str(p),
                "size": len(content.encode(encoding)),
                "lines": content.count('\n') + 1,
                "backup_created": backup_path is not None,
                "backup_path": backup_path
            }
            
        except PermissionError:
            raise FileOperationError("write", path, "Permission denied")
        except Exception as e:
            # Restore from backup on failure
            if backup_path and Path(backup_path).exists():
                shutil.copy2(backup_path, p)
            raise FileOperationError("write", path, str(e))
    
    def list_directory(
        self,
        path: str = "~",
        show_hidden: bool = False,
        recursive: bool = False,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        List directory contents.
        
        Args:
            path: Directory path
            show_hidden: Include hidden files
            recursive: List recursively
            max_depth: Max recursion depth
            
        Returns:
            Dict with items list and statistics
        """
        p = self._expand_path(path)
        
        if not p.exists():
            raise FileNotFoundError(path)
        
        if not p.is_dir():
            raise FileOperationError("list", path, "Not a directory")
        
        items = []
        total_files = 0
        total_dirs = 0
        total_size = 0
        
        def process_directory(dir_path: Path, depth: int = 0):
            nonlocal total_files, total_dirs, total_size
            
            if recursive and depth > max_depth:
                return
            
            try:
                for item in sorted(dir_path.iterdir()):
                    # Skip hidden files
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    try:
                        stat = item.stat()
                        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        
                        file_info = {
                            "name": item.name,
                            "path": str(item),
                            "is_dir": item.is_dir(),
                            "is_file": item.is_file(),
                            "size": stat.st_size if item.is_file() else 0,
                            "modified": modified,
                            "extension": item.suffix if item.is_file() else None,
                        }
                        
                        if depth == 0:
                            items.append(file_info)
                        
                        if item.is_dir():
                            total_dirs += 1
                            if recursive:
                                process_directory(item, depth + 1)
                        else:
                            total_files += 1
                            total_size += stat.st_size
                            
                    except (PermissionError, OSError):
                        continue
                        
            except PermissionError:
                pass
        
        process_directory(p)
        
        # Sort: directories first, then files
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        return {
            "path": str(p),
            "items": items,
            "total_files": total_files,
            "total_dirs": total_dirs,
            "total_size": total_size
        }
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory and parent directories."""
        p = self._expand_path(path)
        
        try:
            p.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(p)}
        except PermissionError:
            raise FileOperationError("mkdir", path, "Permission denied")
        except Exception as e:
            raise FileOperationError("mkdir", path, str(e))
    
    def delete(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Delete file or directory.
        
        Args:
            path: Path to delete
            recursive: Delete directories recursively
        """
        p = self._expand_path(path)
        
        if not p.exists():
            raise FileNotFoundError(path)
        
        try:
            if p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                else:
                    p.rmdir()  # Only works if empty
            else:
                p.unlink()
            
            return {"success": True, "path": str(p), "deleted": True}
            
        except OSError as e:
            raise FileOperationError("delete", path, str(e))
    
    def search(
        self,
        query: str,
        path: str = ".",
        extensions: Optional[List[str]] = None,
        include_content: bool = False,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for files matching query.
        
        Args:
            query: Search query
            path: Search root
            extensions: Filter by extensions
            include_content: Search file contents
            max_results: Maximum results
            
        Returns:
            List of matching files with match details
        """
        p = self._expand_path(path)
        results = []
        query_lower = query.lower()
        
        def search_directory(dir_path: Path):
            if len(results) >= max_results:
                return
            
            try:
                for item in dir_path.iterdir():
                    if len(results) >= max_results:
                        return
                    
                    # Skip hidden
                    if item.name.startswith('.'):
                        continue
                    
                    if item.is_dir():
                        # Skip common non-content directories
                        if item.name in {'node_modules', '__pycache__', '.git', 'venv', '.venv'}:
                            continue
                        search_directory(item)
                    
                    elif item.is_file():
                        # Filter by extension
                        if extensions:
                            if item.suffix.lower() not in [e.lower() for e in extensions]:
                                continue
                        
                        # Check filename match
                        if query_lower in item.name.lower():
                            results.append({
                                "path": str(item),
                                "name": item.name,
                                "match_type": "filename",
                                "relevance": 1.0
                            })
                            continue
                        
                        # Check content
                        if include_content and not self._is_binary(item):
                            try:
                                content = item.read_text(errors='ignore')
                                if query_lower in content.lower():
                                    # Find matching lines
                                    matches = []
                                    for i, line in enumerate(content.split('\n'), 1):
                                        if query_lower in line.lower():
                                            matches.append({
                                                "line": i,
                                                "content": line.strip()[:200]
                                            })
                                            if len(matches) >= 5:
                                                break
                                    
                                    results.append({
                                        "path": str(item),
                                        "name": item.name,
                                        "match_type": "content",
                                        "matches": matches,
                                        "relevance": 0.8
                                    })
                            except:
                                pass
                                
            except PermissionError:
                pass
        
        search_directory(p)
        return results


# Singleton instance
_file_service: Optional[FileService] = None


def get_file_service() -> FileService:
    """Get singleton file service instance."""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service

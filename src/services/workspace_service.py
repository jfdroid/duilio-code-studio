"""
Workspace Service
=================
Handles workspace/project management.
Single Responsibility: Workspace state and project context.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

from core.config import get_settings
from core.exceptions import WorkspaceError


@dataclass
class WorkspaceState:
    """Current workspace state."""
    path: str = ""
    exists: bool = False
    is_git: bool = False
    git_branch: Optional[str] = None
    total_files: int = 0
    languages: List[str] = field(default_factory=list)
    recent_files: List[str] = field(default_factory=list)


class WorkspaceService:
    """
    Service for workspace management.
    
    Responsibilities:
    - Track current workspace
    - Persist workspace state
    - Detect project type (git, languages)
    - Manage recent files
    """
    
    MAX_RECENT_FILES = 20
    
    def __init__(self):
        self.settings = get_settings()
        self.state_file = self.settings.WORKSPACE_FILE
        self._state: Optional[WorkspaceState] = None
    
    def _load_state(self) -> WorkspaceState:
        """Load workspace state from file."""
        if self._state is not None:
            return self._state
        
        if self.state_file and self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._state = WorkspaceState(**data)
            except:
                self._state = WorkspaceState()
        else:
            self._state = WorkspaceState()
        
        return self._state
    
    def _save_state(self) -> None:
        """Save workspace state to file."""
        if self._state and self.state_file:
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                self.state_file.write_text(json.dumps(asdict(self._state), indent=2))
            except:
                pass
    
    def _detect_git(self, path: Path) -> tuple[bool, Optional[str]]:
        """Detect if path is a git repository and get branch."""
        git_dir = path / ".git"
        if not git_dir.exists():
            return False, None
        
        # Try to get current branch
        head_file = git_dir / "HEAD"
        if head_file.exists():
            try:
                content = head_file.read_text().strip()
                if content.startswith("ref: refs/heads/"):
                    return True, content.replace("ref: refs/heads/", "")
            except:
                pass
        
        return True, None
    
    def _detect_languages(self, path: Path) -> List[str]:
        """Detect programming languages used in workspace."""
        extension_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".kt": "Kotlin",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".cpp": "C++",
            ".c": "C",
        }
        
        found = set()
        count = 0
        
        def scan(dir_path: Path, depth: int = 0):
            nonlocal count
            if depth > 3 or count > 500:
                return
            
            try:
                for item in dir_path.iterdir():
                    if item.name.startswith('.'):
                        continue
                    if item.name in {'node_modules', '__pycache__', 'venv', '.venv', 'build', 'dist'}:
                        continue
                    
                    if item.is_dir():
                        scan(item, depth + 1)
                    elif item.is_file():
                        count += 1
                        ext = item.suffix.lower()
                        if ext in extension_map:
                            found.add(extension_map[ext])
            except:
                pass
        
        scan(path)
        return sorted(list(found))
    
    def _count_files(self, path: Path) -> int:
        """Count files in workspace."""
        count = 0
        
        def scan(dir_path: Path, depth: int = 0):
            nonlocal count
            if depth > 5 or count > 10000:
                return
            
            try:
                for item in dir_path.iterdir():
                    if item.name.startswith('.'):
                        continue
                    if item.name in {'node_modules', '__pycache__', 'venv', '.venv'}:
                        continue
                    
                    if item.is_dir():
                        scan(item, depth + 1)
                    else:
                        count += 1
            except:
                pass
        
        scan(path)
        return count
    
    def get_current(self) -> WorkspaceState:
        """Get current workspace state."""
        return self._load_state()
    
    def set_workspace(self, path: str) -> WorkspaceState:
        """
        Set current workspace path.
        
        Args:
            path: Workspace root path
            
        Returns:
            Updated WorkspaceState
            
        Raises:
            WorkspaceError if path is invalid
        """
        expanded = os.path.expanduser(path)
        p = Path(expanded).resolve()
        
        if not p.exists():
            raise WorkspaceError(f"Path does not exist: {path}", path)
        
        if not p.is_dir():
            raise WorkspaceError(f"Path is not a directory: {path}", path)
        
        is_git, branch = self._detect_git(p)
        languages = self._detect_languages(p)
        total_files = self._count_files(p)
        
        self._state = WorkspaceState(
            path=str(p),
            exists=True,
            is_git=is_git,
            git_branch=branch,
            total_files=total_files,
            languages=languages,
            recent_files=self._load_state().recent_files
        )
        
        self._save_state()
        return self._state
    
    def add_recent_file(self, file_path: str) -> None:
        """Add file to recent files list."""
        state = self._load_state()
        
        # Remove if already in list
        if file_path in state.recent_files:
            state.recent_files.remove(file_path)
        
        # Add to front
        state.recent_files.insert(0, file_path)
        
        # Trim list
        state.recent_files = state.recent_files[:self.MAX_RECENT_FILES]
        
        self._save_state()
    
    def get_recent_files(self) -> List[str]:
        """Get list of recently accessed files."""
        return self._load_state().recent_files
    
    def clear_recent_files(self) -> None:
        """Clear recent files list."""
        state = self._load_state()
        state.recent_files = []
        self._save_state()
    
    def get_project_context(self) -> Dict[str, Any]:
        """
        Get context about current project for AI.
        
        Returns:
            Dict with project structure and metadata
        """
        state = self._load_state()
        
        if not state.path or not state.exists:
            return {"has_workspace": False}
        
        return {
            "has_workspace": True,
            "root_path": state.path,
            "is_git": state.is_git,
            "git_branch": state.git_branch,
            "languages": state.languages,
            "total_files": state.total_files,
            "recent_files": state.recent_files[:5]
        }


# Singleton instance
_workspace_service: Optional[WorkspaceService] = None


def get_workspace_service() -> WorkspaceService:
    """Get singleton workspace service instance."""
    global _workspace_service
    if _workspace_service is None:
        _workspace_service = WorkspaceService()
    return _workspace_service

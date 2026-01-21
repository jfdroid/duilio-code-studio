"""
Git Service
===========
Full Git integration for DuilioCode.
Execute git commands safely from the chat interface.
"""

import os
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class GitCommandType(Enum):
    """Types of git commands."""
    STATUS = "status"
    ADD = "add"
    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    BRANCH = "branch"
    CHECKOUT = "checkout"
    MERGE = "merge"
    DIFF = "diff"
    LOG = "log"
    STASH = "stash"
    RESET = "reset"
    FETCH = "fetch"
    CLONE = "clone"
    INIT = "init"


@dataclass
class GitResult:
    """Result of a git operation."""
    success: bool
    command: str
    output: str
    error: str = ""
    return_code: int = 0


class GitService:
    """
    Service for git operations.
    
    Features:
    - Safe command execution
    - Repository detection
    - Branch management
    - Commit and push
    - Diff and status
    - Log and history
    """
    
    # Commands that are safe to execute
    SAFE_COMMANDS = {
        'status', 'log', 'diff', 'branch', 'remote', 'fetch',
        'show', 'ls-files', 'ls-tree', 'rev-parse', 'describe',
        'config', 'stash'
    }
    
    # Commands that modify repository (require confirmation in UI)
    MODIFY_COMMANDS = {
        'add', 'commit', 'push', 'pull', 'checkout', 'merge',
        'reset', 'revert', 'cherry-pick', 'rebase', 'init', 'clone'
    }
    
    # Dangerous commands (blocked or require extra confirmation)
    DANGEROUS_COMMANDS = {
        'clean', 'reset --hard', 'push --force', 'push -f'
    }
    
    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize git service with optional workspace path."""
        self.workspace_path = workspace_path
        self._git_available = self._check_git_available()
    
    def _check_git_available(self) -> bool:
        """Check if git is available in PATH."""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _get_repo_root(self, path: str) -> Optional[str]:
        """Get the root directory of the git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                cwd=path,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def is_git_repo(self, path: Optional[str] = None) -> bool:
        """Check if path is inside a git repository."""
        check_path = path or self.workspace_path
        if not check_path:
            return False
        return self._get_repo_root(check_path) is not None
    
    def get_repo_info(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive repository information."""
        repo_path = path or self.workspace_path
        
        if not repo_path or not self.is_git_repo(repo_path):
            return {"is_repo": False}
        
        info = {"is_repo": True, "path": repo_path}
        
        # Get current branch
        branch_result = self._execute(['git', 'branch', '--show-current'], repo_path)
        if branch_result.success:
            info["current_branch"] = branch_result.output.strip()
        
        # Get remote URL
        remote_result = self._execute(['git', 'remote', 'get-url', 'origin'], repo_path)
        if remote_result.success:
            info["remote_url"] = remote_result.output.strip()
        
        # Get status summary
        status_result = self._execute(['git', 'status', '--porcelain'], repo_path)
        if status_result.success:
            lines = status_result.output.strip().split('\n') if status_result.output.strip() else []
            info["modified_files"] = len([l for l in lines if l.startswith(' M') or l.startswith('M ')])
            info["staged_files"] = len([l for l in lines if l.startswith('A ') or l.startswith('M ')])
            info["untracked_files"] = len([l for l in lines if l.startswith('??')])
            info["total_changes"] = len(lines)
            info["is_clean"] = len(lines) == 0
        
        # Get last commit
        log_result = self._execute(
            ['git', 'log', '-1', '--format=%H|%s|%an|%ar'],
            repo_path
        )
        if log_result.success and log_result.output.strip():
            parts = log_result.output.strip().split('|')
            if len(parts) >= 4:
                info["last_commit"] = {
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "author": parts[2],
                    "time": parts[3]
                }
        
        # Get all branches
        branches_result = self._execute(['git', 'branch', '-a'], repo_path)
        if branches_result.success:
            branches = [b.strip().replace('* ', '') for b in branches_result.output.strip().split('\n') if b.strip()]
            info["branches"] = branches[:20]  # Limit to 20
        
        return info
    
    def _execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        timeout: int = 60
    ) -> GitResult:
        """Execute a git command safely."""
        work_dir = cwd or self.workspace_path
        
        if not work_dir:
            return GitResult(
                success=False,
                command=' '.join(command),
                output="",
                error="No workspace path specified"
            )
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=work_dir,
                timeout=timeout,
                env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}  # Disable prompts
            )
            
            return GitResult(
                success=result.returncode == 0,
                command=' '.join(command),
                output=result.stdout,
                error=result.stderr,
                return_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return GitResult(
                success=False,
                command=' '.join(command),
                output="",
                error="Command timed out"
            )
        except Exception as e:
            return GitResult(
                success=False,
                command=' '.join(command),
                output="",
                error=str(e)
            )
    
    # === High-Level Git Operations ===
    
    def status(self, path: Optional[str] = None) -> GitResult:
        """Get repository status."""
        return self._execute(['git', 'status'], path)
    
    def status_short(self, path: Optional[str] = None) -> GitResult:
        """Get short status output."""
        return self._execute(['git', 'status', '-s'], path)
    
    def add(self, files: List[str] = None, all: bool = False, path: Optional[str] = None) -> GitResult:
        """Stage files for commit."""
        if all:
            return self._execute(['git', 'add', '-A'], path)
        elif files:
            return self._execute(['git', 'add'] + files, path)
        else:
            return self._execute(['git', 'add', '.'], path)
    
    def commit(self, message: str, path: Optional[str] = None) -> GitResult:
        """Create a commit with the given message."""
        if not message:
            return GitResult(
                success=False,
                command="git commit",
                output="",
                error="Commit message is required"
            )
        return self._execute(['git', 'commit', '-m', message], path)
    
    def push(
        self,
        remote: str = 'origin',
        branch: Optional[str] = None,
        path: Optional[str] = None
    ) -> GitResult:
        """Push commits to remote."""
        cmd = ['git', 'push', remote]
        if branch:
            cmd.append(branch)
        return self._execute(cmd, path)
    
    def pull(
        self,
        remote: str = 'origin',
        branch: Optional[str] = None,
        path: Optional[str] = None
    ) -> GitResult:
        """Pull changes from remote."""
        cmd = ['git', 'pull', remote]
        if branch:
            cmd.append(branch)
        return self._execute(cmd, path)
    
    def fetch(self, remote: str = 'origin', path: Optional[str] = None) -> GitResult:
        """Fetch changes from remote."""
        return self._execute(['git', 'fetch', remote], path)
    
    def branch_list(self, path: Optional[str] = None) -> GitResult:
        """List all branches."""
        return self._execute(['git', 'branch', '-a'], path)
    
    def branch_create(self, name: str, path: Optional[str] = None) -> GitResult:
        """Create a new branch."""
        return self._execute(['git', 'branch', name], path)
    
    def branch_delete(self, name: str, force: bool = False, path: Optional[str] = None) -> GitResult:
        """Delete a branch."""
        flag = '-D' if force else '-d'
        return self._execute(['git', 'branch', flag, name], path)
    
    def checkout(self, target: str, create: bool = False, path: Optional[str] = None) -> GitResult:
        """Checkout a branch or commit."""
        if create:
            return self._execute(['git', 'checkout', '-b', target], path)
        return self._execute(['git', 'checkout', target], path)
    
    def merge(self, branch: str, path: Optional[str] = None) -> GitResult:
        """Merge a branch into current branch."""
        return self._execute(['git', 'merge', branch], path)
    
    def diff(
        self,
        staged: bool = False,
        file: Optional[str] = None,
        path: Optional[str] = None
    ) -> GitResult:
        """Get diff of changes."""
        cmd = ['git', 'diff']
        if staged:
            cmd.append('--staged')
        if file:
            cmd.append(file)
        return self._execute(cmd, path)
    
    def log(
        self,
        count: int = 10,
        oneline: bool = True,
        path: Optional[str] = None
    ) -> GitResult:
        """Get commit log."""
        cmd = ['git', 'log', f'-{count}']
        if oneline:
            cmd.append('--oneline')
        return self._execute(cmd, path)
    
    def stash(self, action: str = 'push', message: Optional[str] = None, path: Optional[str] = None) -> GitResult:
        """Stash operations (push, pop, list, apply, drop)."""
        cmd = ['git', 'stash', action]
        if action == 'push' and message:
            cmd.extend(['-m', message])
        return self._execute(cmd, path)
    
    def reset(
        self,
        mode: str = 'mixed',
        target: str = 'HEAD',
        path: Optional[str] = None
    ) -> GitResult:
        """Reset to a specific commit."""
        cmd = ['git', 'reset', f'--{mode}', target]
        return self._execute(cmd, path)
    
    def init(self, path: Optional[str] = None) -> GitResult:
        """Initialize a new repository."""
        return self._execute(['git', 'init'], path)
    
    def clone(self, url: str, dest: Optional[str] = None, path: Optional[str] = None) -> GitResult:
        """Clone a repository."""
        cmd = ['git', 'clone', url]
        if dest:
            cmd.append(dest)
        return self._execute(cmd, path)
    
    # === AI-Friendly Command Parser ===
    
    def parse_natural_command(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse natural language git command.
        
        Examples:
        - "commit with message 'fix bug'" → ('commit', {'message': 'fix bug'})
        - "push to origin main" → ('push', {'remote': 'origin', 'branch': 'main'})
        - "create branch feature/login" → ('branch_create', {'name': 'feature/login'})
        """
        text_lower = text.lower()
        
        # Commit patterns
        if 'commit' in text_lower:
            # Extract message from quotes
            import re
            match = re.search(r'["\'](.+?)["\']', text)
            message = match.group(1) if match else "Auto commit"
            return ('commit', {'message': message})
        
        # Push patterns
        if 'push' in text_lower:
            parts = text_lower.split()
            remote = 'origin'
            branch = None
            for i, p in enumerate(parts):
                if p == 'to' and i + 1 < len(parts):
                    remote = parts[i + 1]
                if p in ('main', 'master', 'develop') or p.startswith('feature/') or p.startswith('bugfix/'):
                    branch = p
            return ('push', {'remote': remote, 'branch': branch})
        
        # Pull patterns
        if 'pull' in text_lower:
            return ('pull', {'remote': 'origin'})
        
        # Branch patterns
        if 'branch' in text_lower or 'criar branch' in text_lower or 'create branch' in text_lower:
            import re
            match = re.search(r'(feature/|bugfix/|hotfix/|release/)?\w+[-/]?\w*', text)
            if match:
                return ('branch_create', {'name': match.group()})
        
        # Checkout patterns
        if 'checkout' in text_lower or 'switch to' in text_lower or 'mudar para' in text_lower:
            parts = text.split()
            for p in parts:
                if '/' in p or p in ('main', 'master', 'develop'):
                    return ('checkout', {'target': p})
        
        # Status
        if 'status' in text_lower:
            return ('status', {})
        
        # Diff
        if 'diff' in text_lower or 'changes' in text_lower or 'mudanças' in text_lower:
            return ('diff', {'staged': 'staged' in text_lower})
        
        # Log
        if 'log' in text_lower or 'history' in text_lower or 'histórico' in text_lower:
            return ('log', {'count': 10})
        
        return ('unknown', {'raw': text})
    
    def execute_natural_command(self, text: str, path: Optional[str] = None) -> GitResult:
        """Execute a git command from natural language."""
        action, params = self.parse_natural_command(text)
        
        if action == 'commit':
            return self.commit(params.get('message', 'Auto commit'), path)
        elif action == 'push':
            return self.push(params.get('remote', 'origin'), params.get('branch'), path)
        elif action == 'pull':
            return self.pull(params.get('remote', 'origin'), params.get('branch'), path)
        elif action == 'branch_create':
            return self.branch_create(params.get('name'), path)
        elif action == 'checkout':
            return self.checkout(params.get('target'), path)
        elif action == 'status':
            return self.status(path)
        elif action == 'diff':
            return self.diff(params.get('staged', False), path=path)
        elif action == 'log':
            return self.log(params.get('count', 10), path=path)
        else:
            return GitResult(
                success=False,
                command=text,
                output="",
                error=f"Could not parse git command: {text}"
            )


# Singleton instance
_git_service: Optional[GitService] = None


def get_git_service(workspace_path: Optional[str] = None) -> GitService:
    """Get git service instance."""
    global _git_service
    if _git_service is None or workspace_path != _git_service.workspace_path:
        _git_service = GitService(workspace_path)
    return _git_service

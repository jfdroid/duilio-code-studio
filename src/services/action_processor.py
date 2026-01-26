"""
Action Processor Service
========================
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
Processes agent actions (create-file, modify-file, run-command) from AI responses.
This allows backend to process actions directly, not just frontend.
"""

import re
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
from services.file_service import FileService, get_file_service
from services.workspace_service import WorkspaceService, get_workspace_service
from services.dependency_graph import FileDependencyGraph
from services.intelligent_validator import IntelligentValidator, get_intelligent_validator
from services.path_security import PathSecurity
from core.logger import get_logger


class ActionProcessor:
    """
    Processes agent actions from AI responses.
    
    Actions supported:
    - create-file:path\ncontent
    - modify-file:path\ncontent
    - delete-file:path
    - remove-file:path
    - delete-directory:path
    - run-command\ncommand
    """
    
    def __init__(
        self, 
        file_service: Optional[FileService] = None, 
        workspace_service: Optional[WorkspaceService] = None,
        conversation_memory: Optional[Any] = None,
        ollama_service: Optional[Any] = None
    ) -> None:
        # Cache for normalized paths to avoid repeated calculations
        # Key: (file_path, workspace_path), Value: normalized_path
        self._path_cache: Dict[Tuple[str, Optional[str]], str] = {}
        
        # Cache for extracted actions to avoid re-parsing same response
        # Key: MD5 hash of response_text, Value: List of actions
        self._action_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Limit cache size to prevent memory issues
        self._max_cache_size = 1000
        self._max_path_cache_size = 2000  # Path cache can be larger (paths are smaller)
        
        self.file_service = file_service or get_file_service()
        self.workspace_service = workspace_service or get_workspace_service()
        
        # Try to get ollama_service if not provided
        if ollama_service is None:
            try:
                from services.ollama_service import get_ollama_service
                ollama_service = get_ollama_service()
            except Exception:
                ollama_service = None
        
        self.ollama_service = ollama_service
        
        # Import ConversationMemory if not provided
        if conversation_memory is None:
            try:
                from services.conversation_memory import ConversationMemory
                self.conversation_memory = ConversationMemory()
            except ImportError:
                self.conversation_memory = None
        else:
            self.conversation_memory = conversation_memory
        
        # Initialize dependency graph for ordering files
        self.dependency_graph = FileDependencyGraph()
        
        # Initialize language detector (generic, AI-powered)
        try:
            from services.language_detector import get_language_detector
            self.language_detector = get_language_detector(ollama_service)
        except Exception:
            self.language_detector = None
        
        # Initialize intelligent validator
        try:
            self.validator = get_intelligent_validator(ollama_service)
        except Exception:
            self.validator = None
        
        # Initialize logger
        self.logger = get_logger()
    
    def extract_actions(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract all actions from AI response.
        
        Supports multiple formats and variations:
        - ```create-file:path\ncontent```
        - ```create-file:path\n\ncontent``` (with blank line)
        - ```create-file path\ncontent``` (space instead of colon)
        - Similar variations for modify-file and run-command
        
        Returns:
            List of action dictionaries with type, path/content, and metadata
        """
        # Check cache first (use hash of response text as key)
        cache_key = hashlib.md5(response_text.encode()).hexdigest()
        if cache_key in self._action_cache:
            return self._action_cache[cache_key]
        
        actions = []
        
        # More flexible patterns - support colon, space, or newline after action type
        # Pattern 1: Standard format with colon
        create_patterns = [
            r'```create-file:([^\n]+)\n([\s\S]*?)```',  # Standard
            r'```create-file\s+([^\n]+)\n([\s\S]*?)```',  # Space instead of colon
            r'```create-file:([^\n]+)\n\n([\s\S]*?)```',  # With blank line
        ]
        
        # Also handle cases where create-file appears without opening ``` (after create-directory)
        # Pattern: create-file:path\ncontent (ends at next ```create-file:, ```create-directory:, ```, or end of text)
        fallback_pattern = r'(?:^|\n)create-file:([^\n]+)\n([\s\S]*?)(?=\n```create-file:|\n```create-directory:|\n```[a-z]|```\s*$|$)'
        
        for pattern in create_patterns:
            for match in re.finditer(pattern, response_text):
                path = match.group(1).strip()
                content = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                # Clean up path (remove quotes if present)
                path = path.strip('"\'')
                
                # CRITICAL: Validate path is not empty or just extension
                if not path:
                    self.logger.warning(
                        "Empty path extracted. Skipping.",
                        context={"action_type": "create-file", "raw_path": match.group(1) if match else None}
                    )
                    continue
                
                # Check if path is just an extension (e.g., ".txt", ".js")
                # This happens when AI generates wrong format
                path_basename = path.split('/')[-1].split('\\')[-1]  # Get filename from path
                # Invalid if basename is just ".extension" (no filename, only extension)
                # BUT allow files like .gitignore, .env which are hidden files with full names
                if path_basename.startswith('.'):
                    # Check if it's just an extension by looking at the part after the first dot
                    # ".txt" -> invalid (no filename, just extension)
                    # ".gitignore" -> valid (filename is "gitignore")
                    # ".env.local" -> valid (filename is "env")
                    after_first_dot = path_basename[1:]  # Everything after the first dot
                    # Use AI-powered language detector to check if it's a valid file extension
                    if '.' not in after_first_dot and self._is_just_extension(after_first_dot):
                        # Path is just extension like ".txt" - this is invalid
                        self.logger.warning(
                            f"Invalid path (just extension): '{path}'. Skipping.",
                            context={"action_type": "create-file", "invalid_path": path}
                        )
                        continue
                
                # Detect if this is a directory creation
                is_directory = (
                    not content or 
                    not content.strip() or
                    path.endswith('/') or
                    '.gitkeep' in path.lower() or
                    (len(content.strip()) < 10 and 'keep' in content.lower())
                )
                
                # Avoid duplicates
                if not any(a.get('path') == path and a.get('type') == 'create-file' for a in actions):
                    actions.append({
                        'type': 'create-file',
                        'path': path,
                        'content': content,
                        'is_directory': is_directory,
                        'raw_match': match.group(0)
                    })
        
        # Fallback: Extract create-file without opening ``` (handles cases where AI generates wrong format)
        # This happens when AI generates: ```create-directory:dir\n\ncreate-file:path\ncontent
        for match in re.finditer(fallback_pattern, response_text, re.MULTILINE):
            path = match.group(1).strip()
            content = match.group(2).strip() if len(match.groups()) > 1 else ""
            
            # Clean up path
            path = path.strip('"\'')
            
            # Skip if already extracted by standard patterns
            if any(a.get('path') == path and a.get('type') == 'create-file' for a in actions):
                continue
            
            # Validate path
            if not path:
                continue
            
            # Check if path is just an extension
            path_basename = path.split('/')[-1].split('\\')[-1]
            if path_basename.startswith('.'):
                after_first_dot = path_basename[1:]
                if '.' not in after_first_dot and self._is_just_extension(after_first_dot):
                    continue
            
            # Detect if this is a directory creation
            is_directory = (
                not content or 
                not content.strip() or
                path.endswith('/') or
                '.gitkeep' in path.lower() or
                (len(content.strip()) < 10 and 'keep' in content.lower())
            )
            
            actions.append({
                'type': 'create-file',
                'path': path,
                'content': content,
                'is_directory': is_directory,
                'raw_match': match.group(0)
            })
        
        # Extract create-directory actions (explicit directory creation)
        directory_patterns = [
            r'```create-directory:([^\n]+)```',
            r'```create-directory:([^\n]+)\n```',
            r'```create-directory\s+([^\n]+)```',
            r'```create-directory\s+([^\n]+)\n```',
            r'```create-folder:([^\n]+)```',
            r'```create-folder:([^\n]+)\n```',
            # Handle cases where create-directory is followed by newline and then create-file blocks
            r'```create-directory:([^\n]+)\n\n',  # Directory followed by blank line (may have files after)
        ]
        
        for pattern in directory_patterns:
            for match in re.finditer(pattern, response_text):
                path = match.group(1).strip().strip('"\'')
                
                # Avoid duplicates
                if not any(a.get('path') == path and a.get('type') == 'create-directory' for a in actions):
                    actions.append({
                        'type': 'create-directory',
                        'path': path,
                        'raw_match': match.group(0)
                    })
        
        # Extract modify-file actions with flexible patterns
        modify_patterns = [
            r'```modify-file:([^\n]+)\n([\s\S]*?)```',
            r'```modify-file\s+([^\n]+)\n([\s\S]*?)```',
            r'```modify-file:([^\n]+)\n\n([\s\S]*?)```',
        ]
        
        for pattern in modify_patterns:
            for match in re.finditer(pattern, response_text):
                path = match.group(1).strip().strip('"\'')
                content = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                # Avoid duplicates
                if not any(a.get('path') == path and a.get('type') == 'modify-file' for a in actions):
                    actions.append({
                        'type': 'modify-file',
                        'path': path,
                        'content': content,
                        'raw_match': match.group(0)
                    })
        
        # Extract delete-file/remove-file actions
        delete_patterns = [
            r'```delete-file:([^\n`]+)```',
            r'```delete-file\s+([^\n`]+)```',
            r'```remove-file:([^\n`]+)```',
            r'```remove-file\s+([^\n`]+)```',
            r'```delete-directory:([^\n`]+)```',
            r'```delete-directory\s+([^\n`]+)```',
            r'```delete-file:([^\n`]+)\n```',  # With newline
            r'```delete-directory:([^\n`]+)\n```',  # With newline
        ]
        
        for pattern in delete_patterns:
            for match in re.finditer(pattern, response_text, re.MULTILINE):
                path = match.group(1).strip().strip('"\'')
                action_type = 'delete-file'
                if 'directory' in pattern:
                    action_type = 'delete-directory'
                
                # Avoid duplicates
                if not any(a.get('path') == path and a.get('type') == action_type for a in actions):
                    actions.append({
                        'type': action_type,
                        'path': path,
                        'raw_match': match.group(0)
                    })
        
        # Extract run-command actions
        command_patterns = [
            r'```run-command\n([\s\S]*?)```',
            r'```run-command:\n([\s\S]*?)```',
            r'```run-command\s+([\s\S]*?)```',
        ]
        
        for pattern in command_patterns:
            for match in re.finditer(pattern, response_text):
                command = match.group(1).strip()
                
                # Avoid duplicates (check by command content)
                if not any(a.get('command') == command and a.get('type') == 'run-command' for a in actions):
                    actions.append({
                        'type': 'run-command',
                        'command': command,
                        'raw_match': match.group(0)
                    })
        
        # Log extraction results for debugging
        if len(actions) == 0:
            self.logger.warning(
                "No actions extracted from response",
                context={
                    "response_length": len(response_text),
                    "response_preview": response_text[:500],
                    "has_create_file_pattern": bool(re.search(r'```create-file:', response_text)),
                    "has_create_directory_pattern": bool(re.search(r'```create-directory:', response_text)),
                    "has_modify_pattern": bool(re.search(r'```modify-file:', response_text)),
                    "has_delete_pattern": bool(re.search(r'```delete-file:', response_text)),
                }
            )
        else:
            self.logger.debug(
                f"Extracted {len(actions)} actions",
                context={
                    "action_types": [a.get('type') for a in actions],
                    "action_paths": [a.get('path', 'N/A') for a in actions],
                    "response_preview": response_text[:300]
                }
            )
        
        # Cache the result (with size limit)
        if len(self._action_cache) >= self._max_cache_size:
            # Remove oldest entries (remove 10% when full for better performance)
            remove_count = max(1, self._max_cache_size // 10)
            keys_to_remove = list(self._action_cache.keys())[:remove_count]
            for key in keys_to_remove:
                del self._action_cache[key]
            self.logger.debug(
                f"Action cache full, removed {remove_count} oldest entries",
                context={"cache_size": len(self._action_cache), "max_size": self._max_cache_size}
            )
        
        self._action_cache[cache_key] = actions
        return actions
    
    def _cache_path_result(self, cache_key: Tuple[str, Optional[str]], result: str) -> None:
        """
        Cache path normalization result with eviction if needed.
        
        Args:
            cache_key: Cache key (file_path, workspace_path)
            result: Normalized path result
        """
        # Check if path cache is full and evict if needed
        if len(self._path_cache) >= self._max_path_cache_size:
            # Remove oldest entries (remove 10% when full)
            remove_count = max(1, self._max_path_cache_size // 10)
            keys_to_remove = list(self._path_cache.keys())[:remove_count]
            for key in keys_to_remove:
                del self._path_cache[key]
            self.logger.debug(
                f"Path cache full, removed {remove_count} oldest entries",
                context={"cache_size": len(self._path_cache), "max_size": self._max_path_cache_size}
            )
        
        self._path_cache[cache_key] = result
    
    def normalize_path(self, file_path: str, workspace_path: str = None) -> str:
        """
        Normalize file path intelligently with security validation.
        
        Rules:
        - If absolute and outside workspace: use as-is (if allowed)
        - If relative: join with workspace
        - Handle ~ expansion
        - Clean up path (remove extra slashes, normalize separators)
        - Handle both forward and backward slashes
        - CRITICAL: Avoid path duplication
        - SECURITY: Validate path for traversal attacks
        
        Uses caching to avoid repeated calculations for the same path.
        """
        if not file_path:
            return file_path
        
        # Check cache first
        cache_key = (file_path, workspace_path)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]
        
        # Security validation
        is_valid, error = PathSecurity.validate_path(
            file_path,
            workspace_path,
            allow_absolute=True  # Allow absolute paths for external projects
        )
        if not is_valid:
            self.logger.warning(
                f"Path validation failed: {error}",
                context={"file_path": file_path, "workspace_path": workspace_path}
            )
            # Don't block, but log the issue - let the caller decide
        
        # Remove quotes if present
        file_path = file_path.strip().strip('"\'')
        
        # Expand ~
        if file_path.startswith('~'):
            file_path = os.path.expanduser(file_path)
        
        # Normalize slashes (handle both / and \)
        file_path = file_path.replace('\\', '/')
        
        # CRITICAL: Detect and fix path duplication BEFORE normalizing
        # Pattern: /Users/.../Users/... (duplication of base path)
        if '/Users/' in file_path:
            parts = file_path.split('/Users/')
            if len(parts) > 2:
                # Duplication detected - keep only the last occurrence
                # Find the longest valid path starting from /Users/
                for i in range(len(parts) - 1, 0, -1):
                    potential_path = '/Users/' + '/Users/'.join(parts[i:])
                    if os.path.isabs(potential_path):
                        file_path = potential_path
                        break
        
        # Also check for workspace path duplication
        if workspace_path:
            workspace_abs = os.path.abspath(workspace_path)
            # Check if workspace path appears twice in file_path
            if workspace_abs in file_path:
                count = file_path.count(workspace_abs)
                if count > 1:
                    # Duplication detected - keep only the last occurrence
                    last_index = file_path.rfind(workspace_abs)
                    file_path = file_path[last_index:]
        
        # Remove duplicate slashes (but preserve leading // for UNC paths)
        if file_path.startswith('//'):
            file_path = '//' + re.sub(r'/+', '/', file_path[2:])
        else:
            file_path = re.sub(r'/+', '/', file_path)
        
        # If path is already absolute, resolve it first
        if os.path.isabs(file_path):
            file_abs = os.path.abspath(file_path)
            
            if workspace_path:
                workspace_abs = os.path.abspath(workspace_path)
                
                # CRITICAL: Check if path already contains workspace to avoid duplication
                if file_abs.startswith(workspace_abs):
                    # Path is within workspace - check if it's a duplicate
                    try:
                        rel_path = os.path.relpath(file_abs, workspace_abs)
                        # If relative path doesn't go up, it's within workspace
                        if not rel_path.startswith('..'):
                            # Use the absolute path as-is (already normalized)
                            result = os.path.normpath(file_abs)
                            # Cache with eviction if needed
                            self._cache_path_result(cache_key, result)
                            return result
                    except ValueError:
                        # Different drives on Windows, use absolute
                        result = os.path.normpath(file_abs)
                        self._cache_path_result(cache_key, result)
                        return result
                
                # Path is outside workspace, use absolute as-is
                result = os.path.normpath(file_abs)
                self._cache_path_result(cache_key, result)
                return result
            else:
                # No workspace, use absolute as-is
                result = os.path.normpath(file_abs)
                self._cache_path_result(cache_key, result)
                return result
        
        # If relative, join with workspace
        if workspace_path:
            workspace_abs = os.path.abspath(workspace_path)
            
            # Remove workspace prefix if already present (handle both absolute and relative)
            # First check if path already contains workspace (even if not absolute)
            if workspace_abs in file_path or workspace_path in file_path:
                # Path already contains workspace, extract relative part
                if file_path.startswith(workspace_abs):
                    file_path = os.path.relpath(file_path, workspace_abs)
                elif file_path.startswith(workspace_path):
                    file_path = file_path[len(workspace_path):].lstrip('/\\')
            
            # Remove leading ./ or .\
            if file_path.startswith('./') or file_path.startswith('.\\'):
                file_path = file_path[2:]
            
            # Join with workspace
            full_path = os.path.join(workspace_path, file_path)
            normalized = os.path.normpath(full_path)
            
            # Final safety check: ensure no duplication
            normalized_abs = os.path.abspath(normalized)
            workspace_abs_normalized = os.path.abspath(workspace_path)
            
            # Check if normalized path contains workspace twice
            if normalized_abs.startswith(workspace_abs_normalized):
                # Check for duplication pattern: workspace/workspace/...
                parts = normalized_abs.replace(workspace_abs_normalized, '').split(os.sep)
                if parts and parts[0] == '':
                    parts = parts[1:]
                
                # If first part matches workspace name, might be duplication
                workspace_name = os.path.basename(workspace_abs_normalized)
                if parts and parts[0] == workspace_name:
                    # Potential duplication, use relative path
                    try:
                        rel_path = os.path.relpath(normalized_abs, workspace_abs_normalized)
                        result = os.path.normpath(os.path.join(workspace_path, rel_path))
                        self._cache_path_result(cache_key, result)
                        return result
                    except ValueError:
                        pass
            
            # Cache and return normalized path
            self._cache_path_result(cache_key, normalized)
            return normalized
        
        # No workspace, use path as-is (assume absolute or relative to current dir)
        result = os.path.normpath(file_path)
        # Cache the result
        self._cache_path_result(cache_key, result)
        return result
    
    async def process_actions(
        self, 
        response_text: str, 
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """
        Process all actions in response text.
        
        Returns:
            Dictionary with:
            - processed_text: Response text with actions replaced by status messages
            - actions_executed: List of executed actions with status
            - success_count: Number of successful actions
            - error_count: Number of failed actions
        """
        actions = self.extract_actions(response_text)
        
        # Build dependency graph from create-file actions and order by dependencies
        create_file_actions = [a for a in actions if a['type'] == 'create-file' and not a.get('is_directory', False)]
        # Include both create-file with is_directory and explicit create-directory
        directory_actions = (
            [a for a in actions if a['type'] == 'create-file' and a.get('is_directory', False)] +
            [a for a in actions if a['type'] == 'create-directory']
        )
        other_actions = [a for a in actions if a['type'] not in ['create-file', 'create-directory']]
        
        # Check if only directory was created without files
        has_directory_only = (
            len(directory_actions) > 0 and 
            len(create_file_actions) == 0
        )
        
        # Log extracted actions for debugging
        if actions:
            action_types = [a.get('type') for a in actions]
            
            self.logger.info(
                f"Extracted {len(actions)} actions",
                workspace_path=workspace_path,
                context={
                    "action_types": action_types,
                    "action_count": len(actions),
                    "create_file_count": len(create_file_actions),
                    "directory_count": len(directory_actions),
                    "has_directory_only": has_directory_only,
                    "warning": "Only directory created, no files" if has_directory_only else None
                }
            )
            
            # Warn if only directory was created without files
            if has_directory_only:
                self.logger.warning(
                    "Only directory action detected, no file creation actions found",
                    workspace_path=workspace_path,
                    context={
                        "response_preview": response_text[:500],
                        "suggestion": "AI may need to be prompted again to create files",
                        "directory_actions": [a.get('path') for a in directory_actions]
                    }
                )
        else:
            self.logger.warning(
                "No actions extracted from response",
                workspace_path=workspace_path,
                context={"response_length": len(response_text), "response_preview": response_text[:200]}
            )
        
        processed_text = response_text
        actions_executed = []
        success_count = 0
        error_count = 0
        
        if not workspace_path:
            workspace_context = self.workspace_service.get_project_context()
            if workspace_context.get("has_workspace"):
                workspace_path = workspace_context.get("root_path")
        
        if len(create_file_actions) > 1:
            # Reset graph for this batch
            self.dependency_graph = FileDependencyGraph()
            
            # Build graph from file contents
            # Map original paths to normalized paths for matching
            path_mapping = {}  # normalized -> original_path
            for action in create_file_actions:
                path = action['path']
                content = action.get('content', '')
                dependencies = self._extract_dependencies_from_content(content)
                
                # Normalize path for graph
                normalized = self.normalize_path(path, workspace_path)
                path_mapping[normalized] = path
                
                # Add file to graph using normalized path
                # Map dependencies to other files in the batch
                mapped_dependencies = []
                for dep in dependencies:
                    # Try to find if this dependency matches any file in the batch
                    for other_action in create_file_actions:
                        other_path = other_action['path']
                        other_normalized = self.normalize_path(other_path, workspace_path)
                        # Check if dependency matches file name or path
                        if dep in other_path or dep in other_normalized:
                            mapped_dependencies.append(other_normalized)
                
                self.dependency_graph.add_file(
                    file_path=normalized,
                    imports=mapped_dependencies,  # Use mapped dependencies
                    metadata={'action': action}
                )
            
            # Order create-file actions by dependencies (topological sort)
            try:
                ordered_paths = self.dependency_graph.topological_sort()
                
                # Create mapping: normalized_path -> action
                path_to_action = {}
                for action in create_file_actions:
                    normalized = self.normalize_path(action['path'], workspace_path)
                    path_to_action[normalized] = action
                
                # Reorder create-file actions based on topological sort
                ordered_create_actions = []
                seen_actions = set()
                for normalized_path in ordered_paths:
                    if normalized_path in path_to_action:
                        action = path_to_action[normalized_path]
                        if id(action) not in seen_actions:
                            ordered_create_actions.append(action)
                            seen_actions.add(id(action))
                
                # Add any actions not in the graph (shouldn't happen, but safety)
                for action in create_file_actions:
                    if id(action) not in seen_actions:
                        ordered_create_actions.append(action)
                
                # Reorder: directories first, then ordered files, then other actions
                actions = directory_actions + ordered_create_actions + other_actions
            except Exception as e:
                # If ordering fails, use original order
                self.logger.warning(
                    f"Could not order files by dependencies: {e}",
                    context={"error": str(e)}
                )
                actions = directory_actions + create_file_actions + other_actions
        else:
            # Single file or no files, keep original order but directories first
            actions = directory_actions + create_file_actions + other_actions
        
        for action in actions:
            try:
                if action['type'] == 'create-directory':
                    # Explicit directory creation
                    result = await self._create_directory(
                        action['path'],
                        workspace_path
                    )
                    if result['success']:
                        success_count += 1
                        actions_executed.append(f"✅ Created directory: {action['path']}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"✅ **Directory created:** `{action['path']}`"
                        )
                    else:
                        error_count += 1
                        actions_executed.append(f"❌ Failed: {action['path']} - {result.get('error', 'Unknown error')}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"❌ **Failed to create directory:** `{action['path']}`\nError: {result.get('error', 'Unknown error')}"
                        )
                
                elif action['type'] == 'create-file':
                    # Check if this is a directory creation (by .gitkeep or empty content)
                    path = action['path']
                    content = action.get('content', '')
                    is_directory = (
                        action.get('is_directory', False) or
                        '.gitkeep' in path.lower() or
                        path.endswith('/') or
                        (not content.strip() and len(content.strip()) == 0)
                    )
                    
                    # If it's a .gitkeep file, treat as directory creation
                    if '.gitkeep' in path.lower():
                        # Create directory by creating .gitkeep file
                        result = await self._create_file(
                            path,
                            '',  # Empty content for .gitkeep
                            workspace_path
                        )
                    elif is_directory:
                        # Create directory directly
                        result = await self._create_directory(
                            path.rstrip('/'),
                            workspace_path
                        )
                    else:
                        # Validate before creating
                        validation_result = None
                        if self.validator:
                            try:
                                validation_result = self.validator.validate_file_creation(
                                    path=path,
                                    content=content,
                                    workspace_path=workspace_path
                                )
                                if not validation_result.valid:
                                    # Log validation errors but still try to create
                                    self.logger.warning(
                                        f"Validation warnings for {path}",
                                        file_path=path,
                                        workspace_path=workspace_path,
                                        context={"validation_errors": validation_result.errors}
                                    )
                            except Exception as e:
                                self.logger.error(
                                    f"Validation error: {e}",
                                    file_path=path,
                                    workspace_path=workspace_path,
                                    context={"error": str(e)}
                                )
                        
                        # Create file
                        result = await self._create_file(
                            path,
                            content,
                            workspace_path
                        )
                    
                    if result['success']:
                        success_count += 1
                        if is_directory or '.gitkeep' in path.lower():
                            actions_executed.append(f"✅ Created directory: {path}")
                            processed_text = processed_text.replace(
                                action['raw_match'],
                                f"✅ **Directory created:** `{path}`"
                            )
                        else:
                            # Record in conversation memory if available
                            if self.conversation_memory:
                                try:
                                    self.conversation_memory.record_file_creation(
                                        path=path,
                                        content=content,
                                        dependencies=self._extract_dependencies_from_content(content)
                                    )
                                except Exception as e:
                                    self.logger.error(
                                        f"Error recording file creation in memory: {e}",
                                        context={"path": path, "error": str(e)}
                                    )
                            
                            # Add validation feedback if available
                            feedback = ""
                            if validation_result:
                                if validation_result.warnings:
                                    feedback += f"\n⚠️ Warnings: {', '.join(validation_result.warnings[:2])}"
                                if validation_result.suggestions:
                                    feedback += f"\n💡 Suggestions: {', '.join(validation_result.suggestions[:2])}"
                            
                            actions_executed.append(f"✅ Created: {path}{feedback}")
                            processed_text = processed_text.replace(
                                action['raw_match'],
                                f"✅ **File created:** `{path}`{feedback}\n```\n{content[:500]}{'...(truncated)' if len(content) > 500 else ''}\n```"
                            )
                    else:
                        error_count += 1
                        error_msg = result.get('error', 'Unknown error')
                        actions_executed.append(f"❌ Failed: {path} - {error_msg}")
                        self.logger.error(
                            f"Error creating file: {path}",
                            context={"path": path, "error": error_msg}
                        )
                        
                        # Try to provide helpful error message
                        if "Permission denied" in error_msg:
                            error_msg += " - Check file/directory permissions"
                        elif "not a directory" in error_msg.lower():
                            error_msg += " - A file with this name already exists"
                        
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"❌ **Failed to create:** `{path}`\nError: {error_msg}"
                        )
                
                elif action['type'] == 'modify-file':
                    result = await self._modify_file(
                        action['path'],
                        action['content'],
                        workspace_path
                    )
                    if result['success']:
                        success_count += 1
                        
                        # Record in conversation memory if available
                        if self.conversation_memory:
                            try:
                                self.conversation_memory.record_file_modification(
                                    path=action['path'],
                                    modification_type='modified',
                                    preview=action['content'][:200]
                                )
                            except Exception as e:
                                self.logger.error(
                                    f"Error recording file modification in memory: {e}",
                                    file_path=action['path'],
                                    workspace_path=workspace_path,
                                    context={"error": str(e)}
                                )
                        
                        actions_executed.append(f"✅ Modified: {action['path']}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"✅ **File modified:** `{action['path']}`"
                        )
                    else:
                        error_count += 1
                        actions_executed.append(f"❌ Failed: {action['path']} - {result['error']}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"❌ **Failed to modify:** `{action['path']}`\nError: {result['error']}"
                        )
                
                elif action['type'] in ['delete-file', 'delete-directory']:
                    result = await self._delete_path(
                        action['path'],
                        is_directory=(action['type'] == 'delete-directory'),
                        workspace_path=workspace_path
                    )
                    if result['success']:
                        success_count += 1
                        actions_executed.append(f"✅ Deleted: {action['path']}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"✅ **Deleted:** `{action['path']}`"
                        )
                    else:
                        error_count += 1
                        actions_executed.append(f"❌ Failed: {action['path']} - {result['error']}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"❌ **Failed to delete:** `{action['path']}`\nError: {result['error']}"
                        )
                
                elif action['type'] == 'run-command':
                    result = await self._run_command(
                        action['command'],
                        workspace_path
                    )
                    if result['success']:
                        success_count += 1
                        output = result.get('output', '')
                        error = result.get('error', '')
                        if output:
                            actions_executed.append(f"✅ Executed: {action['command']}")
                            processed_text = processed_text.replace(
                                action['raw_match'],
                                f"✅ **Command executed:** `{action['command']}`\n```\n{output}\n```"
                            )
                        elif error:
                            actions_executed.append(f"⚠️ Command executed with errors: {action['command']}")
                            processed_text = processed_text.replace(
                                action['raw_match'],
                                f"⚠️ **Command executed:** `{action['command']}`\n```\n{error}\n```"
                            )
                        else:
                            actions_executed.append(f"✅ Executed: {action['command']}")
                            processed_text = processed_text.replace(
                                action['raw_match'],
                                f"✅ **Command executed:** `{action['command']}`"
                            )
                    else:
                        error_count += 1
                        actions_executed.append(f"❌ Failed: {action['command']} - {result.get('error', 'Unknown error')}")
                        processed_text = processed_text.replace(
                            action['raw_match'],
                            f"❌ **Failed to execute:** `{action['command']}`\nError: {result.get('error', 'Unknown error')}"
                        )
            
            except Exception as e:
                error_count += 1
                actions_executed.append(f"❌ Error processing {action['type']}: {str(e)}")
                processed_text = processed_text.replace(
                    action['raw_match'],
                    f"❌ **Error:** {str(e)}"
                )
        
        result = {
            'processed_text': processed_text,
            'actions_executed': actions_executed,
            'success_count': success_count,
            'error_count': error_count,
            'total_actions': len(actions),
            'has_directory_only': has_directory_only if actions else False,
            'create_file_count': len(create_file_actions),
            'directory_count': len(directory_actions)
        }
        
        # Add conversation memory summary if available
        if self.conversation_memory:
            try:
                result['conversation_memory'] = self.conversation_memory.get_context_summary()
            except Exception as e:
                # If there's an error, don't break processing
                result['conversation_memory'] = f"[Error getting conversation memory: {str(e)}]"
        
        return result
    
    async def _check_command_safety(self, command: str) -> Tuple[bool, str]:
        """
        Check if command is safe to execute using AI-powered detection.
        
        Returns:
            Tuple of (is_dangerous, reason)
        """
        if not self.ollama_service:
            # Fallback: basic pattern check for critical cases
            critical_patterns = ['rm -rf /', 'dd if=', 'mkfs', 'fdisk', ':(){']
            command_lower = command.lower()
            for pattern in critical_patterns:
                if pattern in command_lower:
                    return (True, f"Contains critical dangerous pattern: {pattern}")
            return (False, "Command appears safe")
        
        # Use AI to analyze command safety
        prompt = f"""Analyze if this shell command is safe to execute in a development environment:

Command: {command}

Consider:
- File deletion commands (rm, del)
- System modification (chmod, sudo, su)
- Network operations (wget, curl to external URLs)
- Disk operations (dd, mkfs, fdisk)
- Fork bombs or resource exhaustion
- Commands that could damage the system

Respond with JSON:
{{
    "is_dangerous": true/false,
    "reason": "brief explanation",
    "confidence": 0.0-1.0
}}

Safe commands include: npm start, python -m http.server, npm install, git commands, etc."""
        
        try:
            result = await self.ollama_service.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=150
            )
            
            import json
            response_text = result.response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                is_dangerous = data.get('is_dangerous', False)
                reason = data.get('reason', 'AI detected potential danger')
                confidence = data.get('confidence', 0.5)
                
                # Only block if confidence is high
                if is_dangerous and confidence > 0.7:
                    return (True, reason)
        except Exception as e:
            # If AI check fails, use conservative fallback
            critical_patterns = ['rm -rf /', 'dd if=', 'mkfs', 'fdisk', ':(){']
            command_lower = command.lower()
            for pattern in critical_patterns:
                if pattern in command_lower:
                    return (True, f"Contains critical dangerous pattern: {pattern}")
        
        return (False, "Command appears safe")
    
    def _is_just_extension(self, extension: str) -> bool:
        """
        Check if a string is just a file extension (not a filename).
        
        Uses AI-powered language detector to determine if extension is valid.
        """
        if not extension or len(extension) < 2:
            return False
        
        # Use language detector to check if this is a valid extension
        if self.language_detector:
            lang_info = self.language_detector.detect_from_extension(f".{extension}")
            # If detector recognizes it as a language extension, it's likely just an extension
            if lang_info and lang_info.confidence > 0.5:
                return True
        
        # Fallback: check if it's a very short extension (likely just extension)
        # Common extensions are 2-5 characters
        if len(extension) <= 5 and extension.isalnum():
            # Could be extension, but use AI if available
            return True
        
        return False
    
    def _extract_dependencies_from_content(self, content: str) -> List[str]:
        """
        Extract dependencies from file content generically.
        
        Uses language detector instead of hardcoded patterns.
        """
        if self.language_detector:
            # Use generic language detector
            return self.language_detector.extract_imports(content)
        
        dependencies = []
        
        patterns = [
            r'^(?:from|import)\s+([\w\.]+)',  # Python/Java style
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',  # ES6
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]',  # CommonJS
            r'#include\s*[<"]([^>"]+)[>"]',  # C/C++
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates
    
    async def _create_file(
        self, 
        file_path: str, 
        content: str, 
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """Create a file."""
        try:
            from pathlib import Path
            
            # Security validation before processing
            is_valid, error = PathSecurity.validate_path(
                file_path,
                workspace_path,
                allow_absolute=True
            )
            if not is_valid:
                self.logger.log_security_event(
                    "path_validation_failed",
                    f"Path validation failed: {error}",
                    file_path=file_path,
                    workspace_path=workspace_path,
                    blocked=True
                )
                return {
                    'success': False,
                    'error': f"Security validation failed: {error}",
                    'path': file_path
                }
            
            # Normalize path
            original_path = file_path
            full_path = self.normalize_path(file_path, workspace_path)
            
            # Log action with structured logger
            self.logger.log_action(
                action="create_file",
                action_type="file_creation",
                workspace_path=workspace_path,
                success=True,
                file_path=file_path,
                normalized_path=full_path
            )
            
            path_obj = Path(full_path)
            
            # Ensure we have a valid file path (not a directory)
            if path_obj.exists() and path_obj.is_dir():
                return {
                    'success': False,
                    'error': f"Path exists but is a directory, not a file: {full_path}",
                    'path': file_path
                }
            
            # Create parent directories if needed
            parent_dir = path_obj.parent
            if parent_dir:
                # CRITICAL: Never delete user files without explicit permission
                # If parent exists as a FILE (not directory), return error instead of deleting
                if parent_dir.exists() and parent_dir.is_file():
                    return {
                        'success': False,
                        'error': f"Cannot create file: parent path exists as a file (not directory): {parent_dir}. Please remove or rename the existing file first, or choose a different path.",
                        'path': file_path
                    }
                
                # Create parent directory if it doesn't exist
                if not parent_dir.exists():
                    try:
                        parent_dir.mkdir(parents=True, exist_ok=True)
                    except FileExistsError:
                        # Directory was created by another process, continue
                        pass
                    except Exception as e:
                        return {
                            'success': False,
                            'error': f"Failed to create parent directory {parent_dir}: {str(e)}",
                            'path': file_path
                        }
                
                # Ensure parent is a directory, not a file
                if parent_dir.exists() and not parent_dir.is_dir():
                    return {
                        'success': False,
                        'error': f"Cannot create file: parent path exists but is not a directory: {parent_dir}. Please remove or rename the existing file first.",
                        'path': file_path
                    }
            
            # Create file using FileService
            result = self.file_service.write_file(
                path=str(path_obj),
                content=content or '',  # Allow empty content for .gitkeep files
                create_backup=False
            )
            
            # Verify file was actually created
            if not path_obj.exists():
                return {
                    'success': False,
                    'error': f"File was not created: {full_path}",
                    'path': file_path
                }
            
            self.logger.info(
                f"File created successfully: {full_path}",
                workspace_path=workspace_path,
                file_path=str(path_obj)
            )
            
            return {
                'success': True,
                'path': str(path_obj),
                'result': result
            }
        except Exception as e:
            error_detail = f"{str(e)}"
            return {
                'success': False,
                'error': error_detail,
                'path': file_path
            }
    
    async def _create_directory(
        self,
        dir_path: str,
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """Create a directory."""
        try:
            original_path = dir_path
            full_path = self.normalize_path(dir_path, workspace_path)
            
            # Debug logging
            # Security validation
            is_valid, error = PathSecurity.validate_path(
                dir_path,
                workspace_path,
                allow_absolute=True
            )
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Security validation failed: {error}",
                    'path': dir_path
                }
            
            # Log action
            self.logger.log_action(
                action="create_directory",
                action_type="directory_creation",
                workspace_path=workspace_path,
                success=True,
                directory_path=dir_path,
                normalized_path=full_path
            )
            
            # Remove trailing slash if present
            if full_path.endswith('/'):
                full_path = full_path.rstrip('/')
            
            # Create directory
            result = self.file_service.create_directory(full_path)
            
            # Verify directory was actually created
            from pathlib import Path
            path_obj = Path(full_path)
            if not path_obj.exists() or not path_obj.is_dir():
                return {
                    'success': False,
                    'error': f"Directory was not created: {full_path}",
                    'path': dir_path
                }
            
            self.logger.info(
                f"Directory created successfully: {full_path}",
                workspace_path=workspace_path,
                directory_path=full_path
            )
            
            return {
                'success': True,
                'path': full_path,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'path': dir_path
            }
    
    async def _modify_file(
        self, 
        file_path: str, 
        content: str, 
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """Modify a file."""
        try:
            full_path = self.normalize_path(file_path, workspace_path)
            
            # Write file (will overwrite existing)
            result = self.file_service.write_file(
                path=full_path,
                content=content,
                create_backup=True
            )
            
            return {
                'success': True,
                'path': full_path,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'path': file_path
            }
    
    async def _delete_path(
        self,
        path: str,
        is_directory: bool = False,
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """Delete a file or directory."""
        try:
            full_path = self.normalize_path(path, workspace_path)
            
            # Safety check: don't delete outside workspace unless explicitly absolute
            if workspace_path and not os.path.isabs(path):
                workspace_abs = os.path.abspath(workspace_path)
                file_abs = os.path.abspath(full_path)
                try:
                    rel_path = os.path.relpath(file_abs, workspace_abs)
                    if rel_path.startswith('..'):
                        return {
                            'success': False,
                            'error': f"Safety: Cannot delete path outside workspace. Use absolute path if intentional.",
                            'path': path
                        }
                except ValueError:
                    pass
            
            # Delete using FileService
            result = self.file_service.delete(
                path=full_path,
                recursive=is_directory
            )
            
            return {
                'success': True,
                'path': full_path,
                'result': result
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Path not found: {path}",
                'path': path
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'path': path
            }
    
    async def _run_command(
        self,
        command: str,
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """
        Execute a shell command safely.
        
        Supports:
        - npm start, npm run dev, etc.
        - python -m http.server
        - Other safe development commands
        """
        import subprocess
        import shlex
        
        try:
            # Security: Use AI to detect dangerous commands
            is_dangerous, reason = await self._check_command_safety(command)
            if is_dangerous:
                return {
                    'success': False,
                    'error': f"Command blocked for security: {reason}",
                    'output': '',
                    'command': command
                }
            
            # Determine working directory
            cwd = workspace_path if workspace_path else os.getcwd()
            
            # Expand ~ in path
            if cwd and cwd.startswith('~'):
                cwd = os.path.expanduser(cwd)
            
            # Ensure cwd exists
            if cwd and not os.path.exists(cwd):
                return {
                    'success': False,
                    'error': f"Working directory does not exist: {cwd}",
                    'output': '',
                    'command': command
                }
            
            # Parse command (handle shell operators like &&, |, etc.)
            # For complex commands, use shell=True but be careful
            use_shell = any(op in command for op in ['&&', '||', '|', '>', '<', ';'])
            
            # Log command execution
            self.logger.log_action(
                action="run_command",
                action_type="command_execution",
                workspace_path=workspace_path,
                success=True,
                command=command,
                working_directory=cwd,
                uses_shell=use_shell
            )
            
            # Execute command
            if use_shell:
                # Use shell for complex commands
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=os.environ.copy()
                )
            else:
                # Parse command into list for safer execution
                try:
                    parts = shlex.split(command)
                    process = subprocess.Popen(
                        parts,
                        cwd=cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=os.environ.copy()
                    )
                except ValueError:
                    # If parsing fails, fall back to shell
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        cwd=cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=os.environ.copy()
                    )
            
            # Wait for completion with timeout (30 seconds for dev servers)
            timeout = 30
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                # For long-running commands (like npm start), return immediately
                # User can check status separately
                process.kill()
                return {
                    'success': True,
                    'output': f"Command started in background (timeout after {timeout}s). For long-running servers, check process status separately.",
                    'error': '',
                    'command': command,
                    'pid': process.pid
                }
            
            # Combine stdout and stderr
            output = stdout if stdout else ''
            error = stderr if stderr else ''
            
            # If there's output in stderr but return code is 0, it's usually a warning
            if return_code == 0:
                if error:
                    output = f"{output}\n{error}" if output else error
                return {
                    'success': True,
                    'output': output,
                    'error': '',
                    'command': command,
                    'return_code': return_code
                }
            else:
                return {
                    'success': False,
                    'output': output,
                    'error': error or f"Command failed with return code {return_code}",
                    'command': command,
                    'return_code': return_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'command': command
            }
    
    def clear_caches(self) -> None:
        """
        Clear all caches to free memory.
        
        Useful for:
        - Long-running processes
        - Memory management
        - Testing cleanup
        """
        self._path_cache.clear()
        self._action_cache.clear()
        self.logger.info(
            "Caches cleared",
            context={
                "path_cache_size": len(self._path_cache),
                "action_cache_size": len(self._action_cache)
            }
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dict with cache statistics
        """
        return {
            "path_cache_size": len(self._path_cache),
            "action_cache_size": len(self._action_cache),
            "max_action_cache_size": self._max_cache_size,
            "max_path_cache_size": self._max_path_cache_size,
            "path_cache_usage_percent": (len(self._path_cache) / self._max_path_cache_size * 100) if self._max_path_cache_size > 0 else 0,
            "action_cache_usage_percent": (len(self._action_cache) / self._max_cache_size * 100) if self._max_cache_size > 0 else 0
        }


# Singleton instance
_action_processor: ActionProcessor = None


def get_action_processor(ollama_service: Optional[Any] = None) -> ActionProcessor:
    """
    Get or create ActionProcessor instance.
    
    Args:
        ollama_service: Optional Ollama service for AI-powered features
    
    Returns:
        ActionProcessor instance (singleton)
    """
    global _action_processor
    if _action_processor is None:
        _action_processor = ActionProcessor(ollama_service=ollama_service)
    return _action_processor

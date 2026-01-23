"""
Action Processor Service
========================
Processes agent actions (create-file, modify-file, run-command) from AI responses.
This allows backend to process actions directly, not just frontend.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from services.file_service import FileService, get_file_service
from services.workspace_service import WorkspaceService, get_workspace_service


class ActionProcessor:
    """
    Processes agent actions from AI responses.
    
    Actions supported:
    - create-file:path\ncontent
    - modify-file:path\ncontent
    - run-command\ncommand
    """
    
    def __init__(
        self, 
        file_service: FileService = None, 
        workspace_service: WorkspaceService = None,
        conversation_memory = None
    ):
        self.file_service = file_service or get_file_service()
        self.workspace_service = workspace_service or get_workspace_service()
        
        # Import ConversationMemory if not provided
        if conversation_memory is None:
            try:
                from services.conversation_memory import ConversationMemory
                self.conversation_memory = ConversationMemory()
            except ImportError:
                # Fallback if not available
                self.conversation_memory = None
        else:
            self.conversation_memory = conversation_memory
    
    def extract_actions(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract all actions from AI response.
        
        Returns:
            List of action dictionaries with type, path/content, and metadata
        """
        actions = []
        
        # Extract create-file actions
        create_pattern = r'```create-file:([^\n]+)\n([\s\S]*?)```'
        for match in re.finditer(create_pattern, response_text):
            path = match.group(1).strip()
            content = match.group(2)
            
            # Detect if this is a directory creation (empty content or .gitkeep)
            is_directory = (
                not content.strip() or 
                content.strip() == '' or
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
        
        # Extract modify-file actions
        modify_pattern = r'```modify-file:([^\n]+)\n([\s\S]*?)```'
        for match in re.finditer(modify_pattern, response_text):
            actions.append({
                'type': 'modify-file',
                'path': match.group(1).strip(),
                'content': match.group(2),
                'raw_match': match.group(0)
            })
        
        # Extract run-command actions
        command_pattern = r'```run-command\n([\s\S]*?)```'
        for match in re.finditer(command_pattern, response_text):
            actions.append({
                'type': 'run-command',
                'command': match.group(1).strip(),
                'raw_match': match.group(0)
            })
        
        return actions
    
    def normalize_path(self, file_path: str, workspace_path: str = None) -> str:
        """
        Normalize file path.
        
        Rules:
        - If absolute and outside workspace: use as-is
        - If relative: join with workspace
        - Handle ~ expansion
        """
        if not file_path:
            return file_path
        
        # Expand ~
        if file_path.startswith('~'):
            file_path = os.path.expanduser(file_path)
        
        # If already absolute and outside workspace, use as-is
        if os.path.isabs(file_path):
            if workspace_path and not file_path.startswith(workspace_path):
                return file_path
        
        # If relative or within workspace, join with workspace
        if workspace_path:
            # Remove workspace prefix if already present
            if file_path.startswith(workspace_path):
                file_path = file_path[len(workspace_path):].lstrip('/')
            
            # Join with workspace
            full_path = os.path.join(workspace_path, file_path)
            return os.path.normpath(full_path)
        
        # No workspace, use path as-is (assume absolute or relative to current dir)
        return os.path.normpath(file_path)
    
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
        processed_text = response_text
        actions_executed = []
        success_count = 0
        error_count = 0
        
        if not workspace_path:
            workspace_context = self.workspace_service.get_project_context()
            if workspace_context.get("has_workspace"):
                workspace_path = workspace_context.get("root_path")
        
        for action in actions:
            try:
                if action['type'] == 'create-file':
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
                                    print(f"[ActionProcessor] Error recording file creation in memory: {e}")
                            
                            actions_executed.append(f"✅ Created: {path}")
                            processed_text = processed_text.replace(
                                action['raw_match'],
                                f"✅ **File created:** `{path}`\n```\n{content[:500]}{'...(truncated)' if len(content) > 500 else ''}\n```"
                            )
                    else:
                        error_count += 1
                        error_msg = result.get('error', 'Unknown error')
                        actions_executed.append(f"❌ Failed: {path} - {error_msg}")
                        print(f"[ActionProcessor] Error creating {path}: {error_msg}")  # Debug
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
                                print(f"[ActionProcessor] Error recording file modification in memory: {e}")
                        
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
                
                elif action['type'] == 'run-command':
                    # Command execution would go here
                    # For now, just mark as executed
                    actions_executed.append(f"⚠️ Command execution not yet implemented: {action['command']}")
                    processed_text = processed_text.replace(
                        action['raw_match'],
                        f"⚠️ **Command:** `{action['command']}` (execution not yet implemented)"
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
            'total_actions': len(actions)
        }
        
        # Add conversation memory summary if available
        if self.conversation_memory:
            try:
                result['conversation_memory'] = self.conversation_memory.get_context_summary()
            except Exception as e:
                # If there's an error, don't break processing
                result['conversation_memory'] = f"[Error getting conversation memory: {str(e)}]"
        
        return result
    
    def _extract_dependencies_from_content(self, content: str) -> List[str]:
        """Extract dependencies from file content."""
        dependencies = []
        
        # Python imports
        python_imports = re.findall(r'^(?:from|import)\s+([\w\.]+)', content, re.MULTILINE)
        dependencies.extend(python_imports)
        
        # JavaScript/TypeScript imports
        js_imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        dependencies.extend(js_imports)
        
        # Require statements
        require_imports = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
        dependencies.extend(require_imports)
        
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
            
            full_path = self.normalize_path(file_path, workspace_path)
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
            full_path = self.normalize_path(dir_path, workspace_path)
            
            # Remove trailing slash if present
            if full_path.endswith('/'):
                full_path = full_path.rstrip('/')
            
            # Create directory
            result = self.file_service.create_directory(full_path)
            
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


# Singleton instance
_action_processor: ActionProcessor = None


def get_action_processor() -> ActionProcessor:
    """Get or create ActionProcessor instance."""
    global _action_processor
    if _action_processor is None:
        _action_processor = ActionProcessor()
    return _action_processor

"""
Refactoring Service
===================
Multi-file code refactoring operations.
Rename, move, and transform code across the codebase.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class RefactorChange:
    """A single refactoring change."""
    file_path: str
    line_number: int
    old_text: str
    new_text: str
    context: str = ""  # Surrounding lines for preview


@dataclass
class RefactorResult:
    """Result of a refactoring operation."""
    success: bool
    operation: str
    changes: List[RefactorChange]
    files_modified: int
    total_changes: int
    errors: List[str] = field(default_factory=list)
    preview_only: bool = True


class RefactoringService:
    """
    Service for multi-file refactoring.
    
    Operations:
    - Rename symbol (variable, function, class)
    - Move file/module
    - Extract function
    - Inline variable
    - Change function signature
    """
    
    # File extensions to include in refactoring
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.kt', '.go', '.rs', '.rb',
        '.c', '.cpp', '.h', '.hpp', '.cs',
        '.vue', '.svelte', '.php', '.swift'
    }
    
    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '__pycache__', '.git', '.svn',
        'venv', '.venv', 'build', 'dist', 'target',
        '.idea', '.vscode', 'coverage'
    }
    
    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize refactoring service."""
        self.workspace_path = workspace_path
    
    def _get_files(self, path: str, extensions: Set[str] = None) -> List[Path]:
        """Get all code files in path."""
        extensions = extensions or self.CODE_EXTENSIONS
        root = Path(path)
        files = []
        
        def scan(dir_path: Path):
            try:
                for item in dir_path.iterdir():
                    if item.name in self.SKIP_DIRS or item.name.startswith('.'):
                        continue
                    if item.is_dir():
                        scan(item)
                    elif item.is_file() and item.suffix in extensions:
                        files.append(item)
            except PermissionError:
                pass
        
        scan(root)
        return files
    
    def _find_symbol_references(
        self,
        symbol: str,
        path: str,
        whole_word: bool = True
    ) -> List[RefactorChange]:
        """Find all references to a symbol."""
        changes = []
        files = self._get_files(path)
        
        # Build regex pattern
        if whole_word:
            pattern = rf'\b{re.escape(symbol)}\b'
        else:
            pattern = re.escape(symbol)
        
        regex = re.compile(pattern)
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for match in regex.finditer(line):
                        # Get context (2 lines before and after)
                        start = max(0, i - 3)
                        end = min(len(lines), i + 2)
                        context_lines = lines[start:end]
                        context = '\n'.join(context_lines)
                        
                        changes.append(RefactorChange(
                            file_path=str(file_path),
                            line_number=i,
                            old_text=line,
                            new_text=line,  # Will be updated by rename
                            context=context
                        ))
            except Exception:
                continue
        
        return changes
    
    def rename_symbol(
        self,
        old_name: str,
        new_name: str,
        path: Optional[str] = None,
        preview: bool = True,
        whole_word: bool = True
    ) -> RefactorResult:
        """
        Rename a symbol across the codebase.
        
        Args:
            old_name: Current name of the symbol
            new_name: New name for the symbol
            path: Root path to search (uses workspace if not provided)
            preview: If True, only preview changes without applying
            whole_word: If True, match whole words only
            
        Returns:
            RefactorResult with all changes
        """
        search_path = path or self.workspace_path
        if not search_path:
            return RefactorResult(
                success=False,
                operation="rename",
                changes=[],
                files_modified=0,
                total_changes=0,
                errors=["No workspace path specified"]
            )
        
        # Find all references
        changes = self._find_symbol_references(old_name, search_path, whole_word)
        
        # Update changes with new text
        if whole_word:
            pattern = rf'\b{re.escape(old_name)}\b'
        else:
            pattern = re.escape(old_name)
        
        for change in changes:
            change.new_text = re.sub(pattern, new_name, change.old_text)
        
        # Apply changes if not preview
        if not preview:
            errors = []
            modified_files = set()
            
            # Group changes by file
            changes_by_file: Dict[str, List[RefactorChange]] = {}
            for change in changes:
                if change.file_path not in changes_by_file:
                    changes_by_file[change.file_path] = []
                changes_by_file[change.file_path].append(change)
            
            for file_path, file_changes in changes_by_file.items():
                try:
                    content = Path(file_path).read_text(encoding='utf-8')
                    new_content = re.sub(pattern, new_name, content)
                    Path(file_path).write_text(new_content, encoding='utf-8')
                    modified_files.add(file_path)
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
            
            return RefactorResult(
                success=len(errors) == 0,
                operation="rename",
                changes=changes,
                files_modified=len(modified_files),
                total_changes=len(changes),
                errors=errors,
                preview_only=False
            )
        
        # Count unique files
        unique_files = set(c.file_path for c in changes)
        
        return RefactorResult(
            success=True,
            operation="rename",
            changes=changes,
            files_modified=len(unique_files),
            total_changes=len(changes),
            preview_only=True
        )
    
    def find_and_replace(
        self,
        find_pattern: str,
        replace_pattern: str,
        path: Optional[str] = None,
        is_regex: bool = False,
        file_pattern: Optional[str] = None,
        preview: bool = True
    ) -> RefactorResult:
        """
        Find and replace across files.
        
        Args:
            find_pattern: Pattern to find
            replace_pattern: Replacement text
            path: Root path to search
            is_regex: If True, treat pattern as regex
            file_pattern: Glob pattern for files (e.g., "*.py")
            preview: If True, only preview changes
            
        Returns:
            RefactorResult with all changes
        """
        search_path = path or self.workspace_path
        if not search_path:
            return RefactorResult(
                success=False,
                operation="find_replace",
                changes=[],
                files_modified=0,
                total_changes=0,
                errors=["No workspace path specified"]
            )
        
        # Get files
        if file_pattern:
            extensions = {file_pattern.replace('*', '')} if '.' in file_pattern else None
        else:
            extensions = None
        
        files = self._get_files(search_path, extensions)
        changes = []
        
        # Compile pattern
        if is_regex:
            try:
                regex = re.compile(find_pattern)
            except re.error as e:
                return RefactorResult(
                    success=False,
                    operation="find_replace",
                    changes=[],
                    files_modified=0,
                    total_changes=0,
                    errors=[f"Invalid regex: {str(e)}"]
                )
        else:
            regex = re.compile(re.escape(find_pattern))
        
        # Find matches
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if regex.search(line):
                        new_line = regex.sub(replace_pattern, line)
                        
                        # Get context
                        start = max(0, i - 3)
                        end = min(len(lines), i + 2)
                        context = '\n'.join(lines[start:end])
                        
                        changes.append(RefactorChange(
                            file_path=str(file_path),
                            line_number=i,
                            old_text=line,
                            new_text=new_line,
                            context=context
                        ))
            except Exception:
                continue
        
        # Apply if not preview
        if not preview:
            errors = []
            modified_files = set()
            
            changes_by_file: Dict[str, List[RefactorChange]] = {}
            for change in changes:
                if change.file_path not in changes_by_file:
                    changes_by_file[change.file_path] = []
                changes_by_file[change.file_path].append(change)
            
            for file_path, _ in changes_by_file.items():
                try:
                    content = Path(file_path).read_text(encoding='utf-8')
                    new_content = regex.sub(replace_pattern, content)
                    Path(file_path).write_text(new_content, encoding='utf-8')
                    modified_files.add(file_path)
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
            
            return RefactorResult(
                success=len(errors) == 0,
                operation="find_replace",
                changes=changes,
                files_modified=len(modified_files),
                total_changes=len(changes),
                errors=errors,
                preview_only=False
            )
        
        unique_files = set(c.file_path for c in changes)
        
        return RefactorResult(
            success=True,
            operation="find_replace",
            changes=changes,
            files_modified=len(unique_files),
            total_changes=len(changes),
            preview_only=True
        )
    
    def extract_function(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        function_name: str,
        language: str = "python"
    ) -> RefactorResult:
        """
        Extract selected code into a new function.
        
        Args:
            file_path: Path to the file
            start_line: Start line of code to extract
            end_line: End line of code to extract
            function_name: Name for the new function
            language: Programming language
            
        Returns:
            RefactorResult with the change
        """
        try:
            content = Path(file_path).read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Extract the code
            extracted = '\n'.join(lines[start_line - 1:end_line])
            
            # Detect indentation
            first_line = lines[start_line - 1]
            indent = len(first_line) - len(first_line.lstrip())
            base_indent = ' ' * indent
            
            # Create new function based on language
            if language in ('python', 'py'):
                new_function = f"\n\ndef {function_name}():\n"
                new_function += '\n'.join('    ' + line for line in extracted.split('\n'))
                new_function += "\n"
                call = f"{base_indent}{function_name}()"
            elif language in ('javascript', 'js', 'typescript', 'ts'):
                new_function = f"\n\nfunction {function_name}() {{\n"
                new_function += '\n'.join('    ' + line for line in extracted.split('\n'))
                new_function += "\n}\n"
                call = f"{base_indent}{function_name}();"
            else:
                return RefactorResult(
                    success=False,
                    operation="extract_function",
                    changes=[],
                    files_modified=0,
                    total_changes=0,
                    errors=[f"Language not supported: {language}"]
                )
            
            # Build new content
            new_lines = lines[:start_line - 1] + [call] + lines[end_line:]
            new_content = '\n'.join(new_lines) + new_function
            
            change = RefactorChange(
                file_path=file_path,
                line_number=start_line,
                old_text=extracted,
                new_text=call + "\n\n" + new_function,
                context=extracted
            )
            
            return RefactorResult(
                success=True,
                operation="extract_function",
                changes=[change],
                files_modified=1,
                total_changes=1,
                preview_only=True
            )
            
        except Exception as e:
            return RefactorResult(
                success=False,
                operation="extract_function",
                changes=[],
                files_modified=0,
                total_changes=0,
                errors=[str(e)]
            )
    
    def move_file(
        self,
        source: str,
        destination: str,
        update_imports: bool = True,
        preview: bool = True
    ) -> RefactorResult:
        """
        Move a file and update all imports/references.
        
        Args:
            source: Current file path
            destination: New file path
            update_imports: If True, update imports in other files
            preview: If True, only preview changes
            
        Returns:
            RefactorResult with all changes
        """
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return RefactorResult(
                success=False,
                operation="move_file",
                changes=[],
                files_modified=0,
                total_changes=0,
                errors=[f"Source file not found: {source}"]
            )
        
        changes = []
        
        # Main file move
        changes.append(RefactorChange(
            file_path=source,
            line_number=0,
            old_text=f"Move from: {source}",
            new_text=f"Move to: {destination}",
            context="File move operation"
        ))
        
        # Find and update imports
        if update_imports and self.workspace_path:
            # Get module name from path
            source_module = source_path.stem
            dest_module = dest_path.stem
            
            if source_module != dest_module:
                # Find references to old module name
                import_changes = self._find_symbol_references(
                    source_module,
                    self.workspace_path
                )
                
                for change in import_changes:
                    if change.file_path != source:
                        change.new_text = change.old_text.replace(
                            source_module, dest_module
                        )
                        changes.append(change)
        
        if not preview:
            try:
                # Create destination directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                import shutil
                shutil.move(str(source_path), str(dest_path))
                
                # Apply import updates
                if update_imports:
                    for change in changes[1:]:  # Skip the move change
                        content = Path(change.file_path).read_text()
                        new_content = content.replace(
                            change.old_text,
                            change.new_text
                        )
                        Path(change.file_path).write_text(new_content)
                
                return RefactorResult(
                    success=True,
                    operation="move_file",
                    changes=changes,
                    files_modified=len(set(c.file_path for c in changes)),
                    total_changes=len(changes),
                    preview_only=False
                )
            except Exception as e:
                return RefactorResult(
                    success=False,
                    operation="move_file",
                    changes=changes,
                    files_modified=0,
                    total_changes=0,
                    errors=[str(e)],
                    preview_only=False
                )
        
        return RefactorResult(
            success=True,
            operation="move_file",
            changes=changes,
            files_modified=len(set(c.file_path for c in changes)),
            total_changes=len(changes),
            preview_only=True
        )


# Singleton instance
_refactoring_service: Optional[RefactoringService] = None


def get_refactoring_service(workspace_path: Optional[str] = None) -> RefactoringService:
    """Get refactoring service instance."""
    global _refactoring_service
    if _refactoring_service is None or workspace_path != _refactoring_service.workspace_path:
        _refactoring_service = RefactoringService(workspace_path)
    return _refactoring_service

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
    
    def __init__(self, workspace_path: Optional[str] = None, ollama_service=None):
        """
        Initialize refactoring service.
        
        Args:
            workspace_path: Workspace path
            ollama_service: Optional Ollama service for AI-powered features
        """
        self.workspace_path = workspace_path
        
        from services.file_intelligence import get_file_intelligence
        from services.language_detector import get_language_detector
        self.file_intelligence = get_file_intelligence(ollama_service)
        self.language_detector = get_language_detector(ollama_service)
    
    def _get_files(self, path: str, extensions: Set[str] = None) -> List[Path]:
        """
        Get all code files in path using intelligent detection.
        
        Args:
            path: Path to scan
            extensions: Optional set of extensions to filter (if None, uses LanguageDetector)
        """
        root = Path(path)
        files = []
        
        def scan(dir_path: Path):
            try:
                for item in dir_path.iterdir():
                    if self.file_intelligence.should_skip_directory(item.name):
                        continue
                    
                    if item.is_dir():
                        scan(item)
                    elif item.is_file():
                        if extensions:
                            if item.suffix in extensions:
                                files.append(item)
                        else:
                            lang_info = self.language_detector.detect_from_extension(item.suffix)
                            if lang_info and lang_info.name != 'Unknown':
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
                        start = max(0, i - 3)
                        end = min(len(lines), i + 2)
                        context_lines = lines[start:end]
                        context = '\n'.join(context_lines)
                        
                        changes.append(RefactorChange(
                            file_path=str(file_path),
                            line_number=i,
                            old_text=line,
                            new_text=line,
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
        
        changes = self._find_symbol_references(old_name, search_path, whole_word)
        
        if whole_word:
            pattern = rf'\b{re.escape(old_name)}\b'
        else:
            pattern = re.escape(old_name)
        
        for change in changes:
            change.new_text = re.sub(pattern, new_name, change.old_text)
        
        if not preview:
            errors = []
            modified_files = set()
            
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
        
        if file_pattern:
            extensions = {file_pattern.replace('*', '')} if '.' in file_pattern else None
        else:
            extensions = None
        
        files = self._get_files(search_path, extensions)
        changes = []
        
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
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if regex.search(line):
                        new_line = regex.sub(replace_pattern, line)
                        
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
            
            extracted = '\n'.join(lines[start_line - 1:end_line])
            
            first_line = lines[start_line - 1]
            indent = len(first_line) - len(first_line.lstrip())
            base_indent = ' ' * indent
            
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
        
        changes.append(RefactorChange(
            file_path=source,
            line_number=0,
            old_text=f"Move from: {source}",
            new_text=f"Move to: {destination}",
            context="File move operation"
        ))
        
        if update_imports and self.workspace_path:
            source_module = source_path.stem
            dest_module = dest_path.stem
            
            if source_module != dest_module:
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
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                import shutil
                shutil.move(str(source_path), str(dest_path))
                
                if update_imports:
                    for change in changes[1:]:
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

"""
Intelligent Validator Service
==============================
Validates file creation and modification actions intelligently.
Provides feedback and suggestions for improvements.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from services.language_detector import LanguageInfo


@dataclass
class ValidationResult:
    """Validation result for file operations."""
    valid: bool = True
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


class IntelligentValidator:
    """
    Intelligent validator for file creation and modification actions.
    
    Features:
    - Code syntax validation
    - Import/export verification
    - File structure validation
    - Common pattern detection
    - Improvement suggestions
    """
    
    def __init__(self, language_detector=None, ollama_service=None):
        """
        Initialize validator.
        
        Args:
            language_detector: Optional language detector service
            ollama_service: Optional Ollama service for AI-powered validation
        """
        from services.language_detector import get_language_detector
        self.language_detector = language_detector or get_language_detector(ollama_service)
        self.ollama = ollama_service
    
    def validate_file_creation(
        self,
        path: str,
        content: str,
        workspace_path: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate file creation.
        
        Args:
            path: File path
            content: File content
            workspace_path: Workspace path
            
        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult(valid=True)
        
        # Check if path is valid
        if not path or not path.strip():
            result.valid = False
            result.errors.append("File path cannot be empty")
            return result
        
        # Check file extension
        file_ext = Path(path).suffix.lower()
        if not file_ext:
            result.warnings.append("File has no extension - may cause issues")
        
        # Detect language dynamically
        lang_info = None
        if file_ext:
            lang_info = self.language_detector.detect_from_extension(file_ext)
        
        if not lang_info or lang_info.confidence < 0.5:
            # Try content-based detection
            lang_info = self.language_detector.detect_from_content(content, path)
        
        # Validate content based on detected language (generic approach)
        if lang_info:
            validation_result = self._validate_by_language(content, lang_info, file_ext)
            if not validation_result.valid:
                result.valid = False
                result.errors.extend(validation_result.errors)
            result.warnings.extend(validation_result.warnings)
            result.suggestions.extend(validation_result.suggestions)
        else:
            # Generic validation for unknown languages
            validation_result = self._validate_generic(content, file_ext)
            result.warnings.extend(validation_result.warnings)
            result.suggestions.extend(validation_result.suggestions)
        
        # Check for common issues
        if not content.strip():
            result.warnings.append("File is empty")
        
        # Check for encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            result.errors.append("Content contains invalid characters")
            result.valid = False
        
        return result
    
    def validate_file_modification(
        self,
        path: str,
        new_content: str,
        old_content: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate file modification.
        
        Args:
            path: File path
            new_content: New content
            old_content: Old content (optional)
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)
        
        creation_result = self.validate_file_creation(path, new_content)
        result.errors.extend(creation_result.errors)
        result.warnings.extend(creation_result.warnings)
        result.suggestions.extend(creation_result.suggestions)
        
        if not creation_result.valid:
            result.valid = False
        
        if old_content:
            old_lines = len(old_content.split('\n'))
            new_lines = len(new_content.split('\n'))
            
            if new_lines < old_lines * 0.5:
                result.warnings.append("Many lines were removed - verify if intentional")
            
            old_imports = self._extract_imports(old_content)
            new_imports = self._extract_imports(new_content)
            
            removed_imports = set(old_imports) - set(new_imports)
            if removed_imports:
                result.warnings.append(f"Removed imports: {', '.join(removed_imports)}")
        
        return result
    
    def _validate_by_language(self, content: str, lang_info: 'LanguageInfo', ext: str) -> ValidationResult:
        """
        Validate content based on detected language (generic approach).
        
        Uses AI if available, otherwise generic patterns.
        """
        result = ValidationResult(valid=True)
        
        # JSON validation (common format)
        if lang_info.name.lower() == 'json' or ext == '.json':
            return self._validate_json(content)
        
        # Use language detector's structure extraction
        structure = self.language_detector.extract_structure(content)
        
        # Generic validation checks
        imports = self.language_detector.extract_imports(content, lang_info.name)
        
        # Check for exports (generic pattern)
        if structure.get('exports') or structure.get('classes') or structure.get('functions'):
            # Has structure but no exports - might need export
            if not structure.get('exports') and (structure.get('classes') or structure.get('functions')):
                if lang_info.framework:
                    result.suggestions.append(f"{lang_info.framework} component may need export")
        
        # Framework-specific checks (detected dynamically)
        if lang_info.framework:
            framework_result = self._validate_framework(content, lang_info)
            result.warnings.extend(framework_result.warnings)
            result.suggestions.extend(framework_result.suggestions)
        
        # Syntax validation (try generic compilation if possible)
        syntax_result = self._validate_syntax_generic(content, lang_info)
        result.warnings.extend(syntax_result.warnings)
        
        return result
    
    def _validate_generic(self, content: str, ext: str) -> ValidationResult:
        """Generic validation for unknown languages."""
        result = ValidationResult(valid=True)
        
        # Basic checks that work for any language
        if not content.strip():
            result.warnings.append("File is empty")
        
        # Check encoding
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            result.errors.append("Content contains invalid characters")
            result.valid = False
        
        return result
    
    def _validate_json(self, content: str) -> ValidationResult:
        """Validate JSON."""
        result = ValidationResult(valid=True)
        
        try:
            import json
            json.loads(content)
        except json.JSONDecodeError as e:
            result.valid = False
            result.errors.append(f"Invalid JSON: {str(e)}")
        
        return result
    
    def _validate_framework(self, content: str, lang_info: 'LanguageInfo') -> ValidationResult:
        """
        Validate framework-specific patterns (detected dynamically).
        
        Uses AI if available to understand framework requirements.
        """
        result = ValidationResult(valid=True)
        
        # Generic framework validation
        # Could use AI here to understand framework-specific requirements
        if self.ollama and lang_info.framework:
            # Could ask AI: "What are common issues with {framework} code?"
            pass
        
        return result
    
    def _validate_syntax_generic(self, content: str, lang_info: 'LanguageInfo') -> ValidationResult:
        """
        Generic syntax validation.
        
        Tries language-appropriate compilation if possible.
        """
        result = ValidationResult(valid=True)
        
        # Try Python compilation if detected as Python
        if lang_info.name.lower() == 'python':
            try:
                compile(content, '<string>', 'exec')
            except SyntaxError as e:
                result.warnings.append(f"Possible syntax error: {str(e)}")
        
        # For other languages, could use language-specific tools
        # But we keep it generic - AI can catch syntax issues
        
        return result
    
    def _extract_imports(self, content: str, language: Optional[str] = None) -> List[str]:
        """
        Extract imports generically using language detector.
        
        No hardcoded language-specific patterns.
        """
        return self.language_detector.extract_imports(content, language)
    
    def suggest_improvements(
        self,
        path: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Suggest improvements for a file.
        
        Args:
            path: File path
            content: File content
            context: Additional context (e.g., similar files)
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Check for missing documentation
        if not any(line.strip().startswith('//') or line.strip().startswith('#') 
                   for line in content.split('\n')[:10]):
            suggestions.append("Consider adding comments/documentation")
        
        # Check for error handling
        if 'try' not in content and 'catch' not in content:
            if 'async' in content or 'await' in content:
                suggestions.append("Consider adding error handling for async operations")
        
        # Check for type hints (detected dynamically)
        lang_info = self.language_detector.detect_from_content(content, path)
        if lang_info and lang_info.name.lower() in ['typescript', 'ts']:
            if 'function' in content or 'const' in content:
                if ': ' not in content and 'interface' not in content:
                    suggestions.append("Consider adding TypeScript types")
        
        return suggestions


# Singleton instance
_validator: Optional[IntelligentValidator] = None


def get_intelligent_validator(ollama_service=None) -> IntelligentValidator:
    """
    Get or create validator instance.
    
    Args:
        ollama_service: Optional Ollama service for AI-powered validation
    """
    global _validator
    if _validator is None:
        _validator = IntelligentValidator(ollama_service=ollama_service)
    return _validator

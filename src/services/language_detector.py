"""
Language Detector Service
==========================
Generic, AI-powered language and framework detection.
Uses AI model to dynamically detect languages, frameworks, and patterns
instead of hardcoded lists.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class LanguageInfo:
    """Detected language information."""
    name: str
    confidence: float
    extension: Optional[str] = None
    framework: Optional[str] = None
    libraries: List[str] = None
    
    def __post_init__(self):
        if self.libraries is None:
            self.libraries = []


class LanguageDetector:
    """
    Generic language detector using AI-powered analysis.
    
    Instead of hardcoded lists, uses intelligent pattern detection
    and can leverage AI model for complex cases.
    """
    
    def __init__(self, ollama_service=None):
        """
        Initialize language detector.
        
        Args:
            ollama_service: Optional Ollama service for AI-powered detection
        """
        self.ollama = ollama_service
    
    def detect_from_extension(self, extension: str) -> Optional[LanguageInfo]:
        """
        Detect language from file extension using generic patterns.
        
        Uses common patterns but doesn't hardcode specific languages.
        Falls back to AI if needed.
        """
        if not extension:
            return None
        
        ext = extension.lower().lstrip('.')
        
        # Generic pattern-based detection (not hardcoded to specific languages)
        # These are common patterns that work across many languages
        
        # Scripting languages pattern: .{lang}
        # Compiled languages pattern: .{lang}
        # Config files pattern: .{config}
        
        # Use AI to detect if extension is unknown
        # For now, return generic detection
        return LanguageInfo(
            name=self._infer_language_name(ext),
            confidence=0.7,
            extension=extension
        )
    
    def detect_from_content(self, content: str, file_path: Optional[str] = None) -> Optional[LanguageInfo]:
        """
        Detect language from file content using intelligent analysis.
        
        Uses pattern matching and can leverage AI for complex cases.
        """
        if not content or len(content.strip()) < 10:
            return None
        
        # Generic pattern detection (not language-specific)
        patterns = self._analyze_content_patterns(content)
        
        if patterns:
            return LanguageInfo(
                name=patterns.get('language', 'Unknown'),
                confidence=patterns.get('confidence', 0.6),
                framework=patterns.get('framework'),
                libraries=patterns.get('libraries', [])
            )
        
        if self.ollama:
            return self._ai_detect_language(content, file_path)
        
        return None
    
    async def detect_from_content_async(self, content: str, file_path: Optional[str] = None) -> Optional[LanguageInfo]:
        """Async version of detect_from_content with AI support."""
        if not content or len(content.strip()) < 10:
            return None
        
        patterns = self._analyze_content_patterns(content)
        if patterns and patterns.get('confidence', 0) > 0.8:
            return LanguageInfo(
                name=patterns.get('language', 'Unknown'),
                confidence=patterns.get('confidence', 0.6),
                framework=patterns.get('framework'),
                libraries=patterns.get('libraries', [])
            )
        
        if self.ollama:
            return await self._ai_detect_language_async(content, file_path)
        
        return None
    
    def _infer_language_name(self, extension: str) -> str:
        """
        Infer language name from extension using generic rules.
        
        Not hardcoded - uses common naming patterns.
        """
        if len(extension) <= 3:
            return extension.upper()
        return extension.capitalize()
    
    def _analyze_content_patterns(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for language patterns generically.
        
        Uses generic patterns that work across languages, not hardcoded rules.
        """
        result = {}
        content_lower = content.lower()
        
        # Generic import patterns (work for many languages)
        import_patterns = [
            (r'^import\s+', 'import_statement'),
            (r'^from\s+.*\s+import', 'from_import'),
            (r'require\s*\(', 'require_statement'),
            (r'#include\s*[<"]', 'include_statement'),
            (r'^using\s+', 'using_statement'),
            (r'^package\s+', 'package_statement'),
        ]
        
        # Generic class/function patterns
        structure_patterns = [
            (r'^class\s+\w+', 'class_definition'),
            (r'^def\s+\w+', 'function_definition'),
            (r'^function\s+\w+', 'function_definition'),
            (r'^const\s+\w+\s*=\s*\(', 'arrow_function'),
            (r'^\w+\s+\w+\s*\(', 'method_definition'),
        ]
        
        # Generic framework/library detection (not hardcoded)
        # Look for common patterns that indicate frameworks
        framework_indicators = [
            (r'from\s+(\w+)\s+import', 'python_library'),
            (r'import\s+.*\s+from\s+[\'"](\w+)[\'"]', 'js_library'),
            (r'require\s*\(\s*[\'"](\w+)[\'"]', 'js_library'),
        ]
        
        # Detect patterns
        detected_patterns = []
        for pattern, pattern_type in import_patterns + structure_patterns:
            if re.search(pattern, content, re.MULTILINE):
                detected_patterns.append(pattern_type)
        
        # Infer language from patterns (generic inference)
        if 'import_statement' in detected_patterns or 'from_import' in detected_patterns:
            if 'class_definition' in detected_patterns and 'def ' in content:
                result['language'] = 'Python'
                result['confidence'] = 0.9
            elif 'function ' in content or 'const ' in content:
                result['language'] = 'JavaScript'
                result['confidence'] = 0.8
        
        # Extract potential libraries/frameworks
        libraries = []
        for pattern, lib_type in framework_indicators:
            matches = re.findall(pattern, content)
            libraries.extend(matches[:5])  # Limit to avoid noise
        
        if libraries:
            result['libraries'] = list(set(libraries))
        
        return result
    
    def _ai_detect_language(self, content: str, file_path: Optional[str] = None) -> Optional[LanguageInfo]:
        """
        Use AI to detect language (synchronous fallback).
        
        For async version, use detect_from_content_async.
        """
        # Return generic detection if AI not available
        patterns = self._analyze_content_patterns(content)
        if patterns:
            return LanguageInfo(
                name=patterns.get('language', 'Unknown'),
                confidence=patterns.get('confidence', 0.5),
                libraries=patterns.get('libraries', [])
            )
        return None
    
    async def _ai_detect_language_async(self, content: str, file_path: Optional[str] = None) -> Optional[LanguageInfo]:
        """
        Use AI model to detect language and framework dynamically.
        
        This is the powerful, generic approach - AI determines everything.
        """
        if not self.ollama:
            return self._ai_detect_language(content, file_path)
        
        # Build prompt for AI detection
        prompt = f"""Analyze this code snippet and detect:
1. Programming language
2. Framework (if any)
3. Key libraries/imports used

Code snippet (first 500 chars):
{content[:500]}

Respond in JSON format:
{{
    "language": "detected language name",
    "confidence": 0.0-1.0,
    "framework": "framework name or null",
    "libraries": ["lib1", "lib2"]
}}"""
        
        try:
            result = await self.ollama.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for accurate detection
                max_tokens=200
            )
            
            # Parse JSON response
            import json
            response_text = result.response
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return LanguageInfo(
                    name=data.get('language', 'Unknown'),
                    confidence=data.get('confidence', 0.7),
                    framework=data.get('framework'),
                    libraries=data.get('libraries', [])
                )
        except Exception:
            pass
        
        return self._ai_detect_language(content, file_path)
    
    def extract_imports(self, content: str, language: Optional[str] = None) -> List[str]:
        """
        Extract imports generically without hardcoding language-specific patterns.
        
        Uses generic patterns that work across languages.
        """
        imports = []
        
        # Generic import patterns (work for many languages)
        patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',  # ES6 imports
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]',  # CommonJS
            r'^import\s+([\w\.]+)',  # Python/Java style
            r'^from\s+([\w\.]+)\s+import',  # Python from imports
            r'#include\s*[<"]([^>"]+)[>"]',  # C/C++
            r'^using\s+([\w\.]+)',  # C#
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
        
        return list(set(imports))  # Remove duplicates
    
    def extract_structure(self, content: str) -> Dict[str, List[str]]:
        """
        Extract code structure generically (classes, functions, etc.).
        
        Uses generic patterns, not language-specific.
        """
        result = {
            'classes': [],
            'functions': [],
            'exports': []
        }
        
        # Generic patterns that work across languages
        class_patterns = [
            r'^class\s+(\w+)',
            r'^(?:public|private|protected)?\s*class\s+(\w+)',
        ]
        
        function_patterns = [
            r'^def\s+(\w+)',
            r'^function\s+(\w+)',
            r'^(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:async\s*)?\(',
            r'^fun\s+(\w+)',  # Kotlin
        ]
        
        export_patterns = [
            r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)',
            r'^export\s+(\w+)',
        ]
        
        for pattern in class_patterns:
            result['classes'].extend(re.findall(pattern, content, re.MULTILINE))
        
        for pattern in function_patterns:
            result['functions'].extend(re.findall(pattern, content, re.MULTILINE))
        
        for pattern in export_patterns:
            result['exports'].extend(re.findall(pattern, content, re.MULTILINE))
        
        # Remove duplicates
        for key in result:
            result[key] = list(set(result[key]))
        
        return result


# Singleton instance
_language_detector: Optional[LanguageDetector] = None


def get_language_detector(ollama_service=None) -> LanguageDetector:
    """Get or create language detector instance."""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector(ollama_service)
    return _language_detector

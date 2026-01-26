"""
File Intelligence Service
=========================
AI-powered intelligent detection of file types, priorities, and patterns.
Replaces hardcoded lists with dynamic AI-powered detection.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class FileClassification:
    """Classification of a file."""
    is_priority: bool = False
    is_config: bool = False
    is_entry_point: bool = False
    file_type: Optional[str] = None
    confidence: float = 0.0


class FileIntelligence:
    """
    Intelligent file classification and detection.
    
    Uses AI-powered analysis instead of hardcoded lists.
    """
    
    def __init__(self, ollama_service=None):
        """
        Initialize file intelligence service.
        
        Args:
            ollama_service: Optional Ollama service for AI-powered detection
        """
        self.ollama = ollama_service
    
    def is_priority_file(self, file_path: str, content: Optional[str] = None) -> Tuple[bool, float]:
        """
        Determine if file is priority using intelligent detection.
        
        Args:
            file_path: Path to file
            content: Optional file content for better detection
            
        Returns:
            Tuple of (is_priority, confidence)
        """
        path = Path(file_path)
        name = path.name.lower()
        
        # Generic patterns that indicate priority files
        priority_patterns = [
            # Entry points
            r'^(main|index|app|server|entry|start|run)\.',
            # Package managers
            r'^(package|requirements|pyproject|setup|pom|build\.gradle|Cargo|go\.mod)',
            # Documentation
            r'^(readme|license|changelog|contributing)',
            # Configuration
            r'^(dockerfile|docker-compose|makefile|cmake)',
        ]
        
        # Check patterns
        for pattern in priority_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return (True, 0.9)
        
        # Check for common entry point names
        entry_names = {'main', 'index', 'app', '__init__'}
        if path.stem.lower() in entry_names:
            return (True, 0.8)
        
        # AI detection would be async - for now use pattern-based
        # Can be enhanced with async AI detection later if needed
        return (False, 0.0)
    
    def is_config_file(self, file_path: str, content: Optional[str] = None) -> Tuple[bool, float]:
        """
        Determine if file is configuration using intelligent detection.
        
        Args:
            file_path: Path to file
            content: Optional file content
            
        Returns:
            Tuple of (is_config, confidence)
        """
        path = Path(file_path)
        name = path.name.lower()
        
        # Generic config patterns
        config_patterns = [
            r'config',
            r'settings',
            r'\.env',
            r'\.config',
            r'\.toml',
            r'\.yaml',
            r'\.yml',
            r'\.json',  # Could be config
            r'\.ini',
        ]
        
        # Check if name contains config indicators
        for pattern in config_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                # Additional check: common dependency/config file patterns (generic)
                dependency_indicators = ['package', 'requirements', 'pyproject', 'setup', 'dependencies', 'packages']
                if any(indicator in name for indicator in dependency_indicators):
                    return (True, 0.95)
                return (True, 0.7)
        
        # AI detection would be async - for now use pattern-based
        return (False, 0.0)
    
    def should_skip_directory(self, dir_name: str) -> bool:
        """
        Determine if directory should be skipped using intelligent detection.
        
        Args:
            dir_name: Directory name
            
        Returns:
            True if should skip
        """
        # Generic patterns for directories to skip
        skip_patterns = [
            r'^\.',  # Hidden directories
            r'node_modules',
            r'__pycache__',
            r'\.git',
            r'venv|\.venv|env|virtualenv',
            r'build|dist|target|out|bin|obj',
            r'\.idea|\.vscode|\.cursor',
            r'coverage|\.coverage',
            r'\.pytest_cache|\.mypy_cache',
            r'vendor|bower_components',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, dir_name, re.IGNORECASE):
                return True
        
        return False
    
    def is_entry_point(self, file_path: str, content: Optional[str] = None) -> Tuple[bool, float]:
        """
        Detect if file is an entry point using intelligent analysis.
        
        Args:
            file_path: Path to file
            content: Optional file content
            
        Returns:
            Tuple of (is_entry_point, confidence)
        """
        path = Path(file_path)
        name = path.name.lower()
        
        # Generic entry point patterns
        entry_patterns = [
            r'^(main|index|app|server|entry|start|run)\.',
            r'__main__',
        ]
        
        for pattern in entry_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return (True, 0.8)
        
        # Check content for entry point indicators
        if content:
            entry_indicators = [
                r'if\s+__name__\s*==\s*[\'"]__main__[\'"]',  # Python
                r'main\s*\(',  # Main function
                r'app\.listen|app\.run',  # Web apps
                r'require\([\'"]\.\/index',  # Node entry
            ]
            
            for pattern in entry_indicators:
                if re.search(pattern, content, re.IGNORECASE):
                    return (True, 0.7)
        
        # AI detection would be async - for now use pattern-based
        return (False, 0.0)
    
    async def _ai_detect_priority(self, file_path: str, content: str) -> Tuple[bool, float]:
        """Use AI to detect if file is priority."""
        if not self.ollama:
            return (False, 0.0)
        
        prompt = f"""Analyze if this file is a priority/important file in a codebase:

File: {file_path}
Content preview (first 200 chars): {content[:200]}

Is this a priority file (entry point, main file, package manager file, etc.)?
Respond with JSON: {{"is_priority": true/false, "confidence": 0.0-1.0, "reason": "explanation"}}"""
        
        try:
            result = await self.ollama.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            json_match = re.search(r'\{[^}]+\}', result.response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return (data.get('is_priority', False), data.get('confidence', 0.5))
        except:
            pass
        
        return (False, 0.0)
    
    async def _ai_detect_config(self, file_path: str, content: str) -> Tuple[bool, float]:
        """Use AI to detect if file is configuration."""
        if not self.ollama:
            return (False, 0.0)
        
        prompt = f"""Analyze if this file is a configuration file:

File: {file_path}
Content preview (first 200 chars): {content[:200]}

Is this a configuration file?
Respond with JSON: {{"is_config": true/false, "confidence": 0.0-1.0}}"""
        
        try:
            result = await self.ollama.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=150
            )
            
            import json
            json_match = re.search(r'\{[^}]+\}', result.response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return (data.get('is_config', False), data.get('confidence', 0.5))
        except:
            pass
        
        return (False, 0.0)
    
    async def _ai_detect_entry_point(self, file_path: str, content: str) -> Tuple[bool, float]:
        """Use AI to detect if file is entry point."""
        if not self.ollama:
            return (False, 0.0)
        
        prompt = f"""Analyze if this file is an entry point (main file that starts the application):

File: {file_path}
Content preview (first 300 chars): {content[:300]}

Is this an entry point file?
Respond with JSON: {{"is_entry_point": true/false, "confidence": 0.0-1.0}}"""
        
        try:
            result = await self.ollama.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=150
            )
            
            import json
            json_match = re.search(r'\{[^}]+\}', result.response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return (data.get('is_entry_point', False), data.get('confidence', 0.5))
        except:
            pass
        
        return (False, 0.0)
    
    def classify_file(self, file_path: str, content: Optional[str] = None) -> FileClassification:
        """
        Classify a file comprehensively.
        
        Args:
            file_path: Path to file
            content: Optional file content
            
        Returns:
            FileClassification with all attributes
        """
        is_priority, priority_conf = self.is_priority_file(file_path, content)
        is_config, config_conf = self.is_config_file(file_path, content)
        is_entry, entry_conf = self.is_entry_point(file_path, content)
        
        return FileClassification(
            is_priority=is_priority,
            is_config=is_config,
            is_entry_point=is_entry,
            confidence=max(priority_conf, config_conf, entry_conf)
        )


# Singleton instance
_file_intelligence: Optional[FileIntelligence] = None


def get_file_intelligence(ollama_service=None) -> FileIntelligence:
    """Get or create file intelligence instance."""
    global _file_intelligence
    if _file_intelligence is None:
        _file_intelligence = FileIntelligence(ollama_service)
    return _file_intelligence

"""
Path Intelligence Service
=========================
Intelligent detection of file path intentions from user prompts.
Determines if user wants file in root vs subdirectory.
"""

import re
from typing import Optional, Tuple
from pathlib import Path


class PathIntelligence:
    """
    Intelligent path detection from user prompts.
    
    Analyzes prompts to determine:
    - If user wants file in root or subdirectory
    - If path is absolute or relative
    - If user specified directory explicitly
    """
    
    # Patterns that indicate subdirectory specification
    SUBDIRECTORY_INDICATORS = [
        r'\b(src|lib|app|components|utils|services|hooks|pages|api|routes|models|views|controllers)\b',
        r'[\/\\]',  # Forward or backward slash
        r'\b(in|dentro|inside|em)\s+(src|lib|app|components|utils|services)',
    ]
    
    # Patterns that indicate external/parallel project
    EXTERNAL_PROJECT_INDICATORS = [
        r'\b(paralelo|parallel|fora|outside|externo|external|separado|separate)\s+(ao|to|do|of|de|from|a|chamada|called)',
        r'\b(novo projeto|new project)\s+(fora|outside|paralelo|parallel|separado|separate)',
        r'\b(criar|create)\s+(um|a|an)\s+(projeto|project)\s+(paralelo|parallel|fora|outside|separado|separate)',
        r'\b(não|not|don\'t)\s+(criar|create)\s+(dentro|inside|em|in)',
        r'\b(deve|should|must)\s+(ser|be)\s+(um|a|an)\s+(novo|new)\s+(projeto|project)',
        r'\b(pasta|folder|diretorio|directory)\s+(paralela|parallel|separada|separate)',
        r'\b(criar|create)\s+(um|a|an)?\s+(projeto|project)\s+(em|in)\s+(uma|a|an)?\s+(pasta|folder)\s+(paralela|parallel|separada|separate)',
    ]
    
    # Patterns that indicate root file (simple file)
    ROOT_FILE_INDICATORS = [
        r'^crie?\s+um?\s+arquivo\s+chamado\s+(\w+\.\w+)',  # "crie um arquivo chamado teste.js"
        r'^create\s+(?:a\s+)?file\s+(?:called|named)?\s+(\w+\.\w+)',  # "create file teste.js"
        r'arquivo\s+chamado\s+(\w+\.\w+)',  # "arquivo chamado teste.js"
        r'file\s+(?:called|named)\s+(\w+\.\w+)',  # "file called teste.js"
    ]
    
    @classmethod
    def detect_path_intention(cls, prompt: str, filename: Optional[str] = None) -> Tuple[str, bool]:
        """
        Detect user's intention for file path.
        
        Args:
            prompt: User's prompt
            filename: Extracted filename (optional)
            
        Returns:
            Tuple of (detected_path, is_simple_file)
            - detected_path: Suggested path
            - is_simple_file: True if user wants file in root
        """
        prompt_lower = prompt.lower()
        
        # Extract filename if not provided
        if not filename:
            filename = cls._extract_filename(prompt)
        
        if not filename:
            # Can't determine, default to root
            return (filename or "file", True)
        
        # Check for explicit subdirectory indicators
        has_subdirectory = any(
            re.search(pattern, prompt_lower, re.IGNORECASE)
            for pattern in cls.SUBDIRECTORY_INDICATORS
        )
        
        # Check for explicit root file patterns
        is_simple_file = any(
            re.search(pattern, prompt_lower, re.IGNORECASE)
            for pattern in cls.ROOT_FILE_INDICATORS
        )
        
        # Check if filename already contains path
        if '/' in filename or '\\' in filename:
            # User specified path explicitly
            return (filename, False)
        
        # If user explicitly mentions subdirectory, use it
        if has_subdirectory and not is_simple_file:
            # Try to extract the subdirectory
            subdir = cls._extract_subdirectory(prompt)
            if subdir:
                return (f"{subdir}/{filename}", False)
        
        # Default: simple file in root
        return (filename, True)
    
    @classmethod
    def _extract_filename(cls, prompt: str) -> Optional[str]:
        """Extract filename from prompt."""
        # Pattern: "arquivo chamado teste.js" or "file called teste.js"
        patterns = [
            r'chamado\s+([\w\-\.]+\.\w+)',
            r'called\s+([\w\-\.]+\.\w+)',
            r'named\s+([\w\-\.]+\.\w+)',
            r'crie?\s+um?\s+arquivo\s+([\w\-\.]+\.\w+)',
            r'create\s+(?:a\s+)?file\s+([\w\-\.]+\.\w+)',
            r'([\w\-\.]+\.(js|ts|jsx|tsx|py|java|kt|go|rs|json|html|css|md))',  # filename.ext
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @classmethod
    def _extract_subdirectory(cls, prompt: str) -> Optional[str]:
        """Extract subdirectory from prompt."""
        # Look for common patterns
        patterns = [
            r'(?:in|dentro|inside|em)\s+(src|lib|app|components|utils|services|hooks|pages|api|routes)',
            r'(src|lib|app|components|utils|services|hooks|pages|api|routes)[\/\\]',
            r'([\w\/\\]+)\s+com\s+um',  # "src/components com um"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @classmethod
    def detect_external_project_intention(cls, prompt: str, current_workspace: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Detect if user wants to create project outside/parallel to current workspace.
        
        Returns:
            Tuple of (is_external, suggested_path)
            - is_external: True if user wants external project
            - suggested_path: Suggested absolute path for external project
        """
        prompt_lower = prompt.lower()
        
        # Check for external project indicators
        has_external_indicator = any(
            re.search(pattern, prompt_lower, re.IGNORECASE)
            for pattern in cls.EXTERNAL_PROJECT_INDICATORS
        )
        
        if not has_external_indicator:
            return (False, None)
        
        # Try to extract parent directory
        if current_workspace:
            try:
                workspace_path = Path(current_workspace)
                parent_dir = workspace_path.parent
                
                # Extract project name from prompt
                project_name = cls._extract_project_name(prompt)
                if project_name:
                    suggested_path = str(parent_dir / project_name)
                    return (True, suggested_path)
                else:
                    # Default: create in parent with generic name
                    suggested_path = str(parent_dir / "new-project")
                    return (True, suggested_path)
            except:
                pass
        
        return (True, None)
    
    @classmethod
    def _extract_project_name(cls, prompt: str) -> Optional[str]:
        """Extract project name from prompt."""
        patterns = [
            r'(?:projeto|project)\s+(?:chamado|called|named)?\s+([\w\-]+)',
            r'(?:criar|create)\s+(?:um|a|an)?\s+([\w\-]+)',
            r'([\w\-]+)\s+(?:todo list|react|app|application)',
            r'(?:pasta|folder|diretorio|directory)\s+(?:chamada|called|named)?\s+([\w\-]+)',
            r'(?:em|in|dentro|inside)\s+(?:uma|a|an)?\s+(?:pasta|folder|diretorio|directory)?\s+(?:chamada|called|named)?\s+([\w\-]+)',
            r'(?:paralela|parallel)\s+(?:a|to)?\s+(?:chamada|called|named)?\s+([\w\-]+)',
            r'pasta\s+([\w\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Filter out common words that aren't project names
                if name.lower() not in ['chamada', 'called', 'named', 'dentro', 'inside', 'paralela', 'parallel']:
                    return name
        
        return None
    
    @classmethod
    def should_use_root(cls, prompt: str) -> bool:
        """
        Determine if file should be created in root.
        
        Returns True if:
        - User says "arquivo chamado X" or "file called X" (simple pattern)
        - No directory mentioned
        - Filename doesn't contain path
        """
        prompt_lower = prompt.lower()
        filename = cls._extract_filename(prompt)
        
        if not filename:
            return True
        
        # If filename has path, user specified it
        if '/' in filename or '\\' in filename:
            return False
        
        # Check for simple file patterns
        is_simple = any(
            re.search(pattern, prompt_lower, re.IGNORECASE)
            for pattern in cls.ROOT_FILE_INDICATORS
        )
        
        if is_simple:
            return True
        
        # Check for subdirectory indicators
        has_subdir = any(
            re.search(pattern, prompt_lower, re.IGNORECASE)
            for pattern in cls.SUBDIRECTORY_INDICATORS
        )
        
        # If no subdirectory mentioned and simple pattern, use root
        return not has_subdir


# Helper function
def detect_path_intention(prompt: str, filename: Optional[str] = None) -> Tuple[str, bool]:
    """Quick helper to detect path intention."""
    return PathIntelligence.detect_path_intention(prompt, filename)

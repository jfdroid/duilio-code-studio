"""
Project Detector Service
========================
Uses AI to intelligently detect when user wants to create a project
that needs its own directory vs just creating files.
"""

import re
from typing import Optional, Tuple, Dict, Any
from services.ollama_service import OllamaService
from core.logger import get_logger


from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
class ProjectDetector:
    """
    Intelligent project detection using AI.
    
    Determines if user wants to:
    - Create a new project (needs directory)
    - Create files in existing workspace (no directory needed)
    """
    
    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service
        self.logger = get_logger()
    
    async def detect_project_intention(
        self,
        prompt: str,
        workspace_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if user wants to create a project that needs its own directory.
        
        Args:
            prompt: User's prompt
            workspace_path: Current workspace path
            
        Returns:
            Dict with:
            - needs_directory: bool - True if project needs its own directory
            - project_name: Optional[str] - Suggested project name
            - project_type: Optional[str] - Type of project (react, android, etc)
            - confidence: float - Confidence score 0.0-1.0
            - reasoning: str - AI's reasoning
        """
        if not self.ollama:
            return self._fallback_detection(prompt)
        
        system_prompt = """You are an intelligent project detection system.
Analyze the user's prompt and determine if they want to CREATE A NEW PROJECT that needs its own directory,
or just create files in the current workspace.

A PROJECT needs its own directory when:
- User says "criar um aplicativo", "criar um projeto", "create an app", "create a project"
- User mentions "todo list app", "react app", "android app", "delivery app", etc.
- User wants a "complete application" or "full project"
- User mentions multiple files that form a complete application structure

A PROJECT does NOT need its own directory when:
- User just wants to create a single file or a few related files
- User says "criar arquivo X" or "create file X"
- User wants to add files to existing project

Respond in JSON format:
{
    "needs_directory": true | false,
    "project_name": "suggested-project-name" | null,
    "project_type": "react" | "android" | "node" | "python" | "kmm" | "general" | null,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}

Examples:
User: "crie um aplicativo de lista de todo em android"
Response: {"needs_directory": true, "project_name": "android-todo-app", "project_type": "android", "confidence": 0.95, "reasoning": "user wants to create a complete Android application"}

User: "crie uma pagina web em react para um sistema de delivery"
Response: {"needs_directory": true, "project_name": "react-delivery-app", "project_type": "react", "confidence": 0.95, "reasoning": "user wants to create a complete React web application"}

User: "crie um arquivo teste.js"
Response: {"needs_directory": false, "project_name": null, "project_type": null, "confidence": 0.9, "reasoning": "user just wants to create a single file"}

User: "crie um projeto React completo"
Response: {"needs_directory": true, "project_name": "react-project", "project_type": "react", "confidence": 0.95, "reasoning": "user explicitly mentions creating a complete project"}
"""
        
        try:
            result = await self.ollama.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for deterministic detection
                max_tokens=200,
                format="json"
            )
            
            response_content = result.response
            
            # Parse JSON
            import json
            try:
                data = json.loads(response_content)
                return data
            except json.JSONDecodeError:
                # Try to extract JSON from markdown block
                json_match = re.search(r'```json\n(\{[\s\S]*?\})\n```', response_content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    return data
                
                # Fallback: try to extract JSON from any curly braces
                json_match = re.search(r'\{[^}]+\}', response_content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return data
                
                raise ValueError("Could not parse JSON from AI response.")
        
        except Exception as e:
            self.logger.error(
                f"Error during AI detection: {e}",
                context={"error": str(e), "prompt": prompt[:100]}
            )
            return self._fallback_detection(prompt)
    
    def _fallback_detection(self, prompt: str) -> Dict[str, Any]:
        """Fallback detection without AI."""
        prompt_lower = prompt.lower()
        
        # Project indicators
        project_keywords = [
            'aplicativo', 'app', 'application',
            'projeto', 'project',
            'sistema', 'system',
            'aplicação completa', 'complete application',
            'projeto completo', 'complete project',
            'todo list app', 'react app', 'android app',
            'delivery app', 'delivery system'
        ]
        
        # Single file indicators
        single_file_keywords = [
            'arquivo chamado', 'file called',
            'crie um arquivo', 'create a file',
            'arquivo X', 'file X'
        ]
        
        has_project = any(kw in prompt_lower for kw in project_keywords)
        has_single_file = any(kw in prompt_lower for kw in single_file_keywords)
        
        if has_project and not has_single_file:
            # Try to extract project name
            project_name = self._extract_project_name(prompt_lower)
            project_type = self._extract_project_type(prompt_lower)
            
            return {
                "needs_directory": True,
                "project_name": project_name or "new-project",
                "project_type": project_type,
                "confidence": 0.7,
                "reasoning": "fallback: project keywords detected"
            }
        
        return {
            "needs_directory": False,
            "project_name": None,
            "project_type": None,
            "confidence": 0.6,
            "reasoning": "fallback: no clear project intent"
        }
    
    def _extract_project_name(self, prompt_lower: str) -> Optional[str]:
        """Extract project name from prompt."""
        patterns = [
            r'(?:projeto|project)\s+(?:chamado|called|named)?\s+([\w\-]+)',
            r'(?:aplicativo|app|application)\s+(?:chamado|called|named)?\s+([\w\-]+)',
            r'([\w\-]+)\s+(?:todo list|react|android|delivery)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt_lower, re.IGNORECASE)
            if match:
                name = match.group(1)
                if name.lower() not in ['chamado', 'called', 'named']:
                    return name
        
        return None
    
    def _extract_project_type(self, prompt_lower: str) -> Optional[str]:
        """Extract project type from prompt."""
        if 'react' in prompt_lower or 'jsx' in prompt_lower:
            return "react"
        elif 'android' in prompt_lower:
            return "android"
        elif 'node' in prompt_lower or 'express' in prompt_lower:
            return "node"
        elif 'python' in prompt_lower:
            return "python"
        elif 'kmm' in prompt_lower or 'kotlin multiplatform' in prompt_lower:
            return "kmm"
        
        return "general"


def get_project_detector(ollama_service: Optional[OllamaService] = None) -> ProjectDetector:
    """Get or create project detector instance."""
    return ProjectDetector(ollama_service)

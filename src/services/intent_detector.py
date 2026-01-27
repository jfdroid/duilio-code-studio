"""
Intent Detector Service
=======================
Uses AI (Qwen/Ollama) to intelligently detect user intent instead of hardcoded patterns.
"""

import re
from typing import Optional, Tuple, Dict, Any
from services.ollama_service import OllamaService
from core.logger import get_logger


from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
class IntentDetector:
    """
    Intelligent intent detection using AI.
    
    Replaces hardcoded regex patterns and keyword lists with AI-powered analysis.
    """
    
    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service
        self.logger = get_logger()
    
    async def detect_file_intent(
        self, 
        prompt: str,
        workspace_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect user's intent regarding files using AI.
        
        Args:
            prompt: User's prompt
            workspace_path: Optional workspace path for context
            
        Returns:
            Dict with:
            - intent: 'read', 'create', 'modify', 'delete', or None
            - file_name: Extracted filename (if any)
            - confidence: Confidence score 0.0-1.0
            - reasoning: AI's reasoning
        """
        if not self.ollama:
            # Fallback to simple detection if no AI available
            return self._simple_detection(prompt)
        
        # Use AI to detect intent intelligently
        ai_prompt = f"""Analyze this user prompt and determine their intent regarding files:

User prompt: "{prompt}"

Determine:
1. What is the user's intent? (read, create, modify, delete, or none)
2. What file name are they referring to? (extract the filename if mentioned)
3. Your confidence level (0.0 to 1.0)

Respond in JSON format:
{{
    "intent": "read|create|modify|delete|none",
    "file_name": "extracted filename or null",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Examples:
- "o que está escrito no arquivo teste" → {{"intent": "read", "file_name": "teste", "confidence": 0.95}}
- "ler arquivo teste.txt" → {{"intent": "read", "file_name": "teste.txt", "confidence": 0.98}}
- "criar arquivo novo.js" → {{"intent": "create", "file_name": "novo.js", "confidence": 0.95}}
- "nao pedi para criar, pedi para ler" → {{"intent": "read", "file_name": null, "confidence": 0.9}}
- "o que tem no arquivo teste" → {{"intent": "read", "file_name": "teste", "confidence": 0.95}}"""

        try:
            result = await self.ollama.generate(
                prompt=ai_prompt,
                temperature=0.1,  # Low temperature for accurate detection
                max_tokens=200,
                system_prompt="You are an expert at understanding user intent. Be precise and accurate."
            )
            
            # Parse JSON response
            import json
            response_text = result.response.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return {
                    "intent": data.get("intent", "none"),
                    "file_name": data.get("file_name"),
                    "confidence": float(data.get("confidence", 0.5)),
                    "reasoning": data.get("reasoning", "")
                }
        except Exception as e:
            self.logger.warning(
                f"AI detection failed: {e}, using fallback",
                context={"error": str(e), "prompt": prompt[:100]}
            )
        
        # Fallback to simple detection
        return self._simple_detection(prompt)
    
    def _simple_detection(self, prompt: str) -> Dict[str, Any]:
        """
        Simple fallback detection without AI.
        """
        import re
        prompt_lower = prompt.lower()
        
        # Simple keyword-based detection
        read_keywords = ['ler', 'read', 'mostrar', 'show', 'o que está escrito', 'what is written', 
                        'conteúdo', 'content', 'pedi para ler', 'asked to read']
        create_keywords = ['criar', 'create', 'novo', 'new', 'fazer', 'make']
        
        has_read = any(kw in prompt_lower for kw in read_keywords)
        has_create = any(kw in prompt_lower for kw in create_keywords)
        
        if has_read and not has_create:
            # Try to extract filename
            file_match = re.search(r'(?:arquivo|file)\s+(\w+(?:\.\w+)?)', prompt_lower, re.IGNORECASE)
            file_name = file_match.group(1) if file_match else None
            return {
                "intent": "read",
                "file_name": file_name,
                "confidence": 0.7,
                "reasoning": "Detected read keywords"
            }
        elif has_create:
            file_match = re.search(r'(?:arquivo|file)\s+(\w+(?:\.\w+)?)', prompt_lower, re.IGNORECASE)
            file_name = file_match.group(1) if file_match else None
            return {
                "intent": "create",
                "file_name": file_name,
                "confidence": 0.7,
                "reasoning": "Detected create keywords"
            }
        
        return {
            "intent": "none",
            "file_name": None,
            "confidence": 0.5,
            "reasoning": "No clear intent detected"
        }


def get_intent_detector(ollama_service: Optional[OllamaService] = None) -> IntentDetector:
    """Get or create intent detector instance."""
    return IntentDetector(ollama_service)

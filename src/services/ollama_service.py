"""
Ollama Service
==============
Handles all AI/LLM operations via Ollama API.
Single Responsibility: AI text generation and model management.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass

from core.config import get_settings
from core.exceptions import OllamaConnectionError


@dataclass
class GenerationResult:
    """Result from text generation."""
    response: str
    model: str
    done: bool = True
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None
    context: Optional[List[int]] = None


class OllamaService:
    """
    Service for Ollama API interactions.
    
    Responsibilities:
    - Text/code generation
    - Model listing and management
    - Connection health checks
    - Streaming responses
    """
    
    # System prompt for code assistance
    CODE_SYSTEM_PROMPT = """You are DuilioCode, an expert programming assistant.

Your characteristics:
- Responds in English
- Provides clean, well-documented code following best practices
- Explains concepts clearly and didactically
- Suggests performance and security improvements
- Knows multiple languages: Python, JavaScript, TypeScript, Kotlin, Java, Go, Rust, C++
- Understands software architecture: Clean Architecture, SOLID, Design Patterns
- Provides practical examples whenever possible

When providing code:
- Use code blocks with the specified language (```python, ```javascript, etc)
- Add explanatory comments
- Indicate possible errors or edge cases"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OLLAMA_HOST
        self.timeout = self.settings.OLLAMA_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0)
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Ollama server status.
        
        Returns:
            Dict with status, models count, and default model availability.
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                return {
                    "status": "running",
                    "models_count": len(models),
                    "default_model_available": self.settings.DEFAULT_MODEL in model_names,
                    "models": model_names[:10]  # Return first 10
                }
            
            return {"status": "error", "message": f"Status code: {response.status_code}"}
            
        except httpx.ConnectError:
            return {"status": "offline", "message": "Ollama is not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models.
        
        Returns:
            List of model information dictionaries.
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            
            if response.status_code != 200:
                raise OllamaConnectionError(f"Failed to list models: {response.status_code}")
            
            data = response.json()
            models = []
            
            for model in data.get("models", []):
                # Calculate human-readable size
                size_bytes = model.get("size", 0)
                if size_bytes > 1e9:
                    size_str = f"{size_bytes / 1e9:.1f}GB"
                elif size_bytes > 1e6:
                    size_str = f"{size_bytes / 1e6:.1f}MB"
                else:
                    size_str = f"{size_bytes}B"
                
                models.append({
                    "name": model.get("name"),
                    "display_name": model.get("name", "").split(":")[0].title(),
                    "size": size_str,
                    "modified_at": model.get("modified_at"),
                    "installed": True,
                    "details": model.get("details", {})
                })
            
            return models
            
        except httpx.ConnectError:
            raise OllamaConnectionError("Cannot connect to Ollama server")
        except Exception as e:
            raise OllamaConnectionError(f"Error listing models: {str(e)}")
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> GenerationResult:
        """
        Generate text/code using specified model.
        
        Args:
            prompt: User prompt
            model: Model to use (defaults to settings)
            system_prompt: Custom system prompt
            context: Conversation context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            GenerationResult with response and metadata.
        """
        model = model or self.settings.DEFAULT_MODEL
        system = system_prompt or self.CODE_SYSTEM_PROMPT
        
        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"Conversation context:\n{context}\n\nNew question: {prompt}"
        
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )
            
            if response.status_code != 200:
                # Try fallback model
                if model != self.settings.FALLBACK_MODEL:
                    return await self.generate(
                        prompt=prompt,
                        model=self.settings.FALLBACK_MODEL,
                        system_prompt=system_prompt,
                        context=context,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                raise OllamaConnectionError(f"Generation failed: {response.status_code}")
            
            data = response.json()
            
            return GenerationResult(
                response=data.get("response", ""),
                model=data.get("model", model),
                done=data.get("done", True),
                total_duration=data.get("total_duration"),
                eval_count=data.get("eval_count"),
                context=data.get("context")
            )
            
        except httpx.ConnectError:
            raise OllamaConnectionError("Cannot connect to Ollama server")
        except Exception as e:
            raise OllamaConnectionError(f"Generation error: {str(e)}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream text generation token by token.
        
        Yields:
            Generated text tokens as they arrive.
        """
        model = model or self.settings.DEFAULT_MODEL
        system = system_prompt or self.CODE_SYSTEM_PROMPT
        
        try:
            client = await self._get_client()
            
            async with client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": system,
                    "stream": True,
                    "options": {"temperature": temperature}
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get singleton Ollama service instance."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service

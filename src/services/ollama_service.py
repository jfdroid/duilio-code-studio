"""
Ollama Service
==============
Handles all AI/LLM operations via Ollama API.
Single Responsibility: AI text generation and model management.
"""

import httpx
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_settings
from core.exceptions import OllamaConnectionError
from utils.retry import retry_async


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
    
    CODE_SYSTEM_PROMPT = """You are DuilioCode, an expert programming assistant.

CORE PRINCIPLES:
- Clean, well-documented, production-ready code
- Follows best practices and SOLID principles
- Supports: Python, JavaScript, TypeScript, Kotlin, Java, Go, Rust, C++
- Responds in English for technical content

FILE ACTIONS - CRITICAL FORMATS (USE THESE EXACT FORMATS):

1. CREATE FILE - MANDATORY FORMAT:
```create-file:path/to/file.ext
[complete file content here]
```

CRITICAL RULES:
- ALWAYS use ```create-file: (three backticks + create-file:)
- NEVER use ```bash or ```sh or any other language tag
- NEVER write "create-file:" as plain text or in explanations
- The path MUST include the FULL filename with extension
- CORRECT: ```create-file:teste.txt\nHello World\n```
- WRONG: ```bash\ncreate-file:teste.txt\n``` (don't use bash blocks)
- WRONG: create-file:teste.txt (missing backticks)
- WRONG: ```create-file:.txt\n``` (missing filename)

2. CREATE MULTIPLE FILES - ALL IN ONE RESPONSE:
```create-file:package.json
{
  "name": "my-app"
}
```
```create-file:src/index.js
import React from 'react';
```
```create-file:src/App.js
export default function App() { return <div>Hello</div>; }
```

3. CREATE DIRECTORY:
```create-directory:path/to/dir
```

4. MODIFY FILE:
```modify-file:path/to/file.ext
[COMPLETE file content with ALL existing code + your changes]
```

5. DELETE FILE/DIRECTORY:
```delete-file:path/to/file.ext
```
```delete-directory:path/to/dir
```

PATH RULES:
- Workspace files: Use RELATIVE paths (e.g., src/components/Button.jsx)
- External files: Use ABSOLUTE paths (e.g., /Users/username/Desktop/file.txt)
- If user says "paralelo", "fora", "novo projeto", "pasta paralela": Create in parent directory with ABSOLUTE path
- Simple files without directory: Create in ROOT (utils.js, NOT src/utils.js)
- Multiple files: Create ALL in ONE response using multiple ```create-file: blocks

PROJECT CREATION - CRITICAL RULES:
- When user asks for "project", "app", "aplicativo", "complete application": Create ALL files at once
- For Android projects: MUST create build.gradle, settings.gradle, app/build.gradle, AndroidManifest.xml, Kotlin/Java files
- For React projects: MUST create package.json, src/index.js, src/App.jsx, components, public/index.html
- For Node.js projects: MUST create package.json, index.js, complete structure
- Include ALL configuration files, entry points, and complete structure
- Follow framework patterns exactly (React, Android, Python, etc.)
- Match existing codebase style if provided in context
- DO NOT create partial projects - create COMPLETE, FUNCTIONAL projects

🚨 CRITICAL: If you create a directory with create-directory, you MUST ALSO create files inside it in the SAME response.
- WRONG: Only ```create-directory:my-project``` (no files)
- CORRECT: ```create-directory:my-project``` followed by ```create-file:my-project/package.json``` etc.
- NEVER create an empty directory - ALWAYS create files inside it immediately

RESPONSE FORMAT - CRITICAL:
- When user asks to CREATE files, your response MUST START with ```create-file: blocks
- DO NOT write explanations, introductions, or text BEFORE the create-file blocks
- DO NOT use ```bash, ```sh, or any code block language tags
- START your response IMMEDIATELY with: ```create-file:path/to/file.ext
- You can add explanations AFTER all create-file blocks are done
- Example CORRECT response:
  ```create-file:teste.txt
  Hello World
  ```
  [Optional explanation here after file is created]

- Example WRONG response:
  "Vamos criar o arquivo..." [explanation first - WRONG]
  ```bash
  create-file:teste.txt [WRONG - don't use bash blocks]
  ```

CONTEXT:
- Remember files created in previous messages
- When user says "that file" or "the file we created", reference previous context
- Analyze codebase structure when provided"""

    # System prompt for general/creative tasks
    GENERAL_SYSTEM_PROMPT = """You are DuilioCode, a helpful and creative AI assistant.

Your characteristics:
- IMPORTANT: Always respond in the SAME LANGUAGE the user writes to you. If they write in Portuguese, respond in Portuguese. If in English, respond in English. Match their language exactly.
- You are creative, helpful, and knowledgeable
- You can write stories, poems, presentations, articles
- You explain complex topics in simple terms
- You are friendly and engaging
- You provide detailed and thoughtful responses

Be natural and conversational while being helpful and informative."""

    @classmethod
    def is_code_related(cls, prompt: str) -> bool:
        """Detect if the prompt is code-related using intelligent classification."""
        try:
            from services.prompt_classifier import classify_prompt
            classification = classify_prompt(prompt)
            return classification.is_code_related
        except:
            prompt_lower = prompt.lower()
            code_patterns = ['()', '{}', '[]', '=>', '->', '==', '!=', '&&', '||', '```']
            for pattern in code_patterns:
                if pattern in prompt:
                    return True
            return False

    @classmethod
    def get_recommended_model(cls, prompt: str, available_models: list) -> tuple:
        """
        Get recommended model using intelligent classification.
        Uses PromptClassifier instead of hardcoded model lists.
        """
        try:
            from services.prompt_classifier import classify_prompt
            classification = classify_prompt(prompt, available_models)
            return (
                classification.recommended_model,
                classification.is_code_related,
                classification.reasoning
            )
        except:
            model_names = [m.lower() if isinstance(m, str) else m.get('name', '').lower() for m in available_models]
            is_code = cls.is_code_related(prompt)
            return (model_names[0] if model_names else 'qwen2.5-coder:14b', is_code, "Using default model")

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OLLAMA_HOST
        self.timeout = self.settings.OLLAMA_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            # Use connection pooling for better performance
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=limits,
                http2=False  # Ollama doesn't support HTTP/2
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
                    "models": model_names[:10]
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
    
    @retry_async(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        retry_on=[httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError]
    )
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        auto_select_model: bool = True
    ) -> GenerationResult:
        """
        Generate text/code using specified model.
        
        Args:
            prompt: User prompt
            model: Model to use (defaults to smart selection)
            system_prompt: Custom system prompt
            context: Conversation context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            auto_select_model: If True, automatically select best model
            
        Returns:
            GenerationResult with response and metadata.
        """
        is_code = self.is_code_related(prompt)
        
        if model is None and auto_select_model:
            try:
                models = await self.list_models()
                model, _, _ = self.get_recommended_model(prompt, models)
            except:
                model = self.settings.DEFAULT_MODEL
        else:
            model = model or self.settings.DEFAULT_MODEL
        
        if system_prompt is None:
            system = self.CODE_SYSTEM_PROMPT if is_code else self.GENERAL_SYSTEM_PROMPT
        else:
            system = system_prompt
        
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

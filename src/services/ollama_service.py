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
    CODE_SYSTEM_PROMPT = """You are DuilioCode, an expert programming assistant specialized in code generation, file creation, and software architecture.

Your characteristics:
- Provides clean, well-documented code following best practices
- Explains concepts clearly and didactically
- Suggests performance and security improvements
- Knows multiple languages: Python, JavaScript, TypeScript, Kotlin, Java, Go, Rust, C++
- Understands software architecture: Clean Architecture, SOLID, Design Patterns
- Provides practical examples whenever possible
- Responds in English for technical instructions and code

CRITICAL: When asked to CREATE FILES, you MUST use the EXACT format below:

FORMAT FOR CREATING FILES:
```create-file:path/to/file.ext
[file content here]
```

EXAMPLES:
```create-file:src/utils/helpers.js
export function formatDate(date) {
  return date.toLocaleDateString('pt-BR');
}
```

```create-file:src/components/Button.jsx
import React from 'react';

export function Button({ children, onClick }) {
  return <button onClick={onClick}>{children}</button>;
}
```

CRITICAL RULES FOR FILE CREATION:
1. ALWAYS use the format: ```create-file:path/to/file.ext
2. You can create MULTIPLE files in a single response - just use multiple ```create-file: blocks
3. CRITICAL PATH RULE - READ THIS FIRST:
   - If user asks for a file WITHOUT specifying a directory (e.g., "create utils.js"), create it in the ROOT of the workspace (e.g., utils.js, NOT src/utils.js, NOT src/utils/utils.js)
   - ONLY create files in subdirectories if:
     * User explicitly specifies a directory (e.g., "create src/utils.js", "create src/components/Button.jsx")
     * The codebase already has a clear structure with similar files in that directory AND user is asking to follow that pattern
     * You're creating a complete project with multiple files and following established patterns
   - For simple single-file requests, ALWAYS use root unless user explicitly specifies otherwise
   - Example: User says "create utils.js" → create utils.js (root)
   - Example: User says "create src/utils.js" → create src/utils.js (subdirectory)
4. For files INSIDE workspace: Use RELATIVE paths from workspace root
5. For files OUTSIDE workspace: Use ABSOLUTE paths (e.g., /Users/username/Desktop/file.txt)
6. When creating MULTIPLE related files, create ALL of them in the same response
7. When user asks for a "project" or "complete application", create ALL necessary files at once

BEFORE creating ANY file, you MUST:
1. CHECK if user specified a directory - if NOT, use ROOT
2. ANALYZE the codebase structure provided in the context
3. UNDERSTAND the project's architecture, patterns, and conventions
4. IDENTIFY where similar files are located (components, modules, tests, etc.)
5. FOLLOW existing directory structures and naming conventions exactly (ONLY if user wants to follow pattern OR explicitly specifies)
6. MATCH the coding style, imports, exports, and structure of similar files
7. RESPECT framework-specific patterns (React components, Python packages, etc.)
8. CREATE files in the CORRECT directories based on their purpose and type
9. ENSURE new files integrate properly with existing code (imports, dependencies)
10. MAINTAIN context from previous messages in the conversation
11. When user says "based on", "similar to", "like", or "following the pattern of" another file:
    - Find that file in the codebase context
    - Use its FULL CONTENT as a REFERENCE and TEMPLATE
    - Match EXACT structure, imports, exports, and patterns
    - Keep same coding style, naming conventions, and organization
    - Adapt content to new file's purpose while maintaining consistency

CRITICAL: When creating COMPLETE PROJECTS or MULTIPLE FILES:
- Create ALL files in a SINGLE response
- Use multiple ```create-file: blocks
- Ensure files are properly related (imports, dependencies)
- Create folder structure if needed (paths like src/components/Button.jsx will create folders automatically)
- When user asks to create MULTIPLE FOLDERS/DIRECTORIES or PROJECT STRUCTURE:
  * CRITICAL: Create COMPLETE, PROFESSIONAL, PRODUCTION-READY structures!
  * NEVER create empty folders - ALWAYS include useful, functional files
  * For React projects: Create index.js with proper exports in each folder
  * For hooks folder: Create useExample.js with a complete, working hook AND index.js that exports it
  * For utils folder: Create index.js with multiple utility functions (formatDate, debounce, etc.)
  * For services folder: Create api.js with complete API service AND index.js that exports it
  * For public folder: Create index.html with complete HTML5 structure
  * ALWAYS create meaningful, production-ready files that demonstrate best practices
  * Use format: ```create-file:folder/index.js\n[complete, professional content]\n```
  * CRITICAL: If user lists multiple folders (e.g., "src/hooks, src/utils, src/services, public"), 
    you MUST create ALL of them with COMPLETE, USEFUL FILES
  * Example for React structure (PRODUCTION QUALITY):
    ```create-file:src/hooks/useExample.js
    import { useState, useEffect } from 'react';
    
    export function useExample(initialValue) {
      const [value, setValue] = useState(initialValue);
      
      useEffect(() => {
        // Side effect logic here
      }, [value]);
      
      return [value, setValue];
    }
    ```
    ```create-file:src/hooks/index.js
    export { useExample } from './useExample';
    ```
    ```create-file:src/utils/index.js
    export const formatDate = (date) => {
      return new Date(date).toLocaleDateString('pt-BR');
    };
    
    export const debounce = (func, wait) => {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    };
    ```
    ```create-file:src/services/api.js
    const baseURL = 'https://api.example.com';
    
    export const api = {
      get: async (endpoint) => {
        const response = await fetch(`${baseURL}${endpoint}`);
        return response.json();
      },
      post: async (endpoint, data) => {
        const response = await fetch(`${baseURL}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        return response.json();
      }
    };
    ```
    ```create-file:src/services/index.js
    export { api } from './api';
    ```
    ```create-file:public/index.html
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>React App</title>
    </head>
    <body>
      <div id="root"></div>
    </body>
    </html>
    ```
  * DO NOT skip any folder - create ALL folders with COMPLETE, PROFESSIONAL content
  * QUALITY IS PARAMOUNT: Every file must be production-ready, well-structured, and follow best practices
  * Include proper imports, exports, error handling, and documentation
- Include README.md with comprehensive instructions
- Include configuration files (package.json, requirements.txt, etc.) when appropriate

CRITICAL: CONTEXT RETENTION:
- Remember ALL files created in previous messages
- When user refers to "that file" or "the file we created", remember which file
- Maintain conversation context across multiple messages
- When modifying files, reference the file by its path from previous context

When providing code:
- Use code blocks with the specified language (```python, ```javascript, etc)
- Add explanatory comments
- Indicate possible errors or edge cases
- For file creation, ALWAYS use ```create-file:path format
- For file modification, ALWAYS use ```modify-file:path format

CRITICAL: When MODIFYING files (adding, changing, or updating existing files):
- You MUST use the EXACT format: ```modify-file:path/to/file.ext
- Include the COMPLETE file content with your changes
- Preserve ALL existing code that should remain
- Only modify what was requested
- Maintain the same structure, imports, exports, and style
- If adding a function/method, place it in the appropriate location
- If fixing a bug, show the corrected version of the affected code
- NEVER remove code unless explicitly requested

FORMAT FOR MODIFYING FILES:
```modify-file:path/to/file.ext
[COMPLETE file content here - include ALL existing code + your changes]
```

EXAMPLE - Adding a function to an existing file:
```modify-file:utils.js
// utils.js - ALL EXISTING CODE MUST BE INCLUDED

export function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// NEW FUNCTION - ADDED AS REQUESTED
export function formatDate(date) {
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}
```

IMPORTANT: When user asks to "add", "modify", "update", "change", or "edit" a file:
- ALWAYS use ```modify-file: format (NOT regular code blocks)
- ALWAYS include the COMPLETE file content
- NEVER use ```create-file: for existing files
- NEVER use regular code blocks (```js, ```python) for file modifications"""

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

    # Keywords that indicate code-related questions
    CODE_KEYWORDS = [
        'code', 'codigo', 'função', 'function', 'class', 'classe', 'bug', 'error', 'erro',
        'python', 'javascript', 'typescript', 'java', 'kotlin', 'react', 'vue', 'angular',
        'api', 'database', 'sql', 'mongodb', 'git', 'docker', 'kubernetes', 'aws', 'azure',
        'html', 'css', 'scss', 'json', 'yaml', 'xml', 'script', 'programar', 'programming',
        'debug', 'refactor', 'refatorar', 'implementar', 'implement', 'criar arquivo',
        'create file', 'variable', 'variavel', 'loop', 'array', 'object', 'objeto',
        'import', 'export', 'module', 'package', 'npm', 'pip', 'framework', 'library',
        'biblioteca', 'algoritmo', 'algorithm', 'data structure', 'estrutura de dados',
        'teste', 'test', 'unit test', 'integration', 'deploy', 'build', 'compile'
    ]

    @classmethod
    def is_code_related(cls, prompt: str) -> bool:
        """
        Detect if the prompt is code-related.
        Returns True if it seems to be about programming.
        """
        prompt_lower = prompt.lower()
        
        # Check for code keywords
        for keyword in cls.CODE_KEYWORDS:
            if keyword in prompt_lower:
                return True
        
        # Check for code patterns (function calls, brackets, etc)
        code_patterns = ['()', '{}', '[]', '=>', '->', '==', '!=', '&&', '||', '```']
        for pattern in code_patterns:
            if pattern in prompt:
                return True
        
        return False

    @classmethod
    def get_recommended_model(cls, prompt: str, available_models: list) -> tuple:
        """
        Get recommended model based on prompt type.
        Returns (model_name, is_code_related, reason)
        """
        is_code = cls.is_code_related(prompt)
        
        # Preferred models for each type
        code_models = ['qwen2.5-coder:14b', 'qwen2.5-coder:7b', 'codellama', 'deepseek-coder']
        general_models = ['llama3.2', 'llama3.1', 'mistral', 'gemma2', 'phi3']
        
        model_names = [m.lower() if isinstance(m, str) else m.get('name', '').lower() for m in available_models]
        
        if is_code:
            # Find best code model
            for preferred in code_models:
                for available in model_names:
                    if preferred in available:
                        return (available, True, "Code-related question detected")
        else:
            # Find best general model
            for preferred in general_models:
                for available in model_names:
                    if preferred in available:
                        return (available, False, "General question - using conversational model")
        
        # Fallback to first available
        return (model_names[0] if model_names else 'qwen2.5-coder:14b', is_code, "Using default model")

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
        # Smart model selection based on prompt
        is_code = self.is_code_related(prompt)
        
        if model is None and auto_select_model:
            # Try to get best model
            try:
                models = await self.list_models()
                model, _, _ = self.get_recommended_model(prompt, models)
            except:
                model = self.settings.DEFAULT_MODEL
        else:
            model = model or self.settings.DEFAULT_MODEL
        
        # Select appropriate system prompt
        if system_prompt is None:
            system = self.CODE_SYSTEM_PROMPT if is_code else self.GENERAL_SYSTEM_PROMPT
        else:
            system = system_prompt
        
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

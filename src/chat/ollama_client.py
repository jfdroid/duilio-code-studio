"""
Ollama Client - Local LLM Integration
=====================================
Full-featured client for Ollama with streaming, vision, and code support.
"""

import asyncio
import base64
from pathlib import Path
from typing import AsyncGenerator, Optional, List, Dict, Any

import httpx
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import settings


class OllamaClient:
    """Async client for Ollama API - Bilingual (PT-BR / EN)."""
    
    # System prompt - Português do Brasil (PT-BR)
    DEFAULT_SYSTEM = """Você é um assistente de IA útil e prestativo.
REGRA OBRIGATÓRIA: Responda SEMPRE em Português do Brasil (PT-BR).
- Use vocabulário brasileiro (não português de Portugal)
- Seja direto, preciso e útil
- Independente do idioma da pergunta, responda em PT-BR"""
    
    def __init__(
        self,
        host: str = None,
        model: str = None,
        timeout: int = None,
        system_prompt: str = None
    ):
        self.host = host or settings.OLLAMA_URL
        self.model = model or settings.OLLAMA_CHAT_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM
        self.conversation_history: List[Dict[str, str]] = []
    
    async def _request(self, endpoint: str, data: dict) -> Any:
        """Make non-streaming request to Ollama API."""
        url = f"{self.host}/api/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    
    async def _request_stream(self, endpoint: str, data: dict) -> AsyncGenerator[dict, None]:
        """Make streaming request to Ollama API."""
        url = f"{self.host}/api/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=data) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import orjson
                        yield orjson.loads(line)
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str:
        """Generate text response."""
        data = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if system:
            data["system"] = system
        
        if stream:
            return self._stream_generate(data)
        else:
            result = await self._request("generate", data)
            return result.get("response", "")
    
    async def _stream_generate(self, data: dict) -> AsyncGenerator[str, None]:
        """Stream generate response."""
        data["stream"] = True
        async for chunk in self._request_stream("generate", data):
            if "response" in chunk:
                yield chunk["response"]
    
    async def chat(
        self,
        message: str,
        model: str = None,
        system: str = None,
        images: List[str] = None,
        keep_history: bool = True,
        stream: bool = False
    ):
        """Chat with context history. Bilingual: responds in user's language."""
        # Build message
        msg = {"role": "user", "content": message}
        if images:
            msg["images"] = images  # Base64 encoded
        
        messages = []
        # Use provided system prompt or default bilingual prompt
        effective_system = system or self.system_prompt
        if effective_system:
            messages.append({"role": "system", "content": effective_system})
        
        if keep_history:
            messages.extend(self.conversation_history)
        
        messages.append(msg)
        
        data = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        
        if stream:
            return self._stream_chat(data, msg, keep_history)
        else:
            result = await self._request("chat", data)
            response = result.get("message", {}).get("content", "")
            
            if keep_history:
                self.conversation_history.append(msg)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            return response
    
    async def _stream_chat(
        self,
        data: dict,
        user_msg: dict,
        keep_history: bool
    ) -> AsyncGenerator[str, None]:
        """Stream chat response."""
        data["stream"] = True
        full_response = ""
        
        async for chunk in self._request_stream("chat", data):
            if "message" in chunk and "content" in chunk["message"]:
                content = chunk["message"]["content"]
                full_response += content
                yield content
        
        if keep_history:
            self.conversation_history.append(user_msg)
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
    
    async def chat_with_image(
        self,
        message: str,
        image_path: str = None,
        image_base64: str = None,
        model: str = None
    ) -> str:
        """Chat about an image using vision model."""
        model = model or settings.OLLAMA_VISION_MODEL
        
        if image_path:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode()
        
        return await self.chat(
            message=message,
            model=model,
            images=[image_base64],
            keep_history=False
        )
    
    async def code(
        self,
        prompt: str,
        language: str = "python",
        model: str = None
    ) -> str:
        """Generate or explain code."""
        model = model or settings.OLLAMA_CODE_MODEL
        system = f"You are an expert {language} programmer. Provide clean, efficient code with comments."
        
        return await self.generate(
            prompt=prompt,
            model=model,
            system=system
        )
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    async def list_models(self) -> List[dict]:
        """List available models."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
    
    async def pull_model(self, model: str) -> AsyncGenerator[dict, None]:
        """Pull/download a model."""
        data = {"name": model, "stream": True}
        async for chunk in self._request_stream("pull", data):
            yield chunk


# Convenience functions
_client: Optional[OllamaClient] = None


def get_client() -> OllamaClient:
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client


async def chat(message: str, **kwargs) -> str:
    """Quick chat function."""
    return await get_client().chat(message, **kwargs)


async def chat_stream(message: str, **kwargs) -> AsyncGenerator[str, None]:
    """Quick streaming chat."""
    async for chunk in await get_client().chat(message, stream=True, **kwargs):
        yield chunk


async def generate(prompt: str, **kwargs) -> str:
    """Quick generate function."""
    return await get_client().generate(prompt, **kwargs)


async def analyze_image(image_path: str, question: str = "Describe this image in detail") -> str:
    """Analyze an image."""
    return await get_client().chat_with_image(question, image_path=image_path)


async def code(prompt: str, language: str = "python") -> str:
    """Generate code."""
    return await get_client().code(prompt, language)

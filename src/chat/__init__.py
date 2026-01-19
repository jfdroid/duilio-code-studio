"""Chat module with Ollama integration."""

from .ollama_client import OllamaClient, chat, chat_stream

__all__ = ["OllamaClient", "chat", "chat_stream"]

"""
Conversation Service
====================
Manages conversation history and context for AI interactions.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from core.config import get_settings


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float = field(default_factory=time.time)
    model: Optional[str] = None
    category: Optional[str] = None


@dataclass
class Conversation:
    """A conversation with message history."""
    id: str
    title: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    workspace_path: Optional[str] = None
    total_tokens: int = 0


class ConversationService:
    """
    Service for managing conversation history.
    
    Features:
    - Create/load/save conversations
    - Build context from history
    - Summarize long conversations
    - Track token usage
    """
    
    MAX_CONVERSATIONS = 50
    MAX_CONTEXT_MESSAGES = 10
    
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.DATA_DIR) / "conversations"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._conversations: Dict[str, Conversation] = {}
        self._current_id: Optional[str] = None
    
    def _generate_id(self) -> str:
        """Generate unique conversation ID."""
        return f"conv_{int(time.time() * 1000)}"
    
    def _get_file_path(self, conv_id: str) -> Path:
        """Get file path for a conversation."""
        return self.data_dir / f"{conv_id}.json"
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """Save conversation to disk."""
        file_path = self._get_file_path(conversation.id)
        data = {
            "id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "model": m.model,
                    "category": m.category
                }
                for m in conversation.messages
            ],
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "workspace_path": conversation.workspace_path,
            "total_tokens": conversation.total_tokens
        }
        file_path.write_text(json.dumps(data, indent=2))
    
    def _load_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Load conversation from disk."""
        file_path = self._get_file_path(conv_id)
        
        if not file_path.exists():
            return None
        
        try:
            data = json.loads(file_path.read_text())
            messages = [
                Message(
                    role=m["role"],
                    content=m["content"],
                    timestamp=m.get("timestamp", 0),
                    model=m.get("model"),
                    category=m.get("category")
                )
                for m in data.get("messages", [])
            ]
            
            return Conversation(
                id=data["id"],
                title=data["title"],
                messages=messages,
                created_at=data.get("created_at", 0),
                updated_at=data.get("updated_at", 0),
                workspace_path=data.get("workspace_path"),
                total_tokens=data.get("total_tokens", 0)
            )
        except Exception as e:
            print(f"[DuilioCode] Error loading conversation {conv_id}: {e}")
            return None
    
    def create_conversation(
        self,
        title: Optional[str] = None,
        workspace_path: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        conv_id = self._generate_id()
        title = title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conversation = Conversation(
            id=conv_id,
            title=title,
            workspace_path=workspace_path
        )
        
        self._conversations[conv_id] = conversation
        self._current_id = conv_id
        self._save_conversation(conversation)
        
        return conversation
    
    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        if conv_id in self._conversations:
            return self._conversations[conv_id]
        
        conversation = self._load_conversation(conv_id)
        if conversation:
            self._conversations[conv_id] = conversation
        
        return conversation
    
    def get_current(self) -> Optional[Conversation]:
        """Get current active conversation."""
        if self._current_id:
            return self.get_conversation(self._current_id)
        return None
    
    def set_current(self, conv_id: str) -> Optional[Conversation]:
        """Set the current active conversation."""
        conversation = self.get_conversation(conv_id)
        if conversation:
            self._current_id = conv_id
        return conversation
    
    def list_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List all conversations with metadata."""
        conversations = []
        
        try:
            for file_path in self.data_dir.glob("conv_*.json"):
                try:
                    data = json.loads(file_path.read_text())
                    conversations.append({
                        "id": data["id"],
                        "title": data["title"],
                        "updated_at": data.get("updated_at", 0),
                        "message_count": len(data.get("messages", [])),
                        "workspace_path": data.get("workspace_path")
                    })
                except:
                    continue
        except:
            pass
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return conversations[:limit]
    
    def add_message(
        self,
        role: str,
        content: str,
        conv_id: Optional[str] = None,
        model: Optional[str] = None,
        category: Optional[str] = None
    ) -> Message:
        """Add a message to a conversation."""
        if conv_id is None:
            conv_id = self._current_id
        
        if conv_id is None:
            # Create new conversation if none exists
            conversation = self.create_conversation()
            conv_id = conversation.id
        else:
            conversation = self.get_conversation(conv_id)
            if not conversation:
                conversation = self.create_conversation()
                conv_id = conversation.id
        
        message = Message(
            role=role,
            content=content,
            model=model,
            category=category
        )
        
        conversation.messages.append(message)
        conversation.updated_at = time.time()
        
        # Update title from first user message
        if len(conversation.messages) == 1 and role == "user":
            conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        self._save_conversation(conversation)
        
        return message
    
    def get_context_messages(
        self,
        conv_id: Optional[str] = None,
        max_messages: int = None
    ) -> List[Dict[str, str]]:
        """
        Get messages formatted for AI context.
        Returns recent messages in chat format.
        """
        if conv_id is None:
            conv_id = self._current_id
        
        if conv_id is None:
            return []
        
        conversation = self.get_conversation(conv_id)
        if not conversation:
            return []
        
        max_messages = max_messages or self.MAX_CONTEXT_MESSAGES
        messages = conversation.messages[-max_messages:]
        
        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
    
    def build_context_string(
        self,
        conv_id: Optional[str] = None,
        max_messages: int = 5
    ) -> str:
        """
        Build a context string from conversation history.
        Useful for including in prompts.
        """
        messages = self.get_context_messages(conv_id, max_messages)
        
        if not messages:
            return ""
        
        parts = ["=== CONVERSATION HISTORY ==="]
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:500]  # Truncate long messages
            if len(msg["content"]) > 500:
                content += "..."
            parts.append(f"{role}: {content}")
        
        return "\n\n".join(parts)
    
    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation."""
        file_path = self._get_file_path(conv_id)
        
        if file_path.exists():
            file_path.unlink()
        
        if conv_id in self._conversations:
            del self._conversations[conv_id]
        
        if self._current_id == conv_id:
            self._current_id = None
        
        return True
    
    def clear_all(self) -> None:
        """Clear all conversations."""
        for file_path in self.data_dir.glob("conv_*.json"):
            try:
                file_path.unlink()
            except:
                pass
        
        self._conversations.clear()
        self._current_id = None


# Singleton instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get singleton conversation service instance."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service

"""
Conversation Memory Service
============================
Conversation memory with efficient structure to maintain context.

BigO:
- Add: O(1)
- Search: O(n) linear, O(log n) with index
- Clear: O(1)
"""

from typing import Dict, List, Set, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileCreationRecord:
    """File creation record."""
    path: str
    content_preview: str
    timestamp: datetime
    dependencies: List[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FileModificationRecord:
    """File modification record."""
    path: str
    modification_type: str  # 'added', 'modified', 'deleted'
    timestamp: datetime
    preview: str = ""
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConversationMemory:
    """
    Conversation memory with efficient structure.
    
    Maintains history of created/modified files and architectural
    decisions for reference in future messages.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize conversation memory.
        
        Args:
            max_size: Maximum size of records (uses deque with maxlen)
        """
        self.created_files: deque = deque(maxlen=max_size)
        self.modified_files: deque = deque(maxlen=max_size)
        self.file_index: Dict[str, FileCreationRecord] = {}  # path -> record
        self.architectural_decisions: List[Dict] = []
        self.conversation_summary: str = ""
    
    def record_file_creation(
        self, 
        path: str, 
        content: str, 
        dependencies: List[str] = None,
        metadata: Dict = None
    ):
        """
        Record file creation.
        
        Args:
            path: Path of created file
            content: File content
            dependencies: List of dependencies
            metadata: Optional metadata
        """
        record = FileCreationRecord(
            path=path,
            content_preview=content[:200] if content else "",
            timestamp=datetime.now(),
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        self.created_files.append(record)
        self.file_index[path] = record
    
    def record_file_modification(
        self,
        path: str,
        modification_type: str,
        preview: str = "",
        metadata: Dict = None
    ):
        """
        Record file modification.
        
        Args:
            path: Path of modified file
            modification_type: Type of modification
            preview: Preview of changes
            metadata: Optional metadata
        """
        record = FileModificationRecord(
            path=path,
            modification_type=modification_type,
            timestamp=datetime.now(),
            preview=preview[:200] if preview else "",
            metadata=metadata or {}
        )
        self.modified_files.append(record)
    
    def record_architectural_decision(self, decision: str, context: Dict = None):
        """
        Record architectural decision.
        
        Args:
            decision: Description of the decision
            context: Additional context
        """
        self.architectural_decisions.append({
            'decision': decision,
            'context': context or {},
            'timestamp': datetime.now()
        })
    
    def get_file_record(self, path: str) -> Optional[FileCreationRecord]:
        """Return file record if exists."""
        return self.file_index.get(path)
    
    def get_context_summary(self) -> str:
        """
        Return efficient summary of conversation context.
        
        Returns:
            Formatted string with summary
        """
        parts = []
        
        if self.created_files:
            parts.append("=== FILES CREATED IN THIS CONVERSATION ===")
            for record in self.created_files:
                parts.append(f"- {record.path}")
                if record.dependencies:
                    parts.append(f"  Dependencies: {', '.join(record.dependencies)}")
            parts.append("")
        
        if self.modified_files:
            parts.append("=== FILES MODIFIED IN THIS CONVERSATION ===")
            for record in self.modified_files:
                parts.append(f"- {record.path} ({record.modification_type})")
            parts.append("")
        
        if self.architectural_decisions:
            parts.append("=== ARCHITECTURAL DECISIONS ===")
            for decision in self.architectural_decisions[-5:]:  # Últimas 5
                parts.append(f"- {decision['decision']}")
            parts.append("")
        
        return "\n".join(parts)
    
    def get_recent_files(self, limit: int = 10) -> List[str]:
        """Return list of recently created files."""
        return [record.path for record in list(self.created_files)[-limit:]]
    
    def clear(self):
        """Clear all memory."""
        self.created_files.clear()
        self.modified_files.clear()
        self.file_index.clear()
        self.architectural_decisions.clear()
        self.conversation_summary = ""

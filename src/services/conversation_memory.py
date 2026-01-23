"""
Conversation Memory Service
============================
Memória de conversa com estrutura eficiente para manter contexto.

BigO:
- Adicionar: O(1)
- Buscar: O(n) linear, O(log n) com índice
- Limpar: O(1)
"""

from typing import Dict, List, Set, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileCreationRecord:
    """Registro de criação de arquivo."""
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
    """Registro de modificação de arquivo."""
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
    Memória de conversa com estrutura eficiente.
    
    Mantém histórico de arquivos criados/modificados e decisões
    arquiteturais para referência em mensagens futuras.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Inicializa memória de conversa.
        
        Args:
            max_size: Tamanho máximo de registros (usa deque com maxlen)
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
        Registra criação de arquivo.
        
        Args:
            path: Path do arquivo criado
            content: Conteúdo do arquivo
            dependencies: Lista de dependências
            metadata: Metadados opcionais
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
        Registra modificação de arquivo.
        
        Args:
            path: Path do arquivo modificado
            modification_type: Tipo de modificação
            preview: Preview das mudanças
            metadata: Metadados opcionais
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
        Registra decisão arquitetural.
        
        Args:
            decision: Descrição da decisão
            context: Contexto adicional
        """
        self.architectural_decisions.append({
            'decision': decision,
            'context': context or {},
            'timestamp': datetime.now()
        })
    
    def get_file_record(self, path: str) -> Optional[FileCreationRecord]:
        """Retorna registro de arquivo se existir."""
        return self.file_index.get(path)
    
    def get_context_summary(self) -> str:
        """
        Retorna resumo eficiente do contexto da conversa.
        
        Returns:
            String formatada com resumo
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
        """Retorna lista de arquivos criados recentemente."""
        return [record.path for record in list(self.created_files)[-limit:]]
    
    def clear(self):
        """Limpa toda a memória."""
        self.created_files.clear()
        self.modified_files.clear()
        self.file_index.clear()
        self.architectural_decisions.clear()
        self.conversation_summary = ""

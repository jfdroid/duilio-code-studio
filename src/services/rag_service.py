"""
RAG Service (Retrieval Augmented Generation)
=============================================
Semantic search using embeddings for intelligent code retrieval.
Uses local embeddings for privacy and offline operation.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import math


@dataclass
class Document:
    """A document for the RAG index."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)
    chunk_index: int = 0


@dataclass
class SearchResult:
    """A search result with relevance score."""
    document: Document
    score: float
    highlights: List[str] = field(default_factory=list)


class SimpleEmbedding:
    """
    Simple TF-IDF based embedding for offline use.
    No external dependencies required.
    
    For production, consider using:
    - sentence-transformers
    - OpenAI embeddings
    - Ollama embeddings (ollama.embeddings)
    """
    
    def __init__(self, dim: int = 384):
        """Initialize simple embedding model."""
        self.dim = dim
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_count = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
        return tokens
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency."""
        tf = {}
        total = len(tokens)
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        for token in tf:
            tf[token] = tf[token] / total if total > 0 else 0
        return tf
    
    def fit(self, documents: List[str]) -> None:
        """Fit the model on documents to compute IDF."""
        self.doc_count = len(documents)
        doc_freq: Dict[str, int] = {}
        
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
                if token not in self.vocabulary:
                    self.vocabulary[token] = len(self.vocabulary)
        
        for token, freq in doc_freq.items():
            self.idf[token] = math.log((self.doc_count + 1) / (freq + 1)) + 1
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        tokens = self._tokenize(text)
        tf = self._compute_tf(tokens)
        
        tfidf = {}
        for token, freq in tf.items():
            idf = self.idf.get(token, 1.0)
            tfidf[token] = freq * idf
        
        embedding = [0.0] * self.dim
        for token, value in tfidf.items():
            idx = hash(token) % self.dim
            embedding[idx] += value
        
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(x * x for x in vec1))
        norm2 = math.sqrt(sum(x * x for x in vec2))
        
        if norm1 * norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class RAGService:
    """
    Retrieval Augmented Generation service.
    
    Features:
    - Index codebase files
    - Semantic search
    - Context retrieval for AI
    - Incremental updates
    - Persistent storage
    """
    
    # File extensions to index
    INDEXABLE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.kt', '.go', '.rs', '.rb',
        '.c', '.cpp', '.h', '.hpp', '.cs',
        '.vue', '.svelte', '.php', '.swift',
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.html', '.css', '.scss', '.sql'
    }
    
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100
    
    def __init__(self, workspace_path: Optional[str] = None, index_path: Optional[str] = None, ollama_service=None):
        """
        Initialize RAG service.
        
        Args:
            workspace_path: Path to the codebase
            index_path: Path to store the index
            ollama_service: Optional Ollama service for AI-powered features
        """
        self.workspace_path = workspace_path
        self.index_path = index_path or (
            Path.home() / ".duilio" / "rag_index"
        )
        
        from services.file_intelligence import get_file_intelligence
        self.file_intelligence = get_file_intelligence(ollama_service)
        
        self.embedding_model = SimpleEmbedding()
        self.documents: Dict[str, Document] = {}
        self.file_hashes: Dict[str, str] = {}
        self._initialized = False
    
    def _compute_file_hash(self, content: str) -> str:
        """Compute hash of file content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _chunk_text(self, text: str, file_path: str) -> List[Document]:
        """Split text into overlapping chunks."""
        chunks = []
        
        lines = text.split('\n')
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for line in lines:
            current_chunk.append(line)
            current_length += len(line) + 1
            
            if current_length >= self.CHUNK_SIZE:
                chunk_text = '\n'.join(current_chunk)
                doc_id = f"{file_path}:{chunk_index}"
                
                chunks.append(Document(
                    id=doc_id,
                    content=chunk_text,
                    metadata={
                        'file_path': file_path,
                        'chunk_index': chunk_index,
                        'language': Path(file_path).suffix[1:] if Path(file_path).suffix else 'unknown'
                    },
                    chunk_index=chunk_index
                ))
                
                overlap_lines = []
                overlap_length = 0
                for l in reversed(current_chunk):
                    overlap_lines.insert(0, l)
                    overlap_length += len(l) + 1
                    if overlap_length >= self.CHUNK_OVERLAP:
                        break
                
                current_chunk = overlap_lines
                current_length = overlap_length
                chunk_index += 1
        
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if chunk_text.strip():
                doc_id = f"{file_path}:{chunk_index}"
                chunks.append(Document(
                    id=doc_id,
                    content=chunk_text,
                    metadata={
                        'file_path': file_path,
                        'chunk_index': chunk_index,
                        'language': Path(file_path).suffix[1:] if Path(file_path).suffix else 'unknown'
                    },
                    chunk_index=chunk_index
                ))
        
        return chunks
    
    def _get_files(self, path: str) -> List[Path]:
        """Get all indexable files in path."""
        root = Path(path)
        files = []
        
        def scan(dir_path: Path):
            try:
                for item in dir_path.iterdir():
                    if self.file_intelligence.should_skip_directory(item.name):
                        continue
                    if item.is_dir():
                        scan(item)
                    elif item.is_file() and item.suffix in self.INDEXABLE_EXTENSIONS:
                        files.append(item)
            except PermissionError:
                pass
        
        scan(root)
        return files
    
    def index_codebase(
        self,
        path: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Index a codebase for semantic search.
        
        Args:
            path: Path to index (uses workspace_path if not provided)
            force: Force re-index even if unchanged
            
        Returns:
            Indexing statistics
        """
        index_path = path or self.workspace_path
        if not index_path:
            return {"error": "No path specified"}
        
        files = self._get_files(index_path)
        stats = {
            "total_files": len(files),
            "indexed_files": 0,
            "skipped_files": 0,
            "total_chunks": 0,
            "new_chunks": 0
        }
        
        all_texts = []
        new_documents = []
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                file_hash = self._compute_file_hash(content)
                
                rel_path = str(file_path.relative_to(index_path))
                if not force and self.file_hashes.get(rel_path) == file_hash:
                    stats["skipped_files"] += 1
                    continue
                
                chunks = self._chunk_text(content, rel_path)
                
                for chunk in chunks:
                    all_texts.append(chunk.content)
                    new_documents.append(chunk)
                
                self.file_hashes[rel_path] = file_hash
                stats["indexed_files"] += 1
                stats["new_chunks"] += len(chunks)
                
            except Exception as e:
                stats["skipped_files"] += 1
                continue
        
        stats["total_chunks"] = len(new_documents)
        
        if all_texts:
            self.embedding_model.fit(all_texts)
            
            for doc in new_documents:
                doc.embedding = self.embedding_model.embed(doc.content)
                self.documents[doc.id] = doc
        
        self._initialized = True
        return stats
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        file_filter: Optional[str] = None,
        min_score: float = 0.1
    ) -> List[SearchResult]:
        """
        Search the indexed codebase.
        
        Args:
            query: Search query
            top_k: Number of results to return
            file_filter: Optional file extension filter (e.g., ".py")
            min_score: Minimum similarity score
            
        Returns:
            List of search results with scores
        """
        if not self._initialized or not self.documents:
            return []
        
        query_embedding = self.embedding_model.embed(query)
        
        results = []
        for doc in self.documents.values():
            if file_filter:
                file_path = doc.metadata.get('file_path', '')
                if not file_path.endswith(file_filter):
                    continue
            
            score = self.embedding_model.similarity(query_embedding, doc.embedding)
            
            if score >= min_score:
                query_terms = set(query.lower().split())
                highlights = []
                for line in doc.content.split('\n'):
                    line_lower = line.lower()
                    if any(term in line_lower for term in query_terms):
                        highlights.append(line.strip())
                
                results.append(SearchResult(
                    document=doc,
                    score=score,
                    highlights=highlights[:3]
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 4000,
        include_metadata: bool = True
    ) -> str:
        """
        Get relevant context for an AI query.
        
        Args:
            query: User query
            max_tokens: Maximum context length
            include_metadata: Include file paths and metadata
            
        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=10)
        
        context_parts = []
        total_length = 0
        
        for result in results:
            doc = result.document
            
            if include_metadata:
                header = f"\n--- {doc.metadata.get('file_path', 'unknown')} (score: {result.score:.2f}) ---\n"
            else:
                header = "\n---\n"
            
            chunk = header + doc.content + "\n"
            chunk_length = len(chunk)
            
            if total_length + chunk_length > max_tokens * 4:
                break
            
            context_parts.append(chunk)
            total_length += chunk_length
        
        if not context_parts:
            return ""
        
        return "".join(context_parts)
    
    def update_file(self, file_path: str) -> bool:
        """
        Update index for a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if updated successfully
        """
        try:
            path = Path(file_path)
            if not path.exists():
                for doc_id in list(self.documents.keys()):
                    if doc_id.startswith(file_path):
                        del self.documents[doc_id]
                return True
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            for doc_id in list(self.documents.keys()):
                if doc_id.startswith(file_path):
                    del self.documents[doc_id]
            
            chunks = self._chunk_text(content, file_path)
            for chunk in chunks:
                chunk.embedding = self.embedding_model.embed(chunk.content)
                self.documents[chunk.id] = chunk
            
            return True
        except Exception:
            return False
    
    def save_index(self) -> bool:
        """Save index to disk."""
        try:
            index_dir = Path(self.index_path)
            index_dir.mkdir(parents=True, exist_ok=True)
            
            docs_data = []
            for doc in self.documents.values():
                docs_data.append({
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'embedding': doc.embedding,
                    'chunk_index': doc.chunk_index
                })
            
            with open(index_dir / 'documents.json', 'w') as f:
                json.dump(docs_data, f)
            
            with open(index_dir / 'file_hashes.json', 'w') as f:
                json.dump(self.file_hashes, f)
            
            with open(index_dir / 'vocabulary.json', 'w') as f:
                json.dump({
                    'vocabulary': self.embedding_model.vocabulary,
                    'idf': self.embedding_model.idf,
                    'doc_count': self.embedding_model.doc_count
                }, f)
            
            return True
        except Exception:
            return False
    
    def load_index(self) -> bool:
        """Load index from disk."""
        try:
            index_dir = Path(self.index_path)
            
            docs_path = index_dir / 'documents.json'
            if docs_path.exists():
                with open(docs_path) as f:
                    docs_data = json.load(f)
                    for data in docs_data:
                        doc = Document(
                            id=data['id'],
                            content=data['content'],
                            metadata=data['metadata'],
                            embedding=data['embedding'],
                            chunk_index=data['chunk_index']
                        )
                        self.documents[doc.id] = doc
            
            hashes_path = index_dir / 'file_hashes.json'
            if hashes_path.exists():
                with open(hashes_path) as f:
                    self.file_hashes = json.load(f)
            
            vocab_path = index_dir / 'vocabulary.json'
            if vocab_path.exists():
                with open(vocab_path) as f:
                    data = json.load(f)
                    self.embedding_model.vocabulary = data['vocabulary']
                    self.embedding_model.idf = data['idf']
                    self.embedding_model.doc_count = data['doc_count']
            
            self._initialized = len(self.documents) > 0
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "initialized": self._initialized,
            "total_documents": len(self.documents),
            "total_files": len(self.file_hashes),
            "vocabulary_size": len(self.embedding_model.vocabulary),
            "workspace_path": self.workspace_path
        }


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service(workspace_path: Optional[str] = None) -> RAGService:
    """Get RAG service instance."""
    global _rag_service
    if _rag_service is None or workspace_path != _rag_service.workspace_path:
        _rag_service = RAGService(workspace_path)
    return _rag_service

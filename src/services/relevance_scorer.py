"""
Relevance Scorer Service
=========================
Relevance scoring system using multiple factors and cache.

BigO:
- File score: O(1) with cache
- Sort by relevance: O(n log n)
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from pathlib import Path
import re
from functools import lru_cache


class RelevanceScorer:
    """
    Relevance scoring system using multiple factors.
    
    Considers:
    - File name (exact match)
    - Directory similarity
    - Related dependencies
    - File priority
    - Modification recency
    """
    
    def __init__(self, cache_size: int = 10000, ollama_service=None):
        """
        Initialize scorer with cache.
        
        Args:
            cache_size: LRU cache size
            ollama_service: Optional Ollama service for AI-powered features
        """
        self.cache_size = cache_size
        self._file_metadata: Dict[str, Dict] = {}
        self._directory_similarity_cache: Dict[Tuple[str, str], float] = {}
        
        from services.file_intelligence import get_file_intelligence
        self.file_intelligence = get_file_intelligence(ollama_service)
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for comparison."""
        return query.lower().strip()
    
    def _is_priority_file(self, file_path: str) -> bool:
        """Check if file is priority using intelligent detection."""
        is_priority, _ = self.file_intelligence.is_priority_file(file_path)
        return is_priority
    
    def _matches_important_pattern(self, file_path: str) -> bool:
        """Check if file matches important patterns using intelligent detection."""
        is_config, _ = self.file_intelligence.is_config_file(file_path)
        return is_config
    
    def _calculate_name_similarity(self, file_path: str, query: str) -> float:
        """
        Calculate similarity based on file name.
        
        Returns:
            Score from 0.0 to 1.0
        """
        filename = Path(file_path).name.lower()
        query_lower = self._normalize_query(query)
        
        if not query_lower:
            return 0.5  # Neutral score for empty query
        
        # Exact match
        if query_lower == filename:
            return 1.0
        
        # Contains
        if query_lower in filename:
            return 0.8
        
        # Starts with
        if filename.startswith(query_lower):
            return 0.7
        
        # Ends with
        if filename.endswith(query_lower):
            return 0.6
        
        # Word match
        query_words = set(query_lower.split())
        filename_words = set(filename.replace('.', ' ').replace('_', ' ').split())
        if query_words.intersection(filename_words):
            return 0.5
        
        # Levenshtein-like (simplified)
        # Count common characters
        common_chars = set(query_lower) & set(filename)
        if common_chars:
            similarity = len(common_chars) / max(len(query_lower), len(filename))
            return similarity * 0.3
        
        return 0.0
    
    def _calculate_directory_similarity(
        self, 
        file_path: str, 
        query: str,
        directory_tree = None
    ) -> float:
        """
        Calculate similarity based on directory.
        
        Returns:
            Score from 0.0 to 1.0
        """
        if not directory_tree:
            return 0.0
        
        file_dir = str(Path(file_path).parent)
        query_lower = self._normalize_query(query)
        
        query_parts = query_lower.split()
        dir_parts = file_dir.split('/')
        
        common_parts = set(query_parts) & set(dir_parts)
        if common_parts:
            return len(common_parts) / max(len(query_parts), len(dir_parts)) * 0.5
        
        return 0.0
    
    def _calculate_dependency_similarity(
        self,
        file_path: str,
        query: str,
        dependency_graph = None
    ) -> float:
        """
        Calculate similarity based on dependencies.
        
        Returns:
            Score from 0.0 to 1.0
        """
        if not dependency_graph:
            return 0.0
        
        query_lower = self._normalize_query(query)
        
        try:
            deps = dependency_graph.get_dependencies(file_path, direct_only=True)
            dependents = dependency_graph.get_dependents(file_path, direct_only=True)
            
            all_related = deps + dependents
            
            for related in all_related:
                related_name = Path(related).name.lower()
                if query_lower in related_name or related_name in query_lower:
                    return 0.4
            
        except Exception:
            pass
        
        return 0.0
    
    @lru_cache(maxsize=10000)
    def score_file(
        self,
        file_path: str,
        query: str = "",
        dependency_graph = None,
        directory_tree = None
    ) -> float:
        """
        Calculate relevance score of file for query.
        
        Args:
            file_path: File path
            query: Search query
            dependency_graph: Dependency graph (optional)
            directory_tree: Directory tree (optional)
        
        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0
        query_lower = self._normalize_query(query)
        
        # 1. File name (40% weight)
        name_score = self._calculate_name_similarity(file_path, query)
        score += name_score * 0.4
        
        # 2. Directory similarity (30% weight)
        dir_score = self._calculate_directory_similarity(file_path, query, directory_tree)
        score += dir_score * 0.3
        
        # 3. Related dependencies (20% weight)
        dep_score = self._calculate_dependency_similarity(file_path, query, dependency_graph)
        score += dep_score * 0.2
        
        if self._is_priority_file(file_path):
            score += 0.1
        elif self._matches_important_pattern(file_path):
            score += 0.05
        
        return min(1.0, score)
    
    def rank_files(
        self,
        files: List[str],
        query: str = "",
        dependency_graph = None,
        directory_tree = None,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Rank files by relevance.
        
        Args:
            files: List of file paths
            query: Search query
            dependency_graph: Dependency graph (optional)
            directory_tree: Directory tree (optional)
            limit: Maximum number of results
        
        Returns:
            List of tuples (file_path, score) sorted by score
        """
        scored = [
            (
                f,
                self.score_file(f, query, dependency_graph, directory_tree)
            )
            for f in files
        ]
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:limit]
    
    def get_top_files(
        self,
        files: List[str],
        query: str = "",
        dependency_graph = None,
        directory_tree = None,
        limit: int = 10,
        min_score: float = 0.1
    ) -> List[str]:
        """
        Return top N files above minimum score.
        
        Args:
            files: List of paths
            query: Search query
            dependency_graph: Dependency graph (optional)
            directory_tree: Directory tree (optional)
            limit: Maximum number
            min_score: Minimum score
        
        Returns:
            List of paths
        """
        ranked = self.rank_files(files, query, dependency_graph, directory_tree, limit * 2)
        return [f for f, score in ranked if score >= min_score][:limit]
    
    def clear_cache(self):
        """Clear scorer cache."""
        self.score_file.cache_clear()
        self._directory_similarity_cache.clear()

"""
Relevance Scorer Service
=========================
Sistema de scoring de relevância usando múltiplos fatores e cache.

BigO:
- Score de arquivo: O(1) com cache
- Ordenar por relevância: O(n log n)
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from pathlib import Path
import re
from functools import lru_cache


class RelevanceScorer:
    """
    Sistema de scoring de relevância usando múltiplos fatores.
    
    Considera:
    - Nome do arquivo (exact match)
    - Similaridade de diretório
    - Dependências relacionadas
    - Prioridade do arquivo
    - Recência de modificação
    """
    
    # Arquivos prioritários (sempre alta relevância)
    PRIORITY_FILES = {
        'main.py', 'app.py', 'index.py', '__init__.py',
        'main.js', 'index.js', 'app.js', 'main.ts', 'index.ts',
        'package.json', 'requirements.txt', 'pyproject.toml',
        'README.md', 'readme.md'
    }
    
    # Padrões de arquivos importantes
    IMPORTANT_PATTERNS = [
        r'.*config.*',
        r'.*setup.*',
        r'.*init.*',
        r'.*main.*',
        r'.*app.*',
        r'.*index.*'
    ]
    
    def __init__(self, cache_size: int = 10000):
        """
        Inicializa scorer com cache.
        
        Args:
            cache_size: Tamanho do cache LRU
        """
        self.cache_size = cache_size
        self._file_metadata: Dict[str, Dict] = {}
        self._directory_similarity_cache: Dict[Tuple[str, str], float] = {}
    
    def _normalize_query(self, query: str) -> str:
        """Normaliza query para comparação."""
        return query.lower().strip()
    
    def _is_priority_file(self, file_path: str) -> bool:
        """Verifica se arquivo é prioritário."""
        filename = Path(file_path).name.lower()
        return filename in self.PRIORITY_FILES
    
    def _matches_important_pattern(self, file_path: str) -> bool:
        """Verifica se arquivo corresponde a padrões importantes."""
        filename = Path(file_path).name.lower()
        return any(re.match(pattern, filename) for pattern in self.IMPORTANT_PATTERNS)
    
    def _calculate_name_similarity(self, file_path: str, query: str) -> float:
        """
        Calcula similaridade baseada no nome do arquivo.
        
        Returns:
            Score de 0.0 a 1.0
        """
        filename = Path(file_path).name.lower()
        query_lower = self._normalize_query(query)
        
        if not query_lower:
            return 0.5  # Score neutro para query vazia
        
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
        
        # Levenshtein-like (simplificado)
        # Contar caracteres em comum
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
        Calcula similaridade baseada no diretório.
        
        Returns:
            Score de 0.0 a 1.0
        """
        if not directory_tree:
            return 0.0
        
        file_dir = str(Path(file_path).parent)
        query_lower = self._normalize_query(query)
        
        # Verificar se query menciona diretório
        query_parts = query_lower.split()
        dir_parts = file_dir.split('/')
        
        # Contar partes em comum
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
        Calcula similaridade baseada em dependências.
        
        Returns:
            Score de 0.0 a 1.0
        """
        if not dependency_graph:
            return 0.0
        
        query_lower = self._normalize_query(query)
        
        # Buscar dependências
        try:
            deps = dependency_graph.get_dependencies(file_path, direct_only=True)
            dependents = dependency_graph.get_dependents(file_path, direct_only=True)
            
            all_related = deps + dependents
            
            # Verificar se query menciona arquivos relacionados
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
        Calcula score de relevância de arquivo para query.
        
        Args:
            file_path: Path do arquivo
            query: Query de busca
            dependency_graph: Grafo de dependências (opcional)
            directory_tree: Árvore de diretórios (opcional)
        
        Returns:
            Score de 0.0 a 1.0
        """
        score = 0.0
        query_lower = self._normalize_query(query)
        
        # 1. Nome do arquivo (40% do peso)
        name_score = self._calculate_name_similarity(file_path, query)
        score += name_score * 0.4
        
        # 2. Similaridade de diretório (30% do peso)
        dir_score = self._calculate_directory_similarity(file_path, query, directory_tree)
        score += dir_score * 0.3
        
        # 3. Dependências relacionadas (20% do peso)
        dep_score = self._calculate_dependency_similarity(file_path, query, dependency_graph)
        score += dep_score * 0.2
        
        # 4. Prioridade do arquivo (10% do peso)
        if self._is_priority_file(file_path):
            score += 0.1
        elif self._matches_important_pattern(file_path):
            score += 0.05
        
        # Normalizar para 0.0-1.0
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
        Ordena arquivos por relevância.
        
        Args:
            files: Lista de paths de arquivos
            query: Query de busca
            dependency_graph: Grafo de dependências (opcional)
            directory_tree: Árvore de diretórios (opcional)
            limit: Número máximo de resultados
        
        Returns:
            Lista de tuplas (file_path, score) ordenada por score
        """
        scored = [
            (
                f,
                self.score_file(f, query, dependency_graph, directory_tree)
            )
            for f in files
        ]
        
        # Ordenar por score (decrescente)
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
        Retorna top N arquivos acima do score mínimo.
        
        Args:
            files: Lista de paths
            query: Query de busca
            dependency_graph: Grafo de dependências (opcional)
            directory_tree: Árvore de diretórios (opcional)
            limit: Número máximo
            min_score: Score mínimo
        
        Returns:
            Lista de paths
        """
        ranked = self.rank_files(files, query, dependency_graph, directory_tree, limit * 2)
        return [f for f, score in ranked if score >= min_score][:limit]
    
    def clear_cache(self):
        """Limpa cache do scorer."""
        self.score_file.cache_clear()
        self._directory_similarity_cache.clear()

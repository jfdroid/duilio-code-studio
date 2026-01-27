"""
File Dependency Graph Service
=============================
Grafo direcionado de dependências entre arquivos usando estruturas eficientes.

BigO:
- Adicionar nó: O(1)
- Adicionar aresta: O(1)
- Buscar dependências: O(V + E) com DFS
- Topological sort: O(V + E)
"""

from typing import Dict, Set, List, Optional
from collections import defaultdict
from pathlib import Path
import re


class FileDependencyGraph:
    """
    Grafo direcionado de dependências entre arquivos.
    
    Representa relações de import/dependência entre arquivos do codebase.
    Permite encontrar dependências diretas e indiretas, e ordenar arquivos
    por dependências (topological sort).
    """
    
    def __init__(self):
        # Grafo: node -> set of dependencies
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        # Reverse graph: dependency -> set of dependents
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        # Index: file_path -> normalized_path
        self.file_index: Dict[str, str] = {}
        # Reverse index: normalized_path -> set of file_paths
        self.reverse_index: Dict[str, Set[str]] = defaultdict(set)
        # Metadata: normalized_path -> metadata
        self.metadata: Dict[str, Dict] = {}
    
    def _normalize_path(self, file_path: str) -> str:
        """Normaliza path para uso no grafo."""
        return str(Path(file_path).resolve())
    
    def _resolve_import(self, import_path: str, from_file: str) -> Optional[str]:
        """
        Resolve import path para arquivo real.
        
        Tenta diferentes estratégias:
        1. Import relativo
        2. Import absoluto do projeto
        3. Import de node_modules/packages
        """
        from_path = Path(from_file).parent
        
        # Tentar import relativo
        if import_path.startswith('.'):
            # Relative import
            parts = import_path.split('.')
            if parts[0] == '':
                parts = parts[1:]
            
            resolved = from_path
            for part in parts:
                if part:
                    resolved = resolved / part
            
            # Tentar diferentes extensões
            for ext in ['', '.py', '.js', '.ts', '.jsx', '.tsx']:
                candidate = resolved.with_suffix(ext)
                if candidate.exists():
                    return self._normalize_path(str(candidate))
            
            # Tentar como diretório com __init__
            for ext in ['.py', '.js', '.ts']:
                candidate = resolved / f"__init__{ext}"
                if candidate.exists():
                    return self._normalize_path(str(candidate))
        
        # Tentar import absoluto (assumindo estrutura de projeto)
        # Isso é simplificado - em produção, usar análise de paths do projeto
        return None
    
    def add_file(self, file_path: str, imports: List[str], metadata: Dict = None):
        """
        Adiciona arquivo e suas dependências ao grafo.
        
        Args:
            file_path: Path do arquivo
            imports: Lista de imports/dependências
            metadata: Metadados opcionais do arquivo
        """
        normalized = self._normalize_path(file_path)
        self.graph[normalized]  # Garantir que nó existe
        self.file_index[file_path] = normalized
        self.reverse_index[normalized].add(file_path)
        
        if metadata:
            self.metadata[normalized] = metadata
        
        # Adicionar arestas de dependência
        for imp in imports:
            dep_normalized = self._resolve_import(imp, file_path)
            if dep_normalized and dep_normalized != normalized:
                self.graph[normalized].add(dep_normalized)
                self.reverse_graph[dep_normalized].add(normalized)
    
    def get_dependencies(self, file_path: str, direct_only: bool = False) -> List[str]:
        """
        Retorna todas as dependências diretas e indiretas.
        
        Args:
            file_path: Path do arquivo
            direct_only: Se True, retorna apenas dependências diretas
        
        Returns:
            Lista de paths normalizados de dependências
        """
        normalized = self.file_index.get(file_path)
        if not normalized or normalized not in self.graph:
            return []
        
        if direct_only:
            return list(self.graph[normalized])
        
        # DFS para encontrar todas as dependências (transitivas)
        dependencies = []
        visited = set()
        
        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for neighbor in self.graph[node]:
                if neighbor not in dependencies:
                    dependencies.append(neighbor)
                dfs(neighbor)
        
        dfs(normalized)
        return dependencies
    
    def get_dependents(self, file_path: str, direct_only: bool = False) -> List[str]:
        """
        Retorna todos os arquivos que dependem deste.
        
        Args:
            file_path: Path do arquivo
            direct_only: Se True, retorna apenas dependentes diretos
        
        Returns:
            Lista de paths normalizados de dependentes
        """
        normalized = self.file_index.get(file_path)
        if not normalized or normalized not in self.reverse_graph:
            return []
        
        if direct_only:
            return list(self.reverse_graph[normalized])
        
        # DFS no grafo reverso
        dependents = []
        visited = set()
        
        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for neighbor in self.reverse_graph[node]:
                if neighbor not in dependents:
                    dependents.append(neighbor)
                dfs(neighbor)
        
        dfs(normalized)
        return dependents
    
    def topological_sort(self) -> List[str]:
        """
        Retorna ordem topológica para criação de arquivos.
        
        Garante que dependências são criadas antes dos arquivos que as usam.
        
        Returns:
            Lista de paths normalizados em ordem topológica
        """
        # Kahn's algorithm para topological sort
        in_degree = defaultdict(int)
        
        # Calcular graus de entrada
        for node in self.graph:
            in_degree[node] = 0
        
        for node in self.graph:
            for neighbor in self.graph[node]:
                in_degree[neighbor] += 1
        
        # Fila de nós com grau 0
        queue = [node for node in self.graph if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Reduzir grau dos vizinhos
            for neighbor in self.graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Se há ciclo, adicionar nós restantes
        remaining = [node for node in self.graph if node not in result]
        result.extend(remaining)
        
        return result
    
    def has_cycle(self) -> bool:
        """Verifica se o grafo tem ciclos."""
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.graph:
            if node not in visited:
                if has_cycle_dfs(node):
                    return True
        
        return False
    
    def get_connected_components(self) -> List[List[str]]:
        """
        Retorna componentes conectados do grafo (não direcionado).
        
        Útil para identificar grupos de arquivos relacionados.
        """
        visited = set()
        components = []
        
        def dfs(node, component):
            visited.add(node)
            component.append(node)
            # Visitar dependências e dependentes
            for neighbor in list(self.graph[node]) + list(self.reverse_graph[node]):
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        for node in self.graph:
            if node not in visited:
                component = []
                dfs(node, component)
                if component:
                    components.append(component)
        
        return components
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do grafo."""
        total_nodes = len(self.graph)
        total_edges = sum(len(deps) for deps in self.graph.values())
        
        in_degrees = defaultdict(int)
        out_degrees = defaultdict(int)
        
        for node in self.graph:
            out_degrees[node] = len(self.graph[node])
            for neighbor in self.graph[node]:
                in_degrees[neighbor] += 1
        
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'avg_out_degree': total_edges / total_nodes if total_nodes > 0 else 0,
            'max_out_degree': max(out_degrees.values()) if out_degrees else 0,
            'max_in_degree': max(in_degrees.values()) if in_degrees else 0,
            'has_cycles': self.has_cycle(),
            'connected_components': len(self.get_connected_components())
        }

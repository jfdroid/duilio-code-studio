"""
Directory Tree Service (Trie Structure)
=======================================
Árvore Trie para estrutura de diretórios eficiente.

BigO:
- Inserir: O(m) onde m é profundidade do path
- Buscar: O(m)
- Listar subdiretórios: O(k) onde k é número de filhos
"""

from typing import Dict, Optional, List, Set
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DirectoryNode:
    """Nó da árvore de diretórios (Trie)."""
    name: str
    path: str
    children: Dict[str, 'DirectoryNode'] = field(default_factory=dict)
    files: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.children:
            self.children = {}
        if not isinstance(self.files, set):
            self.files = set(self.files) if self.files else set()


class DirectoryTree:
    """
    Árvore Trie para estrutura de diretórios.
    
    Permite inserção e busca eficiente de paths, mantendo estrutura
    hierárquica do filesystem.
    """
    
    def __init__(self, root_path: str):
        """
        Inicializa árvore com root path.
        
        Args:
            root_path: Path raiz do workspace
        """
        self.root_path = Path(root_path).resolve()
        self.root = DirectoryNode("", str(self.root_path))
        self._path_cache: Dict[str, DirectoryNode] = {}  # Cache de paths
    
    def add_path(self, file_path: str, metadata: Dict = None):
        """
        Adiciona path à árvore.
        
        Args:
            file_path: Path completo do arquivo
            metadata: Metadados opcionais
        """
        # Normalizar path
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            try:
                relative = path_obj.relative_to(self.root_path)
            except ValueError:
                # Path fora do root, usar como está
                parts = path_obj.parts
            else:
                parts = relative.parts
        else:
            parts = path_obj.parts
        
        if not parts:
            return
        
        current = self.root
        
        # Navegar/criar diretórios
        for part in parts[:-1]:  # Todos exceto o arquivo
            if part not in current.children:
                new_path = str(Path(current.path) / part) if current.path else part
                current.children[part] = DirectoryNode(part, new_path)
                self._path_cache[new_path] = current.children[part]
            current = current.children[part]
        
        # Adicionar arquivo
        filename = parts[-1]
        current.files.add(filename)
        
        if metadata:
            current.metadata[filename] = metadata
    
    def find_directory(self, dir_path: str) -> Optional[DirectoryNode]:
        """
        Encontra nó de diretório.
        
        Args:
            dir_path: Path do diretório
        
        Returns:
            DirectoryNode ou None se não encontrado
        """
        # Verificar cache primeiro
        if dir_path in self._path_cache:
            return self._path_cache[dir_path]
        
        # Normalizar path
        path_obj = Path(dir_path)
        if path_obj.is_absolute():
            try:
                relative = path_obj.relative_to(self.root_path)
            except ValueError:
                return None
            parts = relative.parts
        else:
            parts = path_obj.parts
        
        if not parts:
            return self.root
        
        current = self.root
        
        for part in parts:
            if part not in current.children:
                return None
            current = current.children[part]
        
        return current
    
    def get_all_paths(self, include_files: bool = True) -> List[str]:
        """
        Retorna todos os paths na árvore.
        
        Args:
            include_files: Se True, inclui arquivos; se False, apenas diretórios
        
        Returns:
            Lista de paths
        """
        paths = []
        
        def traverse(node: DirectoryNode, current_path: str):
            # Adicionar arquivos
            if include_files:
                for filename in node.files:
                    if current_path:
                        paths.append(f"{current_path}/{filename}")
                    else:
                        paths.append(filename)
            
            # Adicionar diretórios e recursão
            for name, child in node.children.items():
                new_path = f"{current_path}/{name}" if current_path else name
                paths.append(new_path + "/")
                traverse(child, new_path)
        
        traverse(self.root, "")
        return paths
    
    def get_files_in_directory(self, dir_path: str) -> List[str]:
        """
        Retorna lista de arquivos em diretório.
        
        Args:
            dir_path: Path do diretório
        
        Returns:
            Lista de nomes de arquivos
        """
        node = self.find_directory(dir_path)
        if not node:
            return []
        
        return sorted(list(node.files))
    
    def get_subdirectories(self, dir_path: str) -> List[str]:
        """
        Retorna lista de subdiretórios.
        
        Args:
            dir_path: Path do diretório
        
        Returns:
            Lista de nomes de subdiretórios
        """
        node = self.find_directory(dir_path)
        if not node:
            return []
        
        return sorted(list(node.children.keys()))
    
    def get_directory_structure(self, dir_path: str = "", max_depth: int = 3) -> Dict:
        """
        Retorna estrutura de diretório como dict.
        
        Args:
            dir_path: Path do diretório (vazio = root)
            max_depth: Profundidade máxima
        
        Returns:
            Dict com estrutura
        """
        node = self.find_directory(dir_path) if dir_path else self.root
        if not node:
            return {}
        
        def build_structure(n: DirectoryNode, depth: int = 0) -> Dict:
            if depth > max_depth:
                return {}
            
            structure = {
                'path': n.path,
                'files': sorted(list(n.files)),
                'directories': {}
            }
            
            for name, child in n.children.items():
                structure['directories'][name] = build_structure(child, depth + 1)
            
            return structure
        
        return build_structure(node)
    
    def find_files_by_pattern(self, pattern: str, dir_path: str = "") -> List[str]:
        """
        Encontra arquivos que correspondem ao padrão.
        
        Args:
            pattern: Padrão de busca (suporta * e ?)
            dir_path: Diretório base (vazio = root)
        
        Returns:
            Lista de paths de arquivos
        """
        import fnmatch
        
        node = self.find_directory(dir_path) if dir_path else self.root
        if not node:
            return []
        
        matches = []
        base_path = dir_path if dir_path else ""
        
        def search(n: DirectoryNode, current_path: str):
            # Buscar arquivos
            for filename in n.files:
                if fnmatch.fnmatch(filename, pattern):
                    if current_path:
                        matches.append(f"{current_path}/{filename}")
                    else:
                        matches.append(filename)
            
            # Buscar em subdiretórios
            for name, child in n.children.items():
                new_path = f"{current_path}/{name}" if current_path else name
                search(child, new_path)
        
        search(node, base_path)
        return matches
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas da árvore."""
        total_files = 0
        total_dirs = 0
        max_depth = 0
        
        def traverse(n: DirectoryNode, depth: int = 0):
            nonlocal total_files, total_dirs, max_depth
            
            max_depth = max(max_depth, depth)
            total_files += len(n.files)
            total_dirs += 1
            
            for child in n.children.values():
                traverse(child, depth + 1)
        
        traverse(self.root)
        
        return {
            'total_files': total_files,
            'total_directories': total_dirs,
            'max_depth': max_depth,
            'root_path': str(self.root_path)
        }

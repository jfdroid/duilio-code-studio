"""
Codebase Analyzer Service
=========================
Intelligent analysis of codebases for AI context.
Reads, analyzes, and summarizes code projects.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FileAnalysis:
    """Analysis of a single file."""
    path: str
    relative_path: str
    extension: str
    language: str
    size: int
    lines: int
    content: str = ""
    summary: str = ""
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


@dataclass
class CodebaseAnalysis:
    """Complete codebase analysis."""
    root_path: str
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    file_tree: str
    main_files: List[FileAnalysis]
    config_files: List[FileAnalysis]
    structure_summary: str
    entry_points: List[str]
    dependencies: Dict[str, List[str]]


class CodebaseAnalyzer:
    """
    Intelligent codebase analyzer for AI context generation.
    
    Features:
    - File tree generation
    - Language detection
    - Entry point detection
    - Import/dependency analysis
    - Code summarization
    - Smart file prioritization
    """
    
    MAX_FILE_SIZE = 500 * 1024
    MAX_FILE_SIZE = 500 * 1024
    MAX_CONTENT_PER_FILE = 5 * 1024
    
    def __init__(self, root_path: str, ollama_service=None):
        """
        Initialize analyzer with root path.
        
        Args:
            root_path: Root path of codebase
            ollama_service: Optional Ollama service for AI-powered detection
        """
        self.root_path = Path(root_path).resolve()
        self._files: List[FileAnalysis] = []
        self._tree_lines: List[str] = []
        
        from services.language_detector import get_language_detector
        self.language_detector = get_language_detector(ollama_service)
        
        from services.file_intelligence import get_file_intelligence
        self.file_intelligence = get_file_intelligence(ollama_service)
        
        try:
            from services.directory_tree import DirectoryTree
            from services.dependency_graph import FileDependencyGraph
            from services.relevance_scorer import RelevanceScorer
            
            self.directory_tree = DirectoryTree(str(self.root_path))
            self.dependency_graph = FileDependencyGraph()
            self.relevance_scorer = RelevanceScorer(ollama_service=ollama_service)
            self._use_optimized_structures = True
        except ImportError:
            self.directory_tree = None
            self.dependency_graph = None
            self.relevance_scorer = None
            self._use_optimized_structures = False
        
    def _should_skip_dir(self, name: str) -> bool:
        """Check if directory should be skipped using intelligent detection."""
        return self.file_intelligence.should_skip_directory(name)
    
    def _get_language(self, extension: str) -> str:
        """Get language from extension using generic detector."""
        lang_info = self.language_detector.detect_from_extension(extension)
        if lang_info:
            return lang_info.name
        return 'Unknown'
    
    def _is_binary(self, path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return True
        except:
            return True
        return False
    
    def _extract_file_info(self, content: str, language: str) -> Dict[str, List[str]]:
        """Extract file information generically using language detector."""
        # Use language detector's generic extraction methods
        structure = self.language_detector.extract_structure(content)
        imports = self.language_detector.extract_imports(content, language)
        
        return {
            'imports': imports,
            'classes': structure.get('classes', []),
            'functions': structure.get('functions', []),
            'exports': structure.get('exports', [])
        }
    
    def _generate_file_summary(self, analysis: FileAnalysis) -> str:
        """Generate a brief summary of the file."""
        parts = []
        
        if analysis.classes:
            parts.append(f"Classes: {', '.join(analysis.classes[:5])}")
        if analysis.functions:
            funcs = [f for f in analysis.functions[:10] if not f.startswith('_')]
            if funcs:
                parts.append(f"Functions: {', '.join(funcs)}")
        if analysis.imports:
            parts.append(f"Imports: {len(analysis.imports)} modules")
        
        return ' | '.join(parts) if parts else f"{analysis.lines} lines of {analysis.language}"
    
    def _build_tree(self, path: Path, prefix: str = "", depth: int = 0, max_depth: int = 4) -> None:
        """Build file tree recursively."""
        if depth > max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        
        dirs = [i for i in items if i.is_dir() and not self._should_skip_dir(i.name)]
        files = [i for i in items if i.is_file() and not i.name.startswith('.')]
        
        # Limit items to prevent huge trees
        if len(dirs) + len(files) > 50:
            dirs = dirs[:20]
            files = files[:30]
        
        all_items = dirs + files
        
        for i, item in enumerate(all_items):
            is_last = i == len(all_items) - 1
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                self._tree_lines.append(f"{prefix}{connector}{item.name}/")
                new_prefix = f"{prefix}{'    ' if is_last else '│   '}"
                self._build_tree(item, new_prefix, depth + 1, max_depth)
            else:
                ext = item.suffix.lower()
                lang = self._get_language(ext)
                marker = f" [{lang}]" if lang != 'Unknown' else ""
                self._tree_lines.append(f"{prefix}{connector}{item.name}{marker}")
    
    def _analyze_file(self, path: Path) -> Optional[FileAnalysis]:
        """Analyze a single file."""
        try:
            stat = path.stat()
            
            # Skip large files
            if stat.st_size > self.MAX_FILE_SIZE:
                return None
            
            # Skip binary files
            if self._is_binary(path):
                return None
            
            ext = path.suffix.lower()
            language = self._get_language(ext)
            
            # Read content
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
            except:
                return None
            
            lines = content.count('\n') + 1
            relative = str(path.relative_to(self.root_path))
            
            # Extract info
            info = self._extract_file_info(content, language)
            
            # Truncate content for context
            truncated_content = content[:self.MAX_CONTENT_PER_FILE]
            if len(content) > self.MAX_CONTENT_PER_FILE:
                truncated_content += "\n... [content truncated] ..."
            
            analysis = FileAnalysis(
                path=str(path),
                relative_path=relative,
                extension=ext,
                language=language,
                size=stat.st_size,
                lines=lines,
                content=truncated_content,
                imports=info['imports'],
                classes=info['classes'],
                functions=info['functions'],
                exports=info['exports'],
            )
            
            analysis.summary = self._generate_file_summary(analysis)
            
            return analysis
            
        except Exception as e:
            return None
    
    def _find_entry_points(self) -> List[str]:
        """Find likely entry points using intelligent detection."""
        entry_points = []
        
        for f in self._files:
            # Use FileIntelligence to detect entry points
            is_entry, confidence = self.file_intelligence.is_entry_point(f.path, f.content)
            if is_entry and confidence > 0.6:
                if f.relative_path not in entry_points:
                    entry_points.append(f.relative_path)
        
        return entry_points[:5]
    
    def _analyze_dependencies(self) -> Dict[str, List[str]]:
        """
        Analyze project dependencies using intelligent detection.
        
        Uses FileIntelligence to detect dependency files instead of hardcoded names.
        """
        deps = {}
        
        for f in self._files:
            classification = self.file_intelligence.classify_file(f.path, f.content)
            
            if classification.is_config:
                name = Path(f.path).name.lower()
                
                try:
                    content = Path(f.path).read_text(encoding='utf-8', errors='ignore')
                    
                    if name.endswith('.json'):
                        try:
                            import json
                            data = json.loads(content)
                            if 'dependencies' in data:
                                deps['npm'] = list(data.get('dependencies', {}).keys())[:20]
                            if 'devDependencies' in data:
                                deps['npm_dev'] = list(data.get('devDependencies', {}).keys())[:10]
                        except:
                            pass
                    
                    elif any(indicator in name for indicator in ['requirements', 'dependencies', 'packages']):
                        deps['pip'] = [
                            line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                            for line in content.splitlines()
                            if line.strip() and not line.startswith('#') and not line.startswith('-')
                        ][:20]
                    
                    elif name.endswith('.toml'):
                        deps['toml_project'] = re.findall(r'["\']([^"\']+)["\']', content)[:20]
                        
                except:
                    pass
        
        return deps
    
    def _generate_structure_summary(self, languages: Dict[str, int]) -> str:
        """Generate a summary of the codebase structure."""
        parts = []
        
        sorted_langs = sorted(languages.items(), key=lambda x: -x[1])
        lang_str = ", ".join([f"{lang}: {count} files" for lang, count in sorted_langs[:5]])
        parts.append(f"Languages: {lang_str}")
        
        dirs = set()
        for f in self._files:
            parts_list = f.relative_path.split('/')
            if len(parts_list) > 1:
                dirs.add(parts_list[0])
        
        if dirs:
            parts.append(f"Main directories: {', '.join(sorted(dirs)[:10])}")
        
        return " | ".join(parts)
    
    def analyze(self, max_files: int = 100, query: str = "", use_cache: bool = True) -> CodebaseAnalysis:
        """
        Analyze the codebase with optimized structures.
        
        Args:
            max_files: Maximum number of files to analyze in detail
            query: Optional query for relevance scoring
            use_cache: If True, use cache for analysis results
            
        Returns:
            CodebaseAnalysis with full project context
            
        BigO:
        - File collection: O(n) where n is total files
        - Tree building: O(n) with DirectoryTree (Trie)
        - Dependency graph: O(n * m) where m is avg imports per file
        - Relevance scoring: O(n log n) for ranking
        - With cache: O(1) for cached results
        """
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {self.root_path}")
        
        if use_cache:
            try:
                from services.cache_service import get_cache_service
                cache = get_cache_service()
                cache_key = cache._make_key(
                    "codebase_analysis",
                    str(self.root_path),
                    max_files,
                    query
                )
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            except Exception:
                pass
        
        all_files: List[Path] = []
        languages: Dict[str, int] = defaultdict(int)
        total_lines = 0
        
        def collect_files(path: Path, depth: int = 0):
            nonlocal total_lines
            if depth > 6:
                return
            
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        if not self._should_skip_dir(item.name):
                            collect_files(item, depth + 1)
                            if self._use_optimized_structures and self.directory_tree:
                                self.directory_tree.add_path(str(item))
                    elif item.is_file():
                        if not item.name.startswith('.'):
                            all_files.append(item)
                            ext = item.suffix.lower()
                            lang = self._get_language(ext)
                            if lang != 'Unknown':
                                languages[lang] += 1
                            if self._use_optimized_structures and self.directory_tree:
                                self.directory_tree.add_path(str(item))
            except:
                pass
        
        collect_files(self.root_path)
        
        if self._use_optimized_structures and self.directory_tree:
            all_paths = self.directory_tree.get_all_paths(include_files=True)
            file_tree = f"{self.root_path.name}/\n" + "\n".join(all_paths[:100])
        else:
            self._tree_lines = [f"{self.root_path.name}/"]
            self._build_tree(self.root_path)
            file_tree = "\n".join(self._tree_lines)
        
        priority_files = []
        other_files = []
        config_files = []
        
        for f in all_files:
            try:
                content = None
                try:
                    if f.stat().st_size < 10000:
                        content = f.read_text(encoding='utf-8', errors='ignore')[:500]
                except:
                    pass
                
                classification = self.file_intelligence.classify_file(str(f), content)
                
                if classification.is_priority:
                    priority_files.append(f)
                elif classification.is_config:
                    config_files.append(f)
                else:
                    other_files.append(f)
            except:
                other_files.append(f)
        
        if query and self._use_optimized_structures and self.relevance_scorer:
            all_file_paths = [str(f) for f in all_files]
            ranked = self.relevance_scorer.rank_files(
                all_file_paths,
                query=query,
                dependency_graph=self.dependency_graph,
                directory_tree=self.directory_tree,
                limit=max_files
            )
            ranked_paths = {path: score for path, score in ranked}
            other_files.sort(key=lambda f: ranked_paths.get(str(f), 0.0), reverse=True)
        
        files_to_analyze = priority_files + config_files + other_files[:max_files - len(priority_files) - len(config_files)]
        
        main_analyses = []
        config_analyses = []
        
        for f in files_to_analyze[:max_files]:
            analysis = self._analyze_file(f)
            if analysis:
                self._files.append(analysis)
                total_lines += analysis.lines
                
                if self._use_optimized_structures and self.dependency_graph:
                    self.dependency_graph.add_file(
                        file_path=str(f),
                        imports=analysis.imports,
                        metadata={
                            'language': analysis.language,
                            'lines': analysis.lines,
                            'classes': analysis.classes,
                            'functions': analysis.functions
                        }
                    )
                
                if f in priority_files:
                    main_analyses.append(analysis)
                elif f in config_files:
                    config_analyses.append(analysis)
        
        result = CodebaseAnalysis(
            root_path=str(self.root_path),
            total_files=len(all_files),
            total_lines=total_lines,
            languages=dict(languages),
            file_tree=file_tree,
            main_files=main_analyses[:20],
            config_files=config_analyses[:10],
            structure_summary=self._generate_structure_summary(languages),
            entry_points=self._find_entry_points(),
            dependencies=self._analyze_dependencies(),
        )
        
        if use_cache:
            try:
                from services.cache_service import get_cache_service
                cache = get_cache_service()
                cache_key = cache._make_key(
                    "codebase_analysis",
                    str(self.root_path),
                    max_files,
                    query
                )
                cache.set(cache_key, result, ttl=3600)
            except Exception:
                pass
        
        return result
    
    def get_context_for_ai(self, analysis: CodebaseAnalysis, max_length: int = 8000, query: str = "") -> str:
        """
        Generate AI context from analysis.
        
        Args:
            analysis: CodebaseAnalysis object
            max_length: Maximum context length
            
        Returns:
            Formatted context string for AI
        """
        parts = []
        
        parts.append(f"=== CODEBASE ANALYSIS: {Path(analysis.root_path).name} ===\n")
        
        parts.append(f"📁 Total Files: {analysis.total_files}")
        parts.append(f"📝 Total Lines: {analysis.total_lines}")
        parts.append(f"📊 {analysis.structure_summary}\n")
        
        if analysis.entry_points:
            parts.append(f"🚀 Entry Points: {', '.join(analysis.entry_points)}\n")
        
        if analysis.dependencies:
            for pkg_type, deps in analysis.dependencies.items():
                if deps:
                    parts.append(f"📦 {pkg_type}: {', '.join(deps[:10])}")
            parts.append("")
        
        tree_lines = analysis.file_tree.split('\n')[:50]
        parts.append("📂 FILE STRUCTURE:")
        parts.append("```")
        parts.append('\n'.join(tree_lines))
        if len(analysis.file_tree.split('\n')) > 50:
            parts.append("... (truncated)")
        parts.append("```\n")
        
        files_to_show = analysis.main_files + analysis.config_files
        
        if query and self._use_optimized_structures and self.relevance_scorer:
            file_paths = [f.path for f in files_to_show]
            ranked = self.relevance_scorer.rank_files(
                file_paths,
                query=query,
                dependency_graph=self.dependency_graph,
                directory_tree=self.directory_tree,
                limit=len(files_to_show)
            )
            ranked_dict = {path: score for path, score in ranked}
            files_to_show.sort(key=lambda f: ranked_dict.get(f.path, 0.0), reverse=True)
        
        parts.append("📄 KEY FILES (Use these as REFERENCE when creating similar files):\n")
        
        current_length = len('\n'.join(parts))
        
        for f in files_to_show:
            if current_length > max_length:
                break
            
            file_section = f"### {f.relative_path}\n"
            file_section += f"Language: {f.language} | Lines: {f.lines}\n"
            file_section += f"Summary: {f.summary}\n"
            
            if self._use_optimized_structures and self.dependency_graph:
                deps = self.dependency_graph.get_dependencies(f.path, direct_only=True)
                if deps:
                    dep_names = [Path(d).name for d in deps[:5]]
                    file_section += f"Dependencies: {', '.join(dep_names)}\n"
            
            if f.content and len(f.content) < 5000:
                file_section += f"```{f.extension[1:]}\n{f.content}\n```\n"
            
            if current_length + len(file_section) < max_length:
                parts.append(file_section)
                current_length += len(file_section)
        
        if current_length < max_length:
            parts.append("\n💡 TIP: When creating new files, use the files above as REFERENCE and TEMPLATE.")
            parts.append("Match their structure, imports, exports, and coding style exactly.")
        
        return '\n'.join(parts)


# Helper function for quick analysis
def analyze_codebase(path: str, max_files: int = 100, ollama_service=None) -> str:
    """
    Quick helper to analyze codebase and get AI context.
    
    Args:
        path: Root path of codebase
        max_files: Maximum files to analyze
        ollama_service: Optional Ollama service for AI-powered analysis
        
    Returns:
        Formatted context string
    """
    analyzer = CodebaseAnalyzer(path, ollama_service=ollama_service)
    analysis = analyzer.analyze(max_files)
    return analyzer.get_context_for_ai(analysis)

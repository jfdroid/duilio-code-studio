"""
Codebase Endpoints Handler
==========================
Handles codebase analysis endpoints.
Extracted from chat.py for better organization.
"""

from typing import Dict, Any
from pathlib import Path
import os

from ...services.codebase_analyzer import CodebaseAnalyzer
from ...services.ollama_service import OllamaService
from ...core.logger import get_logger
from fastapi import HTTPException
from .context_builder import get_codebase_context


class CodebaseEndpoints:
    """Handles codebase analysis endpoints."""
    
    def __init__(self):
        self.logger = get_logger()
    
    async def analyze_codebase(
        self,
        request,
        ollama: OllamaService
    ) -> Dict[str, Any]:
        """
        Analyze a codebase and return structured information.
        
        Args:
            request: AnalyzeCodebaseRequest object
            ollama: OllamaService instance
            
        Returns:
            Dict with analysis results
        """
        try:
            path = os.path.expanduser(request.path)
            
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
            
            # Try to get ollama service for AI-powered analysis
            try:
                ollama_service = ollama
            except:
                ollama_service = None
            
            analyzer = CodebaseAnalyzer(path, ollama_service=ollama_service)
            analysis = analyzer.analyze(max_files=request.max_files)
            
            # Get AI-ready context
            ai_context = analyzer.get_context_for_ai(analysis)
            
            return {
                "root_path": analysis.root_path,
                "total_files": analysis.total_files,
                "total_lines": analysis.total_lines,
                "languages": analysis.languages,
                "file_tree": analysis.file_tree,
                "entry_points": analysis.entry_points,
                "dependencies": analysis.dependencies,
                "structure_summary": analysis.structure_summary,
                "main_files": [
                    {
                        "path": f.relative_path,
                        "language": f.language,
                        "lines": f.lines,
                        "summary": f.summary,
                        "classes": f.classes[:10],
                        "functions": f.functions[:10],
                    }
                    for f in analysis.main_files[:15]
                ],
                "ai_context_length": len(ai_context),
                "ai_context_preview": ai_context[:2000] + "..." if len(ai_context) > 2000 else ai_context
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error analyzing codebase: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_codebase_context(
        self,
        path: str,
        refresh: bool = False,
        ollama: OllamaService = None
    ) -> Dict[str, Any]:
        """
        Get AI-ready context for a codebase.
        Uses caching for performance.
        
        Args:
            path: Codebase path
            refresh: Force refresh cache
            ollama: OllamaService instance
            
        Returns:
            Dict with context information
        """
        try:
            expanded_path = os.path.expanduser(path)
            
            if not os.path.exists(expanded_path):
                raise HTTPException(status_code=404, detail=f"Path not found: {path}")
            
            context = get_codebase_context(
                expanded_path, 
                force_refresh=refresh, 
                ollama_service=ollama
            )
            
            return {
                "path": path,
                "context": context,
                "length": len(context),
                "cached": not refresh
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting codebase context: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

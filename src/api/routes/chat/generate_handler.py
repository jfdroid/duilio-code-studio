"""
Generate Handler
================
Handles /generate endpoint logic.
Extracted from chat.py for better organization.
"""

import time
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directories to path for imports (same as chat.py)
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from services.ollama_service import OllamaService
from services.workspace_service import WorkspaceService
from services.user_preferences import UserPreferencesService
from services.prompt_examples import PromptExamplesService
from services.file_service import FileService
from services.intent_detector import get_intent_detector
from services.prompt_classifier import classify_prompt
from core.logger import get_logger
from core.validators import WorkspacePathValidator, ModelNameValidator, TemperatureValidator, MaxTokensValidator
from core.exceptions import ValidationError
from core.error_handler import handle_error
from fastapi import HTTPException
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_router import GenerateRequest


class GenerateHandler:
    """Handles code/text generation requests."""
    
    def __init__(self):
        self.logger = get_logger()
    
    async def handle(
        self,
        request: "GenerateRequest",
        ollama: OllamaService,
        workspace: WorkspaceService,
        user_prefs: UserPreferencesService,
        examples: PromptExamplesService
    ) -> Dict[str, Any]:
        """
        Handle generate request.
        
        Args:
            request: GenerateRequest object
            ollama: OllamaService instance
            workspace: WorkspaceService instance
            user_prefs: UserPreferencesService instance
            examples: PromptExamplesService instance
            
        Returns:
            Dict with generated response
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            request.model = ModelNameValidator.validate(request.model)
            request.temperature = TemperatureValidator.validate(request.temperature)
            request.max_tokens = MaxTokensValidator.validate(request.max_tokens)
            
            # Classify prompt
            models = await ollama.list_models()
            classification = classify_prompt(request.prompt, models)
            
            # Get user preferences
            preferred_model = user_prefs.get_best_model(
                classification.is_code_related,
                [m.get("name", m) if isinstance(m, dict) else m for m in models]
            )
            
            # Detect file intent
            workspace_path = self._resolve_workspace_path(request.workspace_path, workspace)
            read_file_intent, file_to_read, file_content_context = await self._detect_file_intent(
                request.prompt, workspace_path, ollama
            )
            
            # Read file if requested
            if read_file_intent and file_to_read and workspace_path:
                file_content_context = await self._read_file(file_to_read, workspace_path)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(
                request, classification, workspace_path, file_content_context, examples, ollama
            )
            
            # Generate response
            result = await ollama.generate(
                prompt=request.prompt,
                model=request.model,
                system_prompt=system_prompt,
                context=request.context,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Update user preferences
            user_prefs.record_interaction(
                prompt=request.prompt,
                model=request.model,
                category=classification.category.value,
                success=True
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "response": result.response,
                "model": result.model,
                "tokens": result.tokens,
                "duration_ms": duration,
                "classification": {
                    "category": classification.category.value,
                    "confidence": classification.confidence,
                    "is_code_related": classification.is_code_related
                }
            }
            
        except ValidationError as e:
            raise handle_error(e, context={"endpoint": "generate", "model": request.model})
        except Exception as e:
            self.logger.error(f"Error in generate: {e}", exc_info=True)
            raise handle_error(e, context={"endpoint": "generate"})
    
    def _resolve_workspace_path(self, request_path: Optional[str], workspace: WorkspaceService) -> Optional[str]:
        """Resolve workspace path from request or workspace service."""
        if request_path:
            return request_path
        
        project_context = workspace.get_project_context()
        if project_context.get("has_workspace"):
            return project_context.get("root_path")
        
        workspace_state = workspace.get_current()
        if workspace_state and workspace_state.path:
            return workspace_state.path
        
        return None
    
    async def _detect_file_intent(
        self, prompt: str, workspace_path: Optional[str], ollama: OllamaService
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Detect if user wants to read a file."""
        read_file_intent = False
        file_to_read = None
        file_content_context = None
        
        if not workspace_path:
            return read_file_intent, file_to_read, file_content_context
        
        try:
            intent_detector = get_intent_detector(ollama)
            intent_result = await intent_detector.detect_file_intent(prompt, workspace_path)
            
            if intent_result["intent"] == "read":
                read_file_intent = True
                file_to_read = intent_result.get("file_name")
                if file_to_read:
                    file_to_read = file_to_read.strip('.,!?;:')
        except Exception as e:
            self.logger.error(f"Error in file intent detection: {e}")
        
        return read_file_intent, file_to_read, file_content_context
    
    async def _read_file(self, file_to_read: str, workspace_path: str) -> Optional[str]:
        """Read file content if file exists."""
        try:
            file_service = FileService()
            workspace_path_obj = Path(workspace_path)
            
            # Try to find file
            possible_paths = [workspace_path_obj / file_to_read]
            
            if '.' not in file_to_read:
                for ext in ['.txt', '.js', '.py', '.json', '.md']:
                    possible_paths.append(workspace_path_obj / f"{file_to_read}{ext}")
            
            for path in possible_paths:
                if path.exists() and path.is_file():
                    file_content = file_service.read_file(str(path))
                    return f"\n\n=== FILE CONTENT: {path.name} ===\n{file_content.content}\n=== END OF FILE ===\n"
        except Exception as e:
            self.logger.error(f"Error reading file: {e}")
        
        return None
    
    def _build_system_prompt(
        self, request, classification, workspace_path, file_content_context, examples, ollama: OllamaService
    ) -> str:
        """Build system prompt with context."""
        system_prompt = request.system_prompt
        if not system_prompt:
            base_system = ollama.CODE_SYSTEM_PROMPT if classification.is_code_related else ollama.GENERAL_SYSTEM_PROMPT
            system_prompt = f"{base_system}\n\n{classification.system_prompt_modifier}"
            
            if workspace_path:
                system_prompt += f"\n\n=== CRITICAL WORKSPACE CONTEXT ==="
                system_prompt += f"\nThe user has opened workspace: {workspace_path}"
                system_prompt += "\nWhen they ask about 'this codebase', 'this project', or 'the code', you MUST refer to the workspace analysis provided in the context."
                system_prompt += "\nYou KNOW this codebase - analyze it, explain it, help them work with it!"
                
                if file_content_context:
                    system_prompt += "\n\n=== FILE READING DETECTED ==="
                    system_prompt += "\nThe file content is provided in the context above."
                    system_prompt += "\nDO NOT use create-file: format. Simply explain what is written in the file."
                    system_prompt += "\nAnswer in the SAME LANGUAGE the user wrote (Portuguese/English)."
                elif request.include_codebase:
                    from .context_builder import get_codebase_context
                    codebase_context = get_codebase_context(
                        workspace_path, 
                        force_refresh=False, 
                        query=request.prompt,
                        ollama_service=ollama
                    )
                    if codebase_context:
                        system_prompt += f"\n\n=== CODEBASE CONTEXT ===\n{codebase_context}"
        
        return system_prompt

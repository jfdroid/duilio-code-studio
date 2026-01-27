"""
Chat Handler
============
Handles /chat endpoint logic.
Extracted from chat.py for better organization.
"""

import re
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add parent directories to path for imports (same as chat.py)
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from services.ollama_service import OllamaService
from services.workspace_service import WorkspaceService
from services.file_service import FileService
from services.intent_detector import get_intent_detector
from services.prompt_classifier import classify_prompt
from services.prompt_builder import PromptBuilder, OperationType
from services.linguistic_analyzer import get_linguistic_analyzer
from services.system_info import get_system_info_service
from services.path_intelligence import PathIntelligence
from services.project_detector import get_project_detector
from services.action_processor import get_action_processor
from core.logger import get_logger
from core.validators import ModelNameValidator, TemperatureValidator
from core.exceptions import ValidationError
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from typing import TYPE_CHECKING
from .context_builder import get_codebase_context

if TYPE_CHECKING:
    from .chat_router import ChatRequest


class ChatHandler:
    """Handles chat completion requests."""
    
    def __init__(self):
        self.logger = get_logger()
    
    async def handle(
        self,
        request: "ChatRequest",
        ollama: OllamaService,
        workspace: WorkspaceService
    ) -> Dict[str, Any]:
        """
        Handle chat request.
        
        Args:
            request: ChatRequest object
            ollama: OllamaService instance
            workspace: WorkspaceService instance
            
        Returns:
            Dict with chat response
        """
        # Initialize adjusted_temperature early
        adjusted_temperature = request.temperature
        
        try:
            # Validate inputs
            request.model = ModelNameValidator.validate(request.model)
            request.temperature = TemperatureValidator.validate(request.temperature)
            
            # Convert messages to prompt
            messages = request.messages
            prompt_parts = []
            system_prompt = None
            last_user_message = ""
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    system_prompt = content
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                    last_user_message = content
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            
            # Classify the latest user message
            models = await ollama.list_models()
            classification = classify_prompt(last_user_message, models)
            
            # Detect file intent
            workspace_path = self._resolve_workspace_path(request.workspace_path, workspace)
            
            self.logger.info(
                f"Workspace path for chat: {workspace_path}",
                workspace_path=workspace_path,
                context={
                    "request_workspace": request.workspace_path,
                    "final_workspace": workspace_path,
                    "has_workspace": bool(workspace_path),
                    "message": last_user_message[:100]
                }
            )
            
            # Detect file reading intent
            read_file_intent, file_to_read, file_content_context = await self._detect_file_intent(
                last_user_message, workspace_path, ollama
            )
            
            # Read file if requested
            if read_file_intent and file_to_read and workspace_path:
                file_content_context = await self._read_file(file_to_read, workspace_path)
            
            # Build context
            context_parts = []
            if file_content_context:
                context_parts.append(file_content_context)
            
            # Detect CRUD intentions
            crud_intent = self._detect_crud_intent(last_user_message)
            
            # Detect file listing intent
            list_files_intent, seeing_created_intent = self._detect_list_intent(last_user_message)
            
            if list_files_intent:
                adjusted_temperature = min(adjusted_temperature, 0.2)
            
            # Add file listing context if needed
            if workspace_path and (list_files_intent or seeing_created_intent):
                file_listing_context = await self._build_file_listing_context(workspace_path)
                if file_listing_context:
                    context_parts.insert(0, file_listing_context)
            
            # Add codebase context
            if workspace_path:
                try:
                    codebase_context = get_codebase_context(
                        workspace_path,
                        force_refresh=True,
                        query=last_user_message,
                        ollama_service=ollama
                    )
                    context_parts.append(codebase_context)
                    self.logger.info(
                        f"Loaded codebase context: {len(codebase_context)} chars",
                        workspace_path=workspace_path
                    )
                except Exception as e:
                    self.logger.error(f"Codebase analysis error: {e}", workspace_path=workspace_path)
            
            # Build system prompt
            system_prompt = await self._build_system_prompt(
                system_prompt,
                classification,
                workspace_path,
                last_user_message,
                read_file_intent,
                file_to_read,
                file_content_context,
                crud_intent,
                list_files_intent,
                seeing_created_intent,
                ollama
            )
            
            # Build full prompt
            operation = self._determine_operation(
                read_file_intent,
                crud_intent,
                list_files_intent,
                seeing_created_intent
            )
            
            # Build prompt manually (PromptBuilder.build_full_prompt adds operation prompt twice)
            # Separate file listing from other context
            file_listing = [c for c in context_parts if "FILE LISTING" in c]
            other_context = [c for c in context_parts if c not in file_listing]
            
            full_prompt = system_prompt
            
            # Add file listing first (highest priority)
            if file_listing:
                full_prompt += "\n\n" + "\n".join(file_listing)
            
            # Add other context
            if other_context:
                full_prompt += "\n\n" + "\n".join(other_context)
            
            # Add user messages
            full_prompt += "\n\n---\n\n"
            full_prompt += "\n".join(prompt_parts)
            full_prompt += "\n\nAssistant:"
            
            # Handle streaming
            if request.stream:
                return self._handle_streaming(
                    full_prompt,
                    request.model,
                    system_prompt,
                    adjusted_temperature,
                    ollama
                )
            
            # Generate response
            result = await ollama.generate(
                prompt=full_prompt,
                model=request.model,
                system_prompt=system_prompt,
                temperature=adjusted_temperature,
                auto_select_model=False
            )
            
            # Initialize response_content safely
            if not result or not hasattr(result, 'response') or not result.response:
                self.logger.error("Invalid response from Ollama", workspace_path=workspace_path)
                response_content = "I apologize, but I encountered an error generating a response. Please try again."
            else:
                response_content = result.response
            
            # Process agent actions
            actions_processed = False
            actions_result = None
            
            if read_file_intent:
                # Remove create-file actions if user wanted to read
                if 'create-file:' in response_content:
                    self.logger.warning("AI generated create-file for a READ request. Removing it.")
                    response_content = re.sub(r'```create-file:[^\n]+\n[\s\S]*?```', '', response_content)
                    response_content = re.sub(r'create-file:[^\n]+', '', response_content)
            else:
                # Process actions if present
                if any(action in response_content for action in [
                    'create-file:', 'modify-file:', 'delete-file:', 
                    'delete-directory:', 'run-command'
                ]):
                    processor = get_action_processor(ollama_service=ollama)
                    actions_result = await processor.process_actions(
                        response_content,
                        workspace_path
                    )
                    response_content = actions_result['processed_text']
                    actions_processed = True
            
            # Determine if explorer should refresh
            refresh_explorer = (
                actions_processed and 
                actions_result and 
                actions_result.get('success_count', 0) > 0
            )
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    }
                }],
                "model": request.model,
                "usage": result.usage if hasattr(result, 'usage') else {},
                "actions_result": actions_result if actions_processed else None,
                "actions_processed": actions_processed,
                "refresh_explorer": refresh_explorer,
                "classification": {
                    "category": classification.category.value,
                    "is_code_related": classification.is_code_related
                }
            }
            
        except ValidationError as e:
            raise HTTPException(status_code=e.status_code, detail=e.detail)
        except Exception as e:
            self.logger.error(f"Error in chat: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    def _resolve_workspace_path(
        self, 
        request_path: Optional[str], 
        workspace: WorkspaceService
    ) -> Optional[str]:
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
        self, 
        prompt: str, 
        workspace_path: Optional[str], 
        ollama: OllamaService
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
            possible_paths = [workspace_path_obj / file_to_read]
            
            if '.' not in file_to_read:
                for ext in ['.txt', '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.kt', 
                           '.go', '.rs', '.rb', '.json', '.html', '.css', '.md']:
                    possible_paths.append(workspace_path_obj / f"{file_to_read}{ext}")
            
            if '/' in file_to_read or file_to_read.startswith('/'):
                possible_paths.insert(0, Path(file_to_read))
            
            for path in possible_paths:
                try:
                    if path.exists() and path.is_file():
                        file_content = file_service.read_file(str(path))
                        return f"\n\n=== FILE CONTENT: {path.name} ===\n{file_content.content}\n=== END OF FILE ===\n"
                except Exception:
                    continue
            
            # Search in workspace tree
            try:
                from services.workspace_service import get_workspace_service
                ws_service = get_workspace_service()
                tree = ws_service.get_file_tree(workspace_path, max_depth=5)
                
                def find_file_in_tree(node, filename):
                    node_name = node.get('name', '').lower()
                    filename_lower = filename.lower()
                    node_type = node.get('type', '')
                    
                    if (node_name == filename_lower or node_name.startswith(filename_lower)) and node_type == 'file':
                        return node.get('path')
                    
                    for child in node.get('children', []):
                        result = find_file_in_tree(child, filename)
                        if result:
                            return result
                    return None
                
                file_path = find_file_in_tree(tree, file_to_read)
                if file_path:
                    file_content = file_service.read_file(file_path)
                    return f"\n\n=== FILE CONTENT: {Path(file_path).name} ===\n{file_content.content}\n=== END OF FILE ===\n"
            except Exception as e:
                self.logger.error(f"Error searching for file in tree: {e}")
        except Exception as e:
            self.logger.error(f"Error reading file: {e}")
        
        return None
    
    def _detect_crud_intent(self, message: str) -> Dict[str, bool]:
        """Detect CRUD operation intentions."""
        message_lower = message.lower()
        
        create_keywords = [
            'criar arquivo', 'create file', 'criar pasta', 'create folder',
            'criar documento', 'create document', 'novo arquivo', 'new file',
            'adicionar arquivo', 'add file', 'gerar arquivo', 'generate file',
            'criar script', 'create script', 'criar projeto', 'create project',
            'crie um', 'crie uma', 'criar um', 'criar uma'
        ]
        
        update_keywords = [
            'modificar arquivo', 'modify file', 'editar arquivo', 'edit file',
            'atualizar arquivo', 'update file', 'alterar arquivo', 'change file',
            'atualizar', 'update', 'modificar', 'modify', 'editar', 'edit'
        ]
        
        delete_keywords = [
            'deletar arquivo', 'delete file', 'remover arquivo', 'remove file',
            'apagar arquivo', 'erase file', 'excluir arquivo', 'exclude file',
            'deletar', 'delete', 'remover', 'remove', 'apagar', 'erase'
        ]
        
        read_keywords = [
            'ler arquivo', 'read file', 'ver arquivo', 'see file',
            'mostrar arquivo', 'show file', 'conteúdo do arquivo', 'file content'
        ]
        
        return {
            'create': any(kw in message_lower for kw in create_keywords),
            'update': any(kw in message_lower for kw in update_keywords),
            'delete': any(kw in message_lower for kw in delete_keywords),
            'read': any(kw in message_lower for kw in read_keywords),
            'list': False  # Handled separately
        }
    
    def _detect_list_intent(self, message: str) -> tuple[bool, bool]:
        """Detect file listing intent."""
        message_lower = message.lower()
        
        list_keywords = [
            'quantos arquivos', 'how many files',
            'quantas pastas', 'how many folders',
            'listar arquivos', 'list files',
            'arquivos do path', 'files in path',
            'quero ver os arquivos', 'i want to see the files',
            'voce ve arquivos', 'you see files',
            'consegue ver os arquivos', 'can you see the files'
        ]
        
        seeing_created_keywords = [
            'voce esta vendo', 'you are seeing',
            'voce criou', 'you created',
            'esta vendo o que criou', 'seeing what you created'
        ]
        
        list_files_intent = any(kw in message_lower for kw in list_keywords)
        seeing_created_intent = any(kw in message_lower for kw in seeing_created_keywords)
        
        return list_files_intent, seeing_created_intent
    
    async def _build_file_listing_context(self, workspace_path: str) -> Optional[str]:
        """Build file listing context."""
        try:
            from services.workspace_service import get_workspace_service
            ws_service = get_workspace_service()
            workspace_path_obj = Path(workspace_path)
            
            # Count files accurately
            def count_files_accurate(path: Path, max_files: int = 50000) -> tuple[int, int]:
                files_count = 0
                folders_count = 0
                
                def scan(p: Path, depth: int = 0):
                    nonlocal files_count, folders_count
                    if depth > 15 or files_count > max_files:
                        return
                    
                    try:
                        for item in p.iterdir():
                            if item.name.startswith('.'):
                                continue
                            if item.is_dir():
                                folders_count += 1
                                scan(item, depth + 1)
                            elif item.is_file():
                                files_count += 1
                    except (PermissionError, OSError):
                        pass
                
                scan(path)
                return files_count, folders_count
            
            total_files, total_folders = count_files_accurate(workspace_path_obj)
            
            # Get file tree
            file_tree = ws_service.get_file_tree(workspace_path, max_depth=3)
            
            def collect_files(node, file_list=None, prefix=""):
                if file_list is None:
                    file_list = []
                current_path = prefix + node.get('name', '')
                if node.get('type') == 'file':
                    ext = node.get('extension', '')
                    file_type = ext[1:] if ext else 'no extension'
                    file_list.append({
                        'name': node.get('name', ''),
                        'path': current_path,
                        'type': file_type
                    })
                for child in node.get('children', []):
                    collect_files(child, file_list, current_path + '/')
                return file_list
            
            def collect_folders(node, folder_list=None, prefix=""):
                if folder_list is None:
                    folder_list = []
                current_path = prefix + node.get('name', '')
                if node.get('type') == 'directory':
                    folder_list.append({
                        'name': node.get('name', ''),
                        'path': current_path,
                        'type': 'folder'
                    })
                for child in node.get('children', []):
                    collect_folders(child, folder_list, current_path + '/')
                return folder_list
            
            all_files = collect_files(file_tree)
            all_folders = collect_folders(file_tree)
            
            files_only = [f for f in all_files if Path(f['path']).suffix]
            
            # Use PromptBuilder for clean format
            return PromptBuilder.build_file_listing_context(
                files=files_only,
                folders=all_folders,
                workspace_path=workspace_path,
                total_files=total_files,
                total_folders=total_folders
            )
        except Exception as e:
            self.logger.error(f"Error building file listing context: {e}")
            return None
    
    async def _build_system_prompt(
        self,
        existing_system_prompt: Optional[str],
        classification,
        workspace_path: Optional[str],
        last_user_message: str,
        read_file_intent: bool,
        file_to_read: Optional[str],
        file_content_context: Optional[str],
        crud_intent: Dict[str, bool],
        list_files_intent: bool,
        seeing_created_intent: bool,
        ollama: OllamaService
    ) -> str:
        """Build system prompt with all context."""
        if existing_system_prompt:
            system_prompt = existing_system_prompt
        else:
            base_system = ollama.CODE_SYSTEM_PROMPT if classification.is_code_related else ollama.GENERAL_SYSTEM_PROMPT
            system_prompt = f"{base_system}\n\n{classification.system_prompt_modifier}"
        
        # Add system information for Agent mode
        try:
            system_info_service = get_system_info_service()
            system_info_text = system_info_service.get_formatted_prompt()
            system_prompt = PromptBuilder.build_agent_mode_prompt(system_info_text)
            self.logger.info("Added system information to Agent mode prompt")
        except Exception as e:
            self.logger.warning(f"Could not add system information: {e}")
        
        if workspace_path:
            # Detect explanation request
            explanation_keywords = [
                'por que', 'porque', 'pq', 'why', 'como', 'how',
                'explain', 'explique', 'motivo', 'razão', 'reason'
            ]
            explanation_intent = any(kw in last_user_message.lower() for kw in explanation_keywords)
            
            # Linguistic analysis
            linguistic_analyzer = get_linguistic_analyzer()
            linguistic_analysis = linguistic_analyzer.analyze(last_user_message)
            linguistic_context = linguistic_analyzer.build_structured_context(linguistic_analysis)
            
            explanation_intent = linguistic_analysis.requires_explanation
            
            if linguistic_context:
                system_prompt += f"\n\n=== LINGUISTIC ANALYSIS ===\n{linguistic_context}\n"
            
            if explanation_intent:
                system_prompt += "\n\nEXPLANATION REQUEST DETECTED:"
                system_prompt += "\n- User asked WHY/HOW/EXPLAIN - provide detailed reasoning"
                system_prompt += "\n- Reference the FILE LISTING or context you used"
            
            if linguistic_analysis.requires_data:
                system_prompt += "\n\nDATA REQUEST DETECTED:"
                system_prompt += "\n- Use FILE LISTING to provide exact numbers and names"
            
            # Determine operation
            operation = self._determine_operation(
                read_file_intent,
                crud_intent,
                list_files_intent,
                seeing_created_intent
            )
            
            # Add CRUD-specific prompts
            if operation:
                crud_context = {}
                if operation == OperationType.CREATE:
                    # Detect project intention
                    try:
                        project_detector = get_project_detector(ollama)
                        project_intention = await project_detector.detect_project_intention(
                            last_user_message, workspace_path
                        )
                        if project_intention.get("needs_directory", False):
                            crud_context = {
                                "project_type": project_intention.get("project_type", "general"),
                                "project_name": project_intention.get("project_name", "new-project")
                            }
                    except Exception as e:
                        self.logger.warning(f"Error detecting project intention: {e}")
                
                system_prompt += PromptBuilder.build_crud_prompt(operation, crud_context)
            
            system_prompt += f"\n\nWorkspace: {workspace_path}"
        
        return system_prompt
    
    def _determine_operation(
        self,
        read_file_intent: bool,
        crud_intent: Dict[str, bool],
        list_files_intent: bool,
        seeing_created_intent: bool
    ) -> Optional[OperationType]:
        """Determine operation type from intents."""
        if read_file_intent:
            return OperationType.READ
        elif crud_intent['create']:
            return OperationType.CREATE
        elif crud_intent['update']:
            return OperationType.UPDATE
        elif crud_intent['delete']:
            return OperationType.DELETE
        elif list_files_intent or seeing_created_intent:
            return OperationType.LIST
        return None
    
    def _handle_streaming(
        self,
        prompt: str,
        model: str,
        system_prompt: str,
        temperature: float,
        ollama: OllamaService
    ) -> StreamingResponse:
        """Handle streaming response."""
        async def stream_generator():
            async for token in ollama.generate_stream(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )

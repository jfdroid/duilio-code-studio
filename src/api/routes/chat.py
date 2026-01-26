"""
Chat Routes
===========
AI code generation and chat endpoints.
Includes intelligent codebase analysis, smart model selection,
user preference learning, and few-shot example matching.
"""

import time
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from services.ollama_service import OllamaService, get_ollama_service
from services.workspace_service import WorkspaceService, get_workspace_service
from services.codebase_analyzer import CodebaseAnalyzer, analyze_codebase
from services.prompt_classifier import PromptClassifier, classify_prompt
from services.user_preferences import UserPreferencesService, get_user_preferences_service
from services.prompt_examples import PromptExamplesService, get_prompt_examples_service
from services.file_service import FileService
from core.logger import get_logger


import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
router = APIRouter(prefix="/api", tags=["Chat"])


# === Request Models ===

class GenerateRequest(BaseModel):
    """Request for code/text generation."""
    prompt: str = Field(..., description="The prompt")
    model: str = Field(..., description="Model to use (required)")
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    workspace_path: Optional[str] = Field(default=None, description="Path to analyze for context")
    include_codebase: bool = Field(default=True, description="Include codebase analysis in context")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: list = Field(..., description="Message history")
    model: str = Field(..., description="Model to use (required)")
    workspace_path: Optional[str] = Field(default=None, description="Workspace path for context")
    temperature: float = Field(default=0.7)
    stream: bool = Field(default=False)


class AnalyzeCodebaseRequest(BaseModel):
    """Request to analyze a codebase."""
    path: str = Field(..., description="Path to the codebase")
    max_files: int = Field(default=100, description="Maximum files to analyze")


# === Codebase Context Cache ===
_codebase_cache: Dict[str, str] = {}


def get_codebase_context(path: str, force_refresh: bool = False, query: str = "", ollama_service=None) -> str:
    """
    Get or generate codebase context with caching.
    
    Args:
        path: Codebase path
        force_refresh: Force refresh cache
        query: Query for relevance scoring
        ollama_service: Optional Ollama service for AI-powered analysis
    """
    global _codebase_cache
    
    cache_key = f"{path}:{query}"
    if not force_refresh and cache_key in _codebase_cache:
        return _codebase_cache[cache_key]
    
    try:
        from services.codebase_analyzer import CodebaseAnalyzer
        analyzer = CodebaseAnalyzer(path, ollama_service=ollama_service)
        # IMPORTANT:
        # - Chat needs fresh context so the model can accurately MODIFY recently created/edited files.
        # - Passing `query` into analysis enables relevance scoring.
        analysis = analyzer.analyze(max_files=100, query=query, use_cache=not force_refresh)
        context = analyzer.get_context_for_ai(analysis, max_length=8000, query=query)
        _codebase_cache[cache_key] = context
        return context
    except Exception as e:
        return f"[Error analyzing codebase: {str(e)}]"


# === Rate Limiting ===
try:
    from middleware.rate_limiter import limiter, rate_limit_decorator
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    # Dummy decorator if rate limiting not available
    def rate_limit_decorator(limit: str = None):
        def decorator(func):
            return func
        return decorator

# === Endpoints ===

@router.post("/generate")
@rate_limit_decorator("20/minute")  # Code generation - lower limit
async def generate(
    request: GenerateRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    workspace: WorkspaceService = Depends(get_workspace_service),
    user_prefs: UserPreferencesService = Depends(get_user_preferences_service),
    examples: PromptExamplesService = Depends(get_prompt_examples_service)
) -> Dict[str, Any]:
    logger = get_logger()
    """
    Generate code or text response with FULL INTELLIGENCE.
    
    Features:
    - Intelligent model selection based on prompt AND user preferences
    - Automatic codebase analysis for context
    - Smart prompt classification with ML-like patterns
    - Few-shot learning from similar examples
    - User preference learning and adaptation
    """
    start_time = time.time()
    
    try:
        # === 1. CLASSIFY THE PROMPT ===
        models = await ollama.list_models()
        classification = classify_prompt(request.prompt, models)
        
        # === 2. GET USER PREFERENCES ===
        preferred_model = user_prefs.get_best_model(
            classification.is_code_related,
            [m.get("name", m) if isinstance(m, dict) else m for m in models]
        )
        
        # === 3. DETECT FILE INTENT USING AI ===
        read_file_intent = False
        file_to_read = None
        
        # Get workspace path first for file search
        # CRITICAL: Always use explorer path if request.workspace_path is not provided
        workspace_path = request.workspace_path
        if not workspace_path:
            project_context = workspace.get_project_context()
            if project_context.get("has_workspace"):
                workspace_path = project_context.get("root_path")
                logger.info(
                    f"Using explorer path: {workspace_path}",
                    workspace_path=workspace_path
                )
        
        # Use AI-powered intent detection instead of hardcoded patterns
        from services.intent_detector import get_intent_detector
        intent_detector = get_intent_detector(ollama)
        
        try:
            intent_result = await intent_detector.detect_file_intent(
                request.prompt,
                workspace_path
            )
            
            logger.debug(
                f"AI Intent Detection: {intent_result}",
                workspace_path=workspace_path,
                context={"intent_result": intent_result}
            )
            
            if intent_result["intent"] == "read":
                read_file_intent = True
                file_to_read = intent_result.get("file_name")
                if file_to_read:
                    file_to_read = file_to_read.strip('.,!?;:')
                logger.info(
                    f"Detected READ intent for file: {file_to_read}",
                    workspace_path=workspace_path,
                    file_path=file_to_read,
                    context={"confidence": intent_result.get('confidence', 0.0)}
                )
        except Exception as e:
            logger.error(
                f"Error in AI intent detection: {e}",
                workspace_path=workspace_path,
                context={"error": str(e)}
            )
            # Fallback: don't set read_file_intent if AI detection fails
        
        # === 4. READ FILE IF REQUESTED ===
        file_content_context = None
        if read_file_intent and file_to_read and workspace_path:
            try:
                file_service = FileService()
                
                logger.info(
                    f"Detected file reading intent for: '{file_to_read}'",
                    workspace_path=workspace_path,
                    file_path=file_to_read
                )
                
                # Try to find the file in workspace
                workspace_path_obj = Path(workspace_path)
                
                # Build list of possible paths to check
                possible_paths = []
                
                # 1. Direct match (if file_to_read already has extension)
                possible_paths.append(workspace_path_obj / file_to_read)
                
                # 2. Add common extensions if no extension in file_to_read
                if '.' not in file_to_read:
                    for ext in ['.txt', '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.kt', '.go', '.rs', '.rb', '.json', '.html', '.css', '.md']:
                        possible_paths.append(workspace_path_obj / f"{file_to_read}{ext}")
                
                # 3. Check if file_to_read is already a full path
                if '/' in file_to_read or file_to_read.startswith('/'):
                    possible_paths.insert(0, Path(file_to_read))
                
                # 4. Also check in current directory if workspace_path is Desktop
                if 'Desktop' in str(workspace_path):
                    possible_paths.append(Path(workspace_path) / file_to_read)
                    if '.' not in file_to_read:
                        possible_paths.append(Path(workspace_path) / f"{file_to_read}.txt")
                
                file_found = None
                for path in possible_paths:
                    try:
                        if path.exists() and path.is_file():
                            file_found = path
                            logger.info(
                                f"Found file at: {file_found}",
                                workspace_path=workspace_path,
                                file_path=str(file_found)
                            )
                            break
                    except Exception:
                        continue
                
                if file_found:
                    try:
                        file_content = file_service.read_file(str(file_found))
                        file_content_context = f"\n\n=== FILE CONTENT: {file_found.name} ===\n{file_content.content}\n=== END OF FILE ===\n"
                        logger.info(
                            f"Successfully read file {file_found}",
                            workspace_path=workspace_path,
                            file_path=str(file_found),
                            context={"content_length": len(file_content.content)}
                        )
                    except Exception as e:
                        logger.error(
                            f"Error reading file {file_found}: {e}",
                            workspace_path=workspace_path,
                            file_path=str(file_found),
                            context={"error": str(e)}
                        )
                else:
                    # Try to search in workspace tree using get_file_tree
                    try:
                        from services.workspace_service import get_workspace_service
                        ws_service = get_workspace_service()
                        tree = ws_service.get_file_tree(workspace_path, max_depth=5)
                        
                        # Search for file in tree (case-insensitive)
                        def find_file_in_tree(node, filename):
                            node_name = node.get('name', '').lower()
                            filename_lower = filename.lower()
                            node_type = node.get('type', '')
                            
                            # Exact match or starts with filename
                            if (node_name == filename_lower or node_name.startswith(filename_lower)) and node_type == 'file':
                                return node.get('path')
                            
                            # Recursive search in children
                            for child in node.get('children', []):
                                result = find_file_in_tree(child, filename)
                                if result:
                                    return result
                            return None
                        
                        file_path = find_file_in_tree(tree, file_to_read)
                        if file_path:
                            file_content = file_service.read_file(file_path)
                            file_content_context = f"\n\n=== FILE CONTENT: {Path(file_path).name} ===\n{file_content.content}\n=== END OF FILE ===\n"
                            logger.info(
                                f"Found and read file {file_path} via tree search",
                                workspace_path=workspace_path,
                                file_path=file_path
                            )
                        else:
                            logger.warning(
                                f"File '{file_to_read}' not found in workspace",
                                workspace_path=workspace_path,
                                file_path=file_to_read
                            )
                            # Even if not found, read_file_intent is already True, so system will know it's a read request
                    except Exception as e:
                        logger.error(
                            f"Error searching for file in tree: {e}",
                            workspace_path=workspace_path,
                            file_path=file_to_read,
                            context={"error": str(e)}
                        )
            except Exception as e:
                logger.error(
                    f"Error in file reading detection: {e}",
                    workspace_path=workspace_path,
                    file_path=file_to_read,
                    context={"error": str(e)}
                )
        
        # === 5. BUILD COMPREHENSIVE CONTEXT ===
        context_parts = []
        
        # Add file content if file was read
        if file_content_context:
            context_parts.append(file_content_context)
        
        # Add user-provided context
        if request.context:
            context_parts.append(request.context)
        
        # === 6. ANALYZE CODEBASE (THE KEY FEATURE!) ===
        # CRITICAL: Always use workspace_path (which is explorer path) for codebase analysis
        if workspace_path and request.include_codebase:
            try:
                # Ensure we're using the explorer path for codebase analysis
                codebase_context = get_codebase_context(workspace_path, ollama_service=ollama)
                context_parts.append(codebase_context)
                logger.info(
                    f"Loaded codebase context: {len(codebase_context)} chars",
                    workspace_path=workspace_path,
                    context={"context_length": len(codebase_context)}
                )
            except Exception as e:
                logger.error(
                    f"Codebase analysis error: {e}",
                    workspace_path=workspace_path,
                    context={"error": str(e)}
                )
                context_parts.append(f"[Workspace: {workspace_path}]")
        
        # === 7. ADD FEW-SHOT EXAMPLES ===
        few_shot = examples.get_few_shot_context(
            request.prompt,
            classification.category.value
        )
        if few_shot:
            context_parts.append(few_shot)
        
        # Get intent hint
        intent = examples.get_intent_hint(request.prompt)
        
        # Combine context
        full_context = "\n\n".join(context_parts) if context_parts else None
        
        # === 8. BUILD ENHANCED SYSTEM PROMPT ===
        system_prompt = request.system_prompt
        if not system_prompt:
            base_system = ollama.CODE_SYSTEM_PROMPT if classification.is_code_related else ollama.GENERAL_SYSTEM_PROMPT
            system_prompt = f"{base_system}\n\n{classification.system_prompt_modifier}"
            
            if workspace_path:
                system_prompt += f"\n\n=== CRITICAL WORKSPACE CONTEXT ==="
                system_prompt += f"\nThe user has opened workspace: {workspace_path}"
                system_prompt += "\nWhen they ask about 'this codebase', 'this project', or 'the code', you MUST refer to the workspace analysis provided in the context."
                system_prompt += "\nYou KNOW this codebase - analyze it, explain it, help them work with it!"
                
                # CRITICAL: Distinguish between READ and CREATE file intents
                if read_file_intent and file_content_context:
                    system_prompt += "\n\n=== FILE READING DETECTED ==="
                    system_prompt += f"\nThe user wants to READ the file '{file_to_read}', NOT create it."
                    system_prompt += "\nThe file content is provided in the context above."
                    system_prompt += "\nDO NOT use create-file: format. Simply explain what is written in the file."
                    system_prompt += "\nAnswer in the SAME LANGUAGE the user wrote (Portuguese/English)."
                elif request.include_codebase:
                    # Detect project intention
                    from services.project_detector import get_project_detector
                    project_detector = get_project_detector(ollama)
                    project_intention = await project_detector.detect_project_intention(
                        request.prompt, workspace_path
                    )
                    
                    # Add specific instructions for file creation
                    system_prompt += "\n\n=== FILE CREATION INSTRUCTIONS ==="
                    system_prompt += "\n\nCRITICAL: You MUST use this EXACT format to create files:"
                    system_prompt += "\n```create-file:path/to/file.ext"
                    system_prompt += "\n[file content here]"
                    system_prompt += "\n```"
                    
                    if project_intention.get("needs_directory", False):
                        project_name = project_intention.get("project_name", "new-project")
                        project_type = project_intention.get("project_type", "general")
                        
                        system_prompt += f"\n\n🎯 PROJECT CREATION DETECTED: User wants to create a {project_type} project."
                        system_prompt += f"\nCRITICAL PROJECT DIRECTORY RULE:"
                        system_prompt += f"\n1. FIRST create the project directory: ```create-directory:{project_name}```"
                        system_prompt += f"\n2. THEN create ALL files INSIDE this directory: ```create-file:{project_name}/package.json```"
                        system_prompt += f"\n3. ALL files must be created inside {project_name}/ directory"
                        system_prompt += f"\n4. Example: ```create-file:{project_name}/src/index.js``` NOT ```create-file:src/index.js```"
                        system_prompt += f"\n5. This keeps the project isolated and organized"
                        system_prompt += f"\n6. DO NOT create files in workspace root - they must be inside {project_name}/"
                        
                        # Add project-type-specific instructions
                        if project_type == "android":
                            system_prompt += f"\n\n📱 ANDROID PROJECT REQUIREMENTS:"
                            system_prompt += f"\n- MUST create build.gradle (project level)"
                            system_prompt += f"\n- MUST create settings.gradle"
                            system_prompt += f"\n- MUST create app/build.gradle"
                            system_prompt += f"\n- MUST create app/src/main/AndroidManifest.xml"
                            system_prompt += f"\n- MUST create Kotlin/Java source files in app/src/main/java/"
                            system_prompt += f"\n- MUST create MainActivity.kt or MainActivity.java"
                            system_prompt += f"\n- If API mock requested: MUST create API service/mock files"
                            system_prompt += f"\n- Create ALL files in ONE response using multiple ```create-file: blocks"
                        
                        elif project_type == "react":
                            system_prompt += f"\n\n⚛️ REACT PROJECT REQUIREMENTS:"
                            system_prompt += f"\n- MUST create package.json with React dependencies"
                            system_prompt += f"\n- MUST create public/index.html"
                            system_prompt += f"\n- MUST create src/index.js or src/index.jsx"
                            system_prompt += f"\n- MUST create src/App.jsx or src/App.js"
                            system_prompt += f"\n- MUST create React components (JSX/TSX files)"
                            system_prompt += f"\n- Create ALL files in ONE response using multiple ```create-file: blocks"
                        
                        elif project_type == "node":
                            system_prompt += f"\n\n📦 NODE.JS PROJECT REQUIREMENTS:"
                            system_prompt += f"\n- MUST create package.json"
                            system_prompt += f"\n- MUST create index.js or server.js"
                            system_prompt += f"\n- MUST create complete project structure"
                            system_prompt += f"\n- Create ALL files in ONE response using multiple ```create-file: blocks"
                    
                    system_prompt += "\n\nMANDATORY RULES - FOLLOW EXACTLY:"
                    system_prompt += "\n1. ALWAYS use ```create-file: (three backticks + create-file:)"
                    system_prompt += "\n2. NEVER use ```bash, ```sh, or any other language tag for file actions"
                    system_prompt += "\n3. NEVER write 'create-file:' as plain text or in explanations"
                    system_prompt += "\n4. START your response IMMEDIATELY with ```create-file: blocks - NO explanations first"
                    system_prompt += "\n5. DO NOT write 'Vamos criar...' or any introduction before create-file blocks"
                    system_prompt += "\n6. You can add explanations AFTER all create-file blocks are done"
                    system_prompt += "\n\nEXAMPLE CORRECT FORMAT:"
                    system_prompt += "\n```create-file:teste.txt"
                    system_prompt += "\nHello World"
                    system_prompt += "\n```"
                    system_prompt += "\n\nEXAMPLE WRONG FORMAT (DO NOT DO THIS):"
                    system_prompt += "\n\"Vamos criar o arquivo...\" [WRONG - explanation first]"
                    system_prompt += "\n```bash [WRONG - don't use bash]"
                    system_prompt += "\ncreate-file:teste.txt [WRONG - inside bash block]"
                    system_prompt += "\n\nYou can create MULTIPLE files in ONE response by using multiple ```create-file: blocks."
                    system_prompt += "\n\nThe codebase analysis in the context shows you:"
                    system_prompt += "\n- The complete project structure and file tree"
                    system_prompt += "\n- Where different types of files are located"
                    system_prompt += "\n- Coding patterns, conventions, and style used"
                    system_prompt += "\n- Dependencies and how files are organized"
                    system_prompt += "\n- FULL CONTENT of key files (use these as REFERENCE when creating similar files)"
                    system_prompt += "\n\nWhen creating files, you MUST:"
                    system_prompt += "\n1. ALWAYS use ```create-file:path format (NOT regular code blocks)"
                    system_prompt += "\n2. CRITICAL PATH RULE: If user asks for file WITHOUT directory, create in ROOT (utils.js, NOT src/utils.js)"
                    system_prompt += "\n3. For files INSIDE workspace: Use RELATIVE paths (e.g., src/components/Button.jsx ONLY if user specifies or pattern exists)"
                    system_prompt += "\n4. For files OUTSIDE workspace: Use ABSOLUTE paths (e.g., /Users/username/Desktop/file.txt)"
                    system_prompt += "\n5. When user asks for a 'project' or 'complete application', create ALL files in ONE response"
                    system_prompt += "\n6. Use codebase analysis to understand project structure (for workspace files)"
                    system_prompt += "\n7. Place files in the SAME directories where similar files exist (ONLY if user wants to follow pattern OR explicitly specifies directory)"
                    system_prompt += "\n7. Follow the EXACT naming conventions and patterns used"
                    system_prompt += "\n8. Match the coding style, imports, and structure of existing files"
                    system_prompt += "\n9. NEVER create files randomly - always base on codebase analysis (workspace) or user's explicit request (external)"
                    system_prompt += "\n10. Ensure new files integrate properly with existing code (for workspace files)"
                    system_prompt += "\n11. MAINTAIN context from previous messages - remember files created earlier in the conversation"
                    system_prompt += "\n\nCRITICAL: When user asks to create a file 'based on', 'similar to', 'like', or 'following the pattern of' another file:"
                    system_prompt += "\n- The codebase context shows you similar files with their FULL CONTENT"
                    system_prompt += "\n- Use those files as REFERENCE and TEMPLATE - copy their structure exactly"
                    system_prompt += "\n- Match the EXACT structure, imports, exports, and patterns from the reference files"
                    system_prompt += "\n- Keep the same coding style, naming conventions, and organization"
                    system_prompt += "\n- Adapt the content to the new file's purpose while maintaining consistency"
                    system_prompt += "\n- Example: If you see 'Button.jsx' in context and user asks for 'Card.jsx', use Button.jsx as the template"
                    system_prompt += "\n\nCRITICAL: CONTEXT RETENTION:"
                    system_prompt += "\n- Remember ALL files created in previous messages in this conversation"
                    system_prompt += "\n- When user refers to 'that file' or 'the file we created', remember which file they mean"
                    system_prompt += "\n- Maintain full conversation context - you have access to all previous messages"
                    system_prompt += "\n- When modifying files, reference the file by its path from previous context"
            
            if intent:
                system_prompt += f"\n\n=== DETECTED INTENT ===\n{intent}"
        
        # === 9. SELECT MODEL (Required - no auto selection) ===
        model = request.model
        if model is None or model == "":
            raise HTTPException(
                status_code=400,
                detail="Model is required. Please specify a model name."
            )
        
        logger.info(
            f"Generating with model: {model}, category: {classification.category.value}",
            workspace_path=workspace_path,
            context={"model": model, "category": classification.category.value}
        )
        
        # === 10. ADJUST TEMPERATURE FOR FILE CREATION ===
        # Lower temperature for file creation tasks to ensure consistent format
        # BUT: Don't adjust if user wants to READ a file
        adjusted_temperature = request.temperature
        if not read_file_intent and classification.is_code_related and any(keyword in request.prompt.lower() for keyword in ['criar', 'create', 'arquivo', 'file', 'projeto', 'project']):
            # Use lower temperature for file creation (more deterministic)
            adjusted_temperature = min(request.temperature, 0.3)
            logger.debug(
                f"Adjusted temperature to {adjusted_temperature} for file creation task",
                workspace_path=workspace_path,
                context={"original_temperature": request.temperature, "adjusted_temperature": adjusted_temperature}
            )
        
        # === 11. GENERATE RESPONSE ===
        result = await ollama.generate(
            prompt=request.prompt,
            model=model,
            system_prompt=system_prompt,
            context=full_context,
            temperature=adjusted_temperature,
            max_tokens=request.max_tokens,
            auto_select_model=False  # We already selected
        )
        
        # === 11.5. INITIALIZE RESPONSE CONTENT SAFELY ===
        # Initialize response_content safely before using it
        if not result or not hasattr(result, 'response') or not result.response:
            logger.error(
                "Invalid response from Ollama",
                workspace_path=workspace_path,
                context={"result": str(result) if result else "None"}
            )
            response_content = "I apologize, but I encountered an error generating a response. Please try again."
        else:
            response_content = result.response
        
        # === 12. VALIDATE AND PROCESS AGENT ACTIONS ===
        # CRITICAL: If user wanted to READ a file, don't process create-file actions
        if read_file_intent:
            logger.info(
                "File reading intent detected - skipping action processing",
                workspace_path=workspace_path,
                file_path=file_to_read
            )
            # Remove any create-file actions that might have been generated incorrectly
            if 'create-file:' in response_content:
                logger.warning(
                    "AI generated create-file for a READ request. Removing it.",
                    workspace_path=workspace_path,
                    file_path=file_to_read
                )
                # Remove create-file blocks
                response_content = re.sub(r'```create-file:[^\n]+\n[\s\S]*?```', '', response_content)
                response_content = re.sub(r'create-file:[^\n]+', '', response_content)
        
        original_response = response_content  # Save original for analysis
        actions_processed = False
        actions_result = None
        
        # Check if response contains agent actions (create-file, modify-file, run-command, delete-file, delete-directory)
        if any(action in response_content for action in ['create-file:', 'modify-file:', 'delete-file:', 'delete-directory:', 'run-command']):
            # Validate format before processing
            has_correct_format = '```create-file:' in original_response or '```modify-file:' in original_response
            has_wrong_format = ('```bash' in original_response or '```sh' in original_response) and 'create-file:' in original_response
            has_text_before = original_response.strip().startswith(('Vamos', 'Vou', 'Let', 'I will', 'Criando', 'Creating'))
            
            logger.debug(
                "Format validation",
                workspace_path=workspace_path,
                context={
                    "has_correct_format": has_correct_format,
                    "has_wrong_format": has_wrong_format,
                    "has_text_before": has_text_before
                }
            )
            
            if has_wrong_format or (has_text_before and not has_correct_format):
                logger.warning(
                    "AI used incorrect format. Attempting to process anyway...",
                    workspace_path=workspace_path,
                    context={"has_wrong_format": has_wrong_format, "has_text_before": has_text_before}
                )
            
            from services.action_processor import get_action_processor
            processor = get_action_processor(ollama_service=ollama)
            actions_result = await processor.process_actions(
                response_content,
                workspace_path
            )
            response_content = actions_result['processed_text']
            actions_processed = True
            logger.info(
                f"Processed {actions_result['total_actions']} actions: {actions_result['success_count']} success, {actions_result['error_count']} errors",
                workspace_path=workspace_path,
                context={
                    "total_actions": actions_result['total_actions'],
                    "success_count": actions_result['success_count'],
                    "error_count": actions_result['error_count']
                }
            )
        
            # If format was wrong but we still processed, log for improvement
            if has_wrong_format and actions_result.get('success_count', 0) == 0:
                logger.error(
                    "Wrong format prevented action processing. Consider improving prompt.",
                    workspace_path=workspace_path,
                    context={"has_wrong_format": has_wrong_format, "success_count": actions_result.get('success_count', 0)}
                )
        
        # === 13. RECORD USAGE FOR LEARNING ===
        response_time = time.time() - start_time
        user_prefs.record_model_usage(
            model=result.model,
            success=True,
            tokens=result.eval_count or 0,
            response_time=response_time,
            category=classification.category.value
        )
        
        # Record detected languages
        for lang in classification.keywords_found:
            if lang in ('python', 'javascript', 'typescript', 'kotlin', 'java', 'go', 'rust'):
                user_prefs.record_language_detected(lang)
        
        # Add refresh flag if actions were processed successfully
        refresh_explorer = False
        if actions_processed and actions_result:
            if actions_result.get('success_count', 0) > 0:
                refresh_explorer = True
        
        return {
            "response": response_content,
            "original_response": original_response if actions_processed else None,  # Include original for analysis
            "model": result.model,
            "done": result.done,
            "total_duration": result.total_duration,
            "eval_count": result.eval_count,
            "response_time_ms": int(response_time * 1000),
            "classification": {
                "category": classification.category.value,
                "confidence": classification.confidence,
                "is_code_related": classification.is_code_related,
                "reasoning": classification.reasoning,
                "intent": intent
            },
            "context_info": {
                "workspace_path": workspace_path,
                "context_length": len(full_context) if full_context else 0,
                "has_codebase_context": workspace_path is not None and request.include_codebase
            },
            "actions_processed": actions_processed,
            "actions_result": actions_result,
            "refresh_explorer": refresh_explorer
        }
        
    except Exception as e:
        # Record failure for learning
        if request.model:
            user_prefs.record_model_usage(
                model=request.model,
                success=False,
                category="error"
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
@rate_limit_decorator("30/minute")  # Chat endpoint - moderate limit
async def chat(
    request: ChatRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Chat completion endpoint with intelligent context.
    
    Features:
    - Automatic codebase analysis
    - Conversation history handling
    - Smart model selection
    - Streaming support
    """
    logger = get_logger()
    
    try:
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
        
        # === DETECT FILE INTENT USING AI ===
        read_file_intent = False
        file_to_read = None
        file_content_context = None
        
        # Get workspace path first
        # CRITICAL: Always use explorer path if request.workspace_path is not provided
        workspace_path = request.workspace_path
        if not workspace_path:
            project_context = workspace.get_project_context()
            if project_context.get("has_workspace"):
                workspace_path = project_context.get("root_path")
                logger.info(
                    f"Using explorer path: {workspace_path}",
                    workspace_path=workspace_path
                )
            else:
                # Try to get current workspace state
                workspace_state = workspace.get_current()
                if workspace_state and workspace_state.path:
                    workspace_path = workspace_state.path
                    logger.info(
                        f"Using workspace state path: {workspace_path}",
                        workspace_path=workspace_path
                    )
        
        logger.info(
            f"Workspace path for chat: {workspace_path}",
            workspace_path=workspace_path,
            context={"request_workspace": request.workspace_path, "final_workspace": workspace_path}
        )
        
        # Use AI-powered intent detection instead of hardcoded patterns
        from services.intent_detector import get_intent_detector
        intent_detector = get_intent_detector(ollama)
        
        try:
            intent_result = await intent_detector.detect_file_intent(
                last_user_message,
                workspace_path
            )
            
            logger.debug(
                f"AI Intent Detection: {intent_result}",
                workspace_path=workspace_path,
                context={"intent_result": intent_result}
            )
            
            if intent_result["intent"] == "read":
                read_file_intent = True
                file_to_read = intent_result.get("file_name")
                if file_to_read:
                    file_to_read = file_to_read.strip('.,!?;:')
                logger.info(
                    f"Detected READ intent for file: {file_to_read}",
                    workspace_path=workspace_path,
                    file_path=file_to_read,
                    context={"confidence": intent_result.get('confidence', 0.0)}
                )
        except Exception as e:
            logger.error(
                f"Error in AI intent detection: {e}",
                workspace_path=workspace_path,
                context={"error": str(e)}
            )
            # Fallback: don't set read_file_intent if AI detection fails
            
        # === READ FILE IF REQUESTED ===
        if read_file_intent and file_to_read and workspace_path:
            try:
                file_service = FileService()
                
                logger.info(
                    f"Detected file reading intent for: '{file_to_read}'",
                    workspace_path=workspace_path,
                    file_path=file_to_read
                )
                
                workspace_path_obj = Path(workspace_path)
                possible_paths = []
                
                # 1. Direct match
                possible_paths.append(workspace_path_obj / file_to_read)
                
                # 2. Add extensions if no extension
                if '.' not in file_to_read:
                    for ext in ['.txt', '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.kt', '.go', '.rs', '.rb', '.json', '.html', '.css', '.md']:
                        possible_paths.append(workspace_path_obj / f"{file_to_read}{ext}")
                
                # 3. Full path check
                if '/' in file_to_read or file_to_read.startswith('/'):
                    possible_paths.insert(0, Path(file_to_read))
                
                file_found = None
                for path in possible_paths:
                    try:
                        if path.exists() and path.is_file():
                            file_found = path
                            logger.info(
                                f"Found file at: {file_found}",
                                workspace_path=workspace_path,
                                file_path=str(file_found)
                            )
                            break
                    except Exception:
                        continue
                
                if file_found:
                    try:
                        file_content = file_service.read_file(str(file_found))
                        file_content_context = f"\n\n=== FILE CONTENT: {file_found.name} ===\n{file_content.content}\n=== END OF FILE ===\n"
                        logger.info(
                            f"Successfully read file {file_found}",
                            workspace_path=workspace_path,
                            file_path=str(file_found),
                            context={"content_length": len(file_content.content)}
                        )
                    except Exception as e:
                        logger.error(
                            f"Error reading file {file_found}: {e}",
                            workspace_path=workspace_path,
                            file_path=str(file_found),
                            context={"error": str(e)}
                        )
                else:
                    # Search in workspace tree using get_file_tree
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
                            file_content_context = f"\n\n=== FILE CONTENT: {Path(file_path).name} ===\n{file_content.content}\n=== END OF FILE ===\n"
                            logger.info(
                                f"Found and read file {file_path} via tree search",
                                workspace_path=workspace_path,
                                file_path=file_path
                            )
                        else:
                            logger.warning(
                                f"File '{file_to_read}' not found in workspace",
                                workspace_path=workspace_path,
                                file_path=file_to_read
                            )
                            # Even if not found, read_file_intent is already True, so system will know it's a read request
                    except Exception as e:
                        logger.error(
                            f"Error searching for file in tree: {e}",
                            workspace_path=workspace_path,
                            file_path=file_to_read,
                            context={"error": str(e)}
                        )
            except Exception as e:
                logger.error(
                    f"Error in file reading: {e}",
                    workspace_path=workspace_path,
                    file_path=file_to_read,
                    context={"error": str(e)}
                )
        
        # Build context with codebase if workspace provided
        context_parts = []
        
        # Add file content FIRST if file was read
        if file_content_context:
            context_parts.append(file_content_context)
        
        # Detect if user is asking about listing/counting files
        list_files_intent = False
        list_keywords = [
            'quantos arquivos', 'how many files', 
            'listar arquivos', 'list files', 
            'arquivos no codebase', 'files in codebase', 
            'todos os arquivos', 'all files',
            'diga cada arquivo', 'tell me each file', 
            'nome e tipo', 'name and type',
            'quantos arquivos voce ve', 'quantos arquivos você vê',
            'quantos arquivos voce ve?', 'quantos arquivos você vê?',
            'quantos arquivos vc ve', 'quantos arquivos vc vê',
            'arquivos que voce ve', 'arquivos que você vê',
            'arquivos que vc ve', 'arquivos que vc vê',
            'voce ve arquivos', 'você vê arquivos',
            'vc ve arquivos', 'vc vê arquivos'
        ]
        message_lower = last_user_message.lower()
        if any(keyword in message_lower for keyword in list_keywords):
            list_files_intent = True
            logger.info(
                "Detected file listing intent",
                workspace_path=workspace_path,
                context={"message": last_user_message, "detected_keywords": [k for k in list_keywords if k in message_lower]}
            )
        
        if workspace_path:
            # If user wants to list files, get file tree
            if list_files_intent:
                try:
                    from services.workspace_service import get_workspace_service
                    ws_service = get_workspace_service()
                    file_tree = ws_service.get_file_tree(workspace_path, max_depth=10)
                    
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
                    
                    all_files = collect_files(file_tree)
                    file_count = len(all_files)
                    
                    files_list_text = f"\n=== FILE LISTING FOR WORKSPACE: {workspace_path} ===\n"
                    files_list_text += f"Total files: {file_count}\n\n"
                    files_list_text += "Files in codebase:\n"
                    for f in all_files[:200]:  # Limit to 200 files to avoid token overflow
                        files_list_text += f"- {f['path']} (type: {f['type']})\n"
                    if len(all_files) > 200:
                        files_list_text += f"\n... and {len(all_files) - 200} more files\n"
                    files_list_text += "=== END OF FILE LISTING ===\n"
                    
                    context_parts.insert(0, files_list_text)  # Add at beginning for priority
                    logger.info(
                        f"Added file listing context: {file_count} files",
                        workspace_path=workspace_path,
                        context={"file_count": file_count}
                    )
                except Exception as e:
                    logger.error(
                        f"Error generating file list: {e}",
                        workspace_path=workspace_path,
                        context={"error": str(e)}
                    )
            
            try:
                # CRITICAL: Always use workspace_path (which is explorer path) for codebase analysis
                # Pass last user message as query for relevance scoring
                # Force refresh for chat so workspace edits are reflected immediately in context.
                codebase_context = get_codebase_context(workspace_path, force_refresh=True, query=last_user_message, ollama_service=ollama)
                context_parts.append(codebase_context)
                logger.info(
                    f"Loaded codebase context: {len(codebase_context)} chars",
                    workspace_path=workspace_path,
                    context={"context_length": len(codebase_context)}
                )
            except Exception as e:
                logger.error(
                    f"Codebase analysis error: {e}",
                    workspace_path=workspace_path,
                    context={"error": str(e)}
                )
                pass
        
        # Build system prompt
        if not system_prompt:
            base_system = ollama.CODE_SYSTEM_PROMPT if classification.is_code_related else ollama.GENERAL_SYSTEM_PROMPT
            system_prompt = f"{base_system}\n\n{classification.system_prompt_modifier}"
            
            # === AGENT MODE: Add system information ===
            # In Agent mode, provide system/machine information for local context
            # This allows the AI to answer questions about the user's machine, OS, hardware, etc.
            try:
                from services.system_info import get_system_info_service
                system_info_service = get_system_info_service()
                system_info_text = system_info_service.get_formatted_prompt()
                
                system_prompt += "\n\n=== AGENT MODE: LOCAL MACHINE ACCESS ==="
                system_prompt += f"\n{system_info_text}"
                system_prompt += "\n\nCRITICAL: You have DIRECT ACCESS to the user's local machine information above."
                system_prompt += "\nYou CAN and SHOULD answer questions about:"
                system_prompt += "\n- Operating system and version"
                system_prompt += "\n- CPU and hardware specifications"
                system_prompt += "\n- Memory/RAM information"
                system_prompt += "\n- User name and home directory"
                system_prompt += "\n- Hostname and system details"
                system_prompt += "\n- Any other system/machine-related questions"
                system_prompt += "\n\nDO NOT say you cannot see or access this information - YOU HAVE IT!"
                system_prompt += "\nAnswer in the SAME LANGUAGE the user wrote (Portuguese/English)."
                
                logger.info(
                    "Added system information to Agent mode prompt",
                    workspace_path=workspace_path
                )
            except Exception as e:
                logger.warning(
                    f"Could not add system information: {e}",
                    workspace_path=workspace_path,
                    context={"error": str(e)}
                )
            
            # Add file listing instructions if user asked about files
            if list_files_intent:
                system_prompt += "\n\n=== FILE LISTING REQUEST DETECTED ==="
                system_prompt += "\nThe user wants to know about files in the codebase."
                system_prompt += "\nA complete file listing has been provided in the context above."
                system_prompt += "\nCRITICAL: You MUST use that information to answer the user's question accurately."
                system_prompt += "\nDO NOT say you cannot see files - you have access to the file listing in the context!"
                system_prompt += "\nList each file with its name and type/extension."
                system_prompt += "\nAnswer in the SAME LANGUAGE the user wrote (Portuguese/English)."
                if workspace_path:
                    system_prompt += f"\nWorkspace path: {workspace_path}"
            
            if workspace_path:
                # CRITICAL: Distinguish between READ and CREATE file intents
                if read_file_intent and file_content_context:
                    system_prompt += "\n\n=== FILE READING DETECTED ==="
                    system_prompt += f"\nThe user wants to READ the file '{file_to_read}', NOT create it."
                    system_prompt += "\nThe file content is provided in the context above."
                    system_prompt += "\nDO NOT use create-file: format. Simply explain what is written in the file."
                    system_prompt += "\nAnswer in the SAME LANGUAGE the user wrote (Portuguese/English)."
                    system_prompt += "\nIf the file content is empty or the file doesn't exist, say so clearly."
                elif read_file_intent and not file_content_context:
                    system_prompt += "\n\n=== FILE READING DETECTED (FILE NOT FOUND) ==="
                    system_prompt += f"\nThe user wants to READ the file '{file_to_read}', but the file was not found."
                    system_prompt += "\nDO NOT try to create the file. Simply inform the user that the file was not found."
                    system_prompt += "\nAnswer in the SAME LANGUAGE the user wrote (Portuguese/English)."
                else:
                    # Normal file creation instructions
                    from services.path_intelligence import PathIntelligence
                    from services.project_detector import get_project_detector
                    
                    # Detect if user wants external project
                    is_external, external_path = PathIntelligence.detect_external_project_intention(
                        last_user_message, workspace_path
                    )
                    
                    # Detect if user wants to create a project that needs its own directory
                    project_detector = get_project_detector(ollama)
                    project_intention = await project_detector.detect_project_intention(
                        last_user_message, workspace_path
                    )
                    
                    system_prompt += f"\n\nActive workspace: {workspace_path}"
                    
                    if project_intention.get("needs_directory", False):
                        project_name = project_intention.get("project_name", "new-project")
                        project_type = project_intention.get("project_type", "general")
                        
                        system_prompt += f"\n\n🎯 PROJECT CREATION DETECTED: User wants to create a {project_type} project."
                        system_prompt += f"\nCRITICAL: You MUST create a directory for this project FIRST."
                        system_prompt += f"\n1. FIRST create the project directory: ```create-directory:{project_name}```"
                        system_prompt += f"\n2. THEN create ALL files INSIDE this directory: ```create-file:{project_name}/package.json```"
                        system_prompt += f"\n3. ALL files must be created inside {project_name}/ directory"
                        system_prompt += f"\n4. Example: ```create-file:{project_name}/src/index.js``` NOT ```create-file:src/index.js```"
                        system_prompt += f"\n5. This keeps the project isolated and organized"
                        
                        # Add project-type-specific instructions
                        if project_type == "android":
                            system_prompt += f"\n\n📱 ANDROID PROJECT REQUIREMENTS:"
                            system_prompt += f"\n- MUST create build.gradle (project level)"
                            system_prompt += f"\n- MUST create settings.gradle"
                            system_prompt += f"\n- MUST create app/build.gradle"
                            system_prompt += f"\n- MUST create app/src/main/AndroidManifest.xml"
                            system_prompt += f"\n- MUST create Kotlin/Java source files in app/src/main/java/"
                            system_prompt += f"\n- MUST create MainActivity.kt or MainActivity.java"
                            system_prompt += f"\n- If API mock requested: MUST create API service/mock files"
                            system_prompt += f"\n- Create ALL files in ONE response using multiple ```create-file: blocks"
                        
                        elif project_type == "react":
                            system_prompt += f"\n\n⚛️ REACT PROJECT REQUIREMENTS:"
                            system_prompt += f"\n- MUST create package.json with React dependencies"
                            system_prompt += f"\n- MUST create public/index.html"
                            system_prompt += f"\n- MUST create src/index.js or src/index.jsx"
                            system_prompt += f"\n- MUST create src/App.jsx or src/App.js"
                            system_prompt += f"\n- MUST create React components (JSX/TSX files)"
                            system_prompt += f"\n- Create ALL files in ONE response using multiple ```create-file: blocks"
                        
                        elif project_type == "node":
                            system_prompt += f"\n\n📦 NODE.JS PROJECT REQUIREMENTS:"
                            system_prompt += f"\n- MUST create package.json"
                            system_prompt += f"\n- MUST create index.js or server.js"
                            system_prompt += f"\n- MUST create complete project structure"
                            system_prompt += f"\n- Create ALL files in ONE response using multiple ```create-file: blocks"
                    
                    if is_external and external_path:
                        system_prompt += f"\n\n⚠️ EXTERNAL PROJECT DETECTED: User wants to create project outside workspace."
                        system_prompt += f"\nSuggested path: {external_path}"
                        system_prompt += f"\nUse ABSOLUTE paths for all files in this project."
                    
                    system_prompt += "\nRefer to codebase analysis when answering about 'this project'."
                    system_prompt += "\n\nCRITICAL FILE FORMAT RULES:"
                    system_prompt += "\n- ALWAYS use ```create-file: (three backticks + create-file:)"
                    system_prompt += "\n- NEVER use ```bash, ```sh, or any other language tag for file actions"
                    system_prompt += "\n- START your response DIRECTLY with ```create-file: blocks when creating files"
                    system_prompt += "\n- DELETE FILES: Use ```delete-file:path or ```delete-directory:path format."
        
        # Add context to prompt
        full_prompt = ""
        if context_parts:
            full_prompt = "\n\n".join(context_parts) + "\n\n---\n\n"
        full_prompt += "\n".join(prompt_parts) + "\nAssistant:"
        
        # Select model (required - no auto selection)
        model = request.model
        if model is None or model == "":
            raise HTTPException(
                status_code=400,
                detail="Model is required. Please specify a model name."
            )
        
        if request.stream:
            async def stream_generator():
                async for token in ollama.generate_stream(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=request.temperature
                ):
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        
        result = await ollama.generate(
            prompt=full_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=request.temperature,
            auto_select_model=False
        )
        
        # Process agent actions if in agent mode (detected by presence of create-file, modify-file, etc)
        # Initialize response_content safely
        if not result or not hasattr(result, 'response') or not result.response:
            logger.error(
                "Invalid response from Ollama",
                workspace_path=workspace_path,
                context={"result": str(result) if result else "None"}
            )
            response_content = "I apologize, but I encountered an error generating a response. Please try again."
        else:
            response_content = result.response
        
        actions_processed = False
        actions_result = None
        
        # CRITICAL: If user wanted to READ a file, don't process create-file actions
        if read_file_intent:
            logger.info(
                "File reading intent detected - skipping action processing",
                workspace_path=workspace_path,
                file_path=file_to_read
            )
            # Remove any create-file actions that might have been generated incorrectly
            if 'create-file:' in response_content:
                logger.warning(
                    "AI generated create-file for a READ request. Removing it.",
                    workspace_path=workspace_path,
                    file_path=file_to_read
                )
                response_content = re.sub(r'```create-file:[^\n]+\n[\s\S]*?```', '', response_content)
                response_content = re.sub(r'create-file:[^\n]+', '', response_content)
        else:
            # Check if response contains agent actions
            if any(action in response_content for action in ['create-file:', 'modify-file:', 'delete-file:', 'delete-directory:', 'run-command']):
                from services.action_processor import get_action_processor
                processor = get_action_processor(ollama_service=ollama)
                actions_result = await processor.process_actions(
                    response_content,
                    workspace_path
                )
                response_content = actions_result['processed_text']
                actions_processed = True
        
        # Add refresh flag if actions were processed successfully
        refresh_explorer = False
        if actions_processed and actions_result:
            if actions_result.get('success_count', 0) > 0:
                refresh_explorer = True
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_content
                }
            }],
            "model": model,
            "usage": result.usage if hasattr(result, 'usage') else {},
            "actions_result": actions_result if actions_processed else None,
            "actions_processed": actions_processed,
            "refresh_explorer": refresh_explorer,
            "classification": {
                "category": classification.category.value,
                "is_code_related": classification.is_code_related
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stream")
async def generate_stream(
    request: GenerateRequest,
    ollama: OllamaService = Depends(get_ollama_service)
) -> StreamingResponse:
    """Stream code generation token by token."""
    
    async def stream_generator():
        async for token in ollama.generate_stream(
            prompt=request.prompt,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )


@router.post("/recommend-model")
async def recommend_model(
    prompt: str,
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Get recommended model for a given prompt.
    Uses intelligent classification to suggest the best model.
    """
    try:
        models = await ollama.list_models()
        classification = classify_prompt(prompt, models)
        
        return {
            "recommended_model": classification.recommended_model,
            "is_code_related": classification.is_code_related,
            "category": classification.category.value,
            "confidence": classification.confidence,
            "reason": classification.reasoning,
            "keywords_found": classification.keywords_found
        }
    except Exception as e:
        return {
            "recommended_model": "qwen2.5-coder:14b",
            "is_code_related": True,
            "reason": f"Error: {str(e)}, using default",
            "category": "code_generation"
        }


@router.post("/analyze-codebase")
async def analyze_codebase_endpoint(
    request: AnalyzeCodebaseRequest
) -> Dict[str, Any]:
    """
    Analyze a codebase and return structured information.
    
    Returns:
    - File tree
    - Languages detected
    - Entry points
    - Dependencies
    - Key files with content
    """
    try:
        import os
        path = os.path.expanduser(request.path)
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        # Try to get ollama service for AI-powered analysis
        try:
            from services.ollama_service import get_ollama_service
            ollama_service = get_ollama_service()
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/codebase-context")
async def get_codebase_context_endpoint(
    path: str,
    refresh: bool = False
) -> Dict[str, Any]:
    """
    Get AI-ready context for a codebase.
    Uses caching for performance.
    """
    try:
        import os
        expanded_path = os.path.expanduser(path)
        
        if not os.path.exists(expanded_path):
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        # Try to get ollama service
        try:
            from services.ollama_service import get_ollama_service
            ollama_service = get_ollama_service()
        except:
            ollama_service = None
        
        context = get_codebase_context(expanded_path, force_refresh=refresh, ollama_service=ollama_service)
        
        return {
            "path": path,
            "context": context,
            "length": len(context),
            "cached": not refresh
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

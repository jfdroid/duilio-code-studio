"""
Chat Routes
===========
AI code generation and chat endpoints.
Includes intelligent codebase analysis, smart model selection,
user preference learning, and few-shot example matching.
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from services.ollama_service import OllamaService, get_ollama_service
from services.workspace_service import WorkspaceService, get_workspace_service
from services.codebase_analyzer import CodebaseAnalyzer, analyze_codebase
from services.prompt_classifier import PromptClassifier, classify_prompt
from services.user_preferences import UserPreferencesService, get_user_preferences_service
from services.prompt_examples import PromptExamplesService, get_prompt_examples_service


router = APIRouter(prefix="/api", tags=["Chat"])


# === Request Models ===

class GenerateRequest(BaseModel):
    """Request for code/text generation."""
    prompt: str = Field(..., description="The prompt")
    model: Optional[str] = Field(default=None, description="Model to use (None for auto-selection)")
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    workspace_path: Optional[str] = Field(default=None, description="Path to analyze for context")
    include_codebase: bool = Field(default=True, description="Include codebase analysis in context")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: list = Field(..., description="Message history")
    model: Optional[str] = Field(default=None, description="Model to use (None for auto)")
    workspace_path: Optional[str] = Field(default=None, description="Workspace path for context")
    temperature: float = Field(default=0.7)
    stream: bool = Field(default=False)


class AnalyzeCodebaseRequest(BaseModel):
    """Request to analyze a codebase."""
    path: str = Field(..., description="Path to the codebase")
    max_files: int = Field(default=100, description="Maximum files to analyze")


# === Codebase Context Cache ===
_codebase_cache: Dict[str, str] = {}


def get_codebase_context(path: str, force_refresh: bool = False) -> str:
    """Get or generate codebase context with caching."""
    global _codebase_cache
    
    if not force_refresh and path in _codebase_cache:
        return _codebase_cache[path]
    
    try:
        context = analyze_codebase(path, max_files=50)
        _codebase_cache[path] = context
        return context
    except Exception as e:
        return f"[Error analyzing codebase: {str(e)}]"


# === Endpoints ===

@router.post("/generate")
async def generate(
    request: GenerateRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    workspace: WorkspaceService = Depends(get_workspace_service),
    user_prefs: UserPreferencesService = Depends(get_user_preferences_service),
    examples: PromptExamplesService = Depends(get_prompt_examples_service)
) -> Dict[str, Any]:
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
        
        # === 3. BUILD COMPREHENSIVE CONTEXT ===
        context_parts = []
        
        # Add user-provided context
        if request.context:
            context_parts.append(request.context)
        
        # Get workspace info
        workspace_path = request.workspace_path
        project_context = workspace.get_project_context()
        
        if not workspace_path and project_context.get("has_workspace"):
            workspace_path = project_context.get("root_path")
        
        # === 4. ANALYZE CODEBASE (THE KEY FEATURE!) ===
        if workspace_path and request.include_codebase:
            try:
                codebase_context = get_codebase_context(workspace_path)
                context_parts.append(codebase_context)
                print(f"[DuilioCode] Loaded codebase context: {len(codebase_context)} chars from {workspace_path}")
            except Exception as e:
                print(f"[DuilioCode] Codebase analysis error: {e}")
                context_parts.append(f"[Workspace: {workspace_path}]")
        
        # === 5. ADD FEW-SHOT EXAMPLES ===
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
        
        # === 6. BUILD ENHANCED SYSTEM PROMPT ===
        system_prompt = request.system_prompt
        if not system_prompt:
            base_system = ollama.CODE_SYSTEM_PROMPT if classification.is_code_related else ollama.GENERAL_SYSTEM_PROMPT
            system_prompt = f"{base_system}\n\n{classification.system_prompt_modifier}"
            
            if workspace_path:
                system_prompt += f"\n\n=== IMPORTANT WORKSPACE CONTEXT ==="
                system_prompt += f"\nThe user has opened workspace: {workspace_path}"
                system_prompt += "\nWhen they ask about 'this codebase', 'this project', 'esse codigo', 'esse projeto', or 'the code', you MUST refer to the workspace analysis provided in the context."
                system_prompt += "\nYou KNOW this codebase - analyze it, explain it, help them work with it!"
            
            if intent:
                system_prompt += f"\n\n=== DETECTED INTENT ===\n{intent}"
        
        # === 7. SELECT MODEL (Smart Selection) ===
        model = request.model
        if model is None:
            # Prefer user's learned preference, then classification
            model = preferred_model or classification.recommended_model
        
        print(f"[DuilioCode] Generating with model: {model}, category: {classification.category.value}")
        
        # === 8. GENERATE RESPONSE ===
        result = await ollama.generate(
            prompt=request.prompt,
            model=model,
            system_prompt=system_prompt,
            context=full_context,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            auto_select_model=False  # We already selected
        )
        
        # === 9. RECORD USAGE FOR LEARNING ===
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
        
        return {
            "response": result.response,
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
            }
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
        
        # Build context with codebase if workspace provided
        context_parts = []
        
        workspace_path = request.workspace_path
        if not workspace_path:
            project_context = workspace.get_project_context()
            if project_context.get("has_workspace"):
                workspace_path = project_context.get("root_path")
        
        if workspace_path:
            try:
                codebase_context = get_codebase_context(workspace_path)
                context_parts.append(codebase_context)
            except:
                pass
        
        # Build system prompt
        if not system_prompt:
            base_system = ollama.CODE_SYSTEM_PROMPT if classification.is_code_related else ollama.GENERAL_SYSTEM_PROMPT
            system_prompt = f"{base_system}\n\n{classification.system_prompt_modifier}"
            
            if workspace_path:
                system_prompt += f"\n\nActive workspace: {workspace_path}"
                system_prompt += "\nRefer to the codebase analysis when answering questions about 'this project' or 'the code'."
        
        # Add context to prompt
        full_prompt = ""
        if context_parts:
            full_prompt = "\n\n".join(context_parts) + "\n\n---\n\n"
        full_prompt += "\n".join(prompt_parts) + "\nAssistant:"
        
        # Select model
        model = request.model
        if model is None:
            model = classification.recommended_model
        
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
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": result.response
                }
            }],
            "model": result.model,
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
        
        analyzer = CodebaseAnalyzer(path)
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
        
        context = get_codebase_context(expanded_path, force_refresh=refresh)
        
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

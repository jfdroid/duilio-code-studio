"""
Tools Routes
============
API endpoints for advanced developer tools:
- Git operations
- Code execution
- Project scaffolding
- Refactoring
- Documentation
- Security scanning
- Agent mode
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from services.git_service import GitService, get_git_service
from services.code_executor import CodeExecutor, get_code_executor
from services.project_scaffolding import ProjectScaffolder, get_project_scaffolder
from services.refactoring_service import RefactoringService, get_refactoring_service
from services.documentation_generator import DocumentationGenerator, get_documentation_generator
from services.security_scanner import SecurityScanner, get_security_scanner
from services.agent_service import AgentService, create_agent
from services.rag_service import RAGService, get_rag_service
from services.workspace_service import WorkspaceService, get_workspace_service
from services.ollama_service import OllamaService, get_ollama_service
from services.file_service import FileService, get_file_service

# Rate limiting (optional)
try:
    from middleware.rate_limiter import rate_limit_decorator
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    def rate_limit_decorator(limit: str = None):
        def decorator(func):
            return func
        return decorator

router = APIRouter(prefix="/api/tools", tags=["Tools"])


# === Request Models ===

class GitCommandRequest(BaseModel):
    """Request for git commands."""
    command: str = Field(..., description="Git command or natural language")
    path: Optional[str] = None


class ExecuteCodeRequest(BaseModel):
    """Request to execute code."""
    code: str = Field(..., description="Code to execute")
    language: str = Field(default="auto", description="Language (python, javascript, shell, auto)")


class CreateProjectRequest(BaseModel):
    """Request to create a project from template."""
    template_id: str = Field(..., description="Template ID")
    target_path: str = Field(..., description="Where to create the project")
    project_name: str = Field(..., description="Project name")
    project_description: str = Field(default="", description="Project description")
    author: str = Field(default="DuilioCode User", description="Author name")


class RenameSymbolRequest(BaseModel):
    """Request to rename a symbol."""
    old_name: str = Field(..., description="Current name")
    new_name: str = Field(..., description="New name")
    path: Optional[str] = None
    preview: bool = Field(default=True, description="Preview only, don't apply")


class FindReplaceRequest(BaseModel):
    """Request for find and replace."""
    find: str = Field(..., description="Pattern to find")
    replace: str = Field(..., description="Replacement text")
    path: Optional[str] = None
    is_regex: bool = Field(default=False)
    file_pattern: Optional[str] = None
    preview: bool = Field(default=True)


class GenerateReadmeRequest(BaseModel):
    """Request to generate README."""
    project_name: str
    project_description: str
    language: str
    features: List[str] = []
    include_badges: bool = True


class GenerateDocstringRequest(BaseModel):
    """Request to generate docstring."""
    function_name: str
    params: List[tuple] = []
    returns: Optional[str] = None
    description: Optional[str] = None
    style: str = Field(default="google", description="google, numpy, or sphinx")


class AgentTaskRequest(BaseModel):
    """Request for agent to execute a task."""
    description: str = Field(..., description="Task description in natural language")


# === Git Endpoints ===

@router.post("/git/execute")
async def execute_git_command(
    request: GitCommandRequest,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Execute a git command (natural language or direct)."""
    ws = workspace.get_current()
    path = request.path or ws.path
    
    if not path:
        raise HTTPException(status_code=400, detail="No workspace path available")
    
    git = get_git_service(path)
    
    if not git.is_git_repo(path):
        raise HTTPException(status_code=400, detail="Not a git repository")
    
    # Try to execute as natural language
    result = git.execute_natural_command(request.command, path)
    
    return {
        "success": result.success,
        "command": result.command,
        "output": result.output,
        "error": result.error
    }


@router.get("/git/status")
async def get_git_status(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Get git repository status."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    git = get_git_service(ws.path)
    return git.get_repo_info(ws.path)


@router.get("/git/log")
async def get_git_log(
    count: int = 10,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Get recent commits."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    git = get_git_service(ws.path)
    result = git.log(count=count, path=ws.path)
    
    return {
        "success": result.success,
        "log": result.output,
        "error": result.error
    }


# === Code Execution Endpoints ===

@router.post("/execute")
@rate_limit_decorator("10/minute")  # Command execution - strict limit
async def execute_code(request: ExecuteCodeRequest) -> Dict[str, Any]:
    """Execute code in a sandboxed environment."""
    executor = get_code_executor()
    
    if request.language == "auto":
        result = executor.execute_auto(request.code)
    else:
        result = executor.execute(request.code, request.language)
    
    return {
        "success": result.success,
        "language": result.language,
        "output": result.output,
        "error": result.error,
        "execution_time_ms": result.execution_time_ms,
        "timed_out": result.timed_out
    }


# === Project Scaffolding Endpoints ===

@router.get("/scaffolding/templates")
async def list_templates() -> Dict[str, Any]:
    """List available project templates."""
    scaffolder = get_project_scaffolder()
    return {"templates": scaffolder.list_templates()}


@router.post("/scaffolding/create")
async def create_project(request: CreateProjectRequest) -> Dict[str, Any]:
    """Create a new project from template."""
    scaffolder = get_project_scaffolder()
    
    result = scaffolder.create_project(
        template_id=request.template_id,
        target_path=request.target_path,
        project_name=request.project_name,
        project_description=request.project_description,
        author=request.author
    )
    
    return result


# === Refactoring Endpoints ===

@router.post("/refactor/rename")
@rate_limit_decorator("15/minute")  # Refactoring - moderate limit
async def rename_symbol(
    request: RenameSymbolRequest,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Rename a symbol across the codebase."""
    ws = workspace.get_current()
    path = request.path or ws.path
    
    if not path:
        raise HTTPException(status_code=400, detail="No workspace path available")
    
    refactor = get_refactoring_service(path)
    result = refactor.rename_symbol(
        old_name=request.old_name,
        new_name=request.new_name,
        path=path,
        preview=request.preview
    )
    
    return {
        "success": result.success,
        "operation": result.operation,
        "files_modified": result.files_modified,
        "total_changes": result.total_changes,
        "preview_only": result.preview_only,
        "changes": [
            {
                "file": c.file_path,
                "line": c.line_number,
                "old": c.old_text[:100],
                "new": c.new_text[:100]
            }
            for c in result.changes[:50]  # Limit for response size
        ],
        "errors": result.errors
    }


@router.post("/refactor/find-replace")
@rate_limit_decorator("15/minute")  # Refactoring - moderate limit
async def find_and_replace(
    request: FindReplaceRequest,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Find and replace across files."""
    ws = workspace.get_current()
    path = request.path or ws.path
    
    if not path:
        raise HTTPException(status_code=400, detail="No workspace path available")
    
    refactor = get_refactoring_service(path)
    result = refactor.find_and_replace(
        find_pattern=request.find,
        replace_pattern=request.replace,
        path=path,
        is_regex=request.is_regex,
        file_pattern=request.file_pattern,
        preview=request.preview
    )
    
    return {
        "success": result.success,
        "files_modified": result.files_modified,
        "total_changes": result.total_changes,
        "preview_only": result.preview_only,
        "changes": [
            {
                "file": c.file_path,
                "line": c.line_number,
                "old": c.old_text[:100],
                "new": c.new_text[:100]
            }
            for c in result.changes[:50]
        ],
        "errors": result.errors
    }


# === Documentation Endpoints ===

@router.post("/docs/readme")
async def generate_readme(request: GenerateReadmeRequest) -> Dict[str, Any]:
    """Generate a README.md file."""
    generator = get_documentation_generator()
    
    readme = generator.generate_readme(
        project_name=request.project_name,
        project_description=request.project_description,
        language=request.language,
        features=request.features,
        include_badges=request.include_badges
    )
    
    return {"readme": readme}


@router.post("/docs/docstring")
async def generate_docstring(request: GenerateDocstringRequest) -> Dict[str, Any]:
    """Generate a docstring for a function."""
    generator = get_documentation_generator()
    
    docstring = generator.generate_docstring(
        function_name=request.function_name,
        params=request.params,
        returns=request.returns,
        description=request.description,
        style=request.style
    )
    
    return {"docstring": docstring}


@router.post("/docs/license")
async def generate_license(
    license_type: str = "mit",
    author: str = "DuilioCode User"
) -> Dict[str, Any]:
    """Generate a LICENSE file."""
    generator = get_documentation_generator()
    license_content = generator.generate_license(license_type, author)
    return {"license": license_content}


# === Security Scanning Endpoints ===

@router.get("/security/scan")
async def security_scan(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Scan dependencies for vulnerabilities."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    scanner = get_security_scanner(ws.path)
    results = scanner.scan_auto(ws.path)
    
    return {
        "scans": [
            {
                "package_manager": r.package_manager,
                "total_packages": r.total_packages,
                "critical": r.critical_count,
                "high": r.high_count,
                "medium": r.medium_count,
                "low": r.low_count,
                "vulnerabilities": [
                    {
                        "package": v.package,
                        "version": v.version,
                        "severity": v.severity.value,
                        "title": v.title,
                        "cve": v.cve,
                        "fixed_version": v.fixed_version
                    }
                    for v in r.vulnerabilities
                ]
            }
            for r in results
        ]
    }


@router.get("/security/report")
async def security_report(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Get formatted security report."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    scanner = get_security_scanner(ws.path)
    results = scanner.scan_auto(ws.path)
    report = scanner.format_report(results)
    
    return {"report": report}


# === Agent Mode Endpoints ===

# Store running tasks
_running_tasks: Dict[str, Any] = {}


@router.post("/agent/execute")
@rate_limit_decorator("5/minute")  # Agent tasks - very strict limit (expensive)
async def execute_agent_task(
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    workspace: WorkspaceService = Depends(get_workspace_service),
    ollama: OllamaService = Depends(get_ollama_service),
    file_service: FileService = Depends(get_file_service)
) -> Dict[str, Any]:
    """
    Execute a task using the autonomous agent.
    
    The agent will:
    1. Analyze the task
    2. Create an execution plan
    3. Implement the solution
    4. Test and verify
    5. Commit changes
    """
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    # Create agent with services
    git = get_git_service(ws.path)
    executor = get_code_executor()
    
    agent = create_agent(
        workspace_path=ws.path,
        ollama=ollama,
        file=file_service,
        git=git,
        executor=executor
    )
    
    # Execute task
    import asyncio
    task = await agent.execute_task(request.description)
    
    # Store task for status checks
    _running_tasks[task.id] = task
    
    return {
        "task_id": task.id,
        "status": task.status.value,
        "progress": task.progress,
        "summary": agent.get_task_summary(task)
    }


@router.get("/agent/status/{task_id}")
async def get_agent_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of an agent task."""
    if task_id not in _running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _running_tasks[task_id]
    
    return {
        "task_id": task.id,
        "status": task.status.value,
        "progress": task.progress,
        "files_created": task.files_created,
        "files_modified": task.files_modified,
        "error": task.error,
        "steps": [
            {
                "description": s.description,
                "status": s.status,
                "result": s.result[:200] if s.result else None,
                "error": s.error
            }
            for s in task.steps
        ]
    }


@router.post("/agent/cancel/{task_id}")
async def cancel_agent_task(task_id: str) -> Dict[str, Any]:
    """Cancel a running agent task."""
    if task_id not in _running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _running_tasks[task_id]
    # Mark as cancelled (the agent checks this flag)
    task.status = "cancelled"
    
    return {"message": "Task cancellation requested", "task_id": task_id}


# === RAG (Semantic Search) Endpoints ===

class RAGSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, description="Number of results")
    file_filter: Optional[str] = Field(default=None, description="File extension filter")


@router.post("/rag/index")
async def index_codebase(
    force: bool = False,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Index the codebase for semantic search."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    rag = get_rag_service(ws.path)
    stats = rag.index_codebase(ws.path, force=force)
    
    return {
        "success": True,
        "stats": stats
    }


@router.post("/rag/search")
async def semantic_search(
    request: RAGSearchRequest,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Perform semantic search on the codebase."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    rag = get_rag_service(ws.path)
    
    # Ensure indexed
    if not rag._initialized:
        rag.index_codebase(ws.path)
    
    results = rag.search(
        query=request.query,
        top_k=request.top_k,
        file_filter=request.file_filter
    )
    
    return {
        "query": request.query,
        "results": [
            {
                "file": r.document.metadata.get('file_path'),
                "chunk_index": r.document.chunk_index,
                "score": round(r.score, 3),
                "content": r.document.content[:500],
                "highlights": r.highlights
            }
            for r in results
        ]
    }


@router.get("/rag/context")
async def get_rag_context(
    query: str,
    max_tokens: int = 4000,
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Get AI-ready context for a query."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    rag = get_rag_service(ws.path)
    
    # Ensure indexed
    if not rag._initialized:
        rag.index_codebase(ws.path)
    
    context = rag.get_context_for_query(query, max_tokens=max_tokens)
    
    return {
        "query": query,
        "context": context,
        "context_length": len(context)
    }


@router.get("/rag/stats")
async def get_rag_stats(
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """Get RAG index statistics."""
    ws = workspace.get_current()
    if not ws.path:
        raise HTTPException(status_code=400, detail="No workspace open")
    
    rag = get_rag_service(ws.path)
    return rag.get_stats()

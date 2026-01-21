"""
DuilioCode Studio - Main API
Local programming assistant with Ollama + Qwen2.5-Coder
"""

import os
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel


# ============================================================================
# SETTINGS
# ============================================================================

class Settings:
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5-coder:14b")
    FALLBACK_MODEL = "qwen2.5-coder:7b"
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7
    
    # Directories
    BASE_DIR = Path(__file__).parent.parent.parent
    WEB_DIR = BASE_DIR / "web"
    TEMPLATES_DIR = WEB_DIR / "templates"


settings = Settings()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CodeRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    context: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096


class CodeResponse(BaseModel):
    response: str
    model: str
    tokens_used: Optional[int] = None
    time_ms: Optional[int] = None


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    stream: Optional[bool] = False


class FileRequest(BaseModel):
    path: str
    content: Optional[str] = None


class FileResponse(BaseModel):
    path: str
    content: str
    language: str
    size: int


class ModelInfo(BaseModel):
    name: str
    size: str
    description: str
    recommended: bool = False


# ============================================================================
# OLLAMA CLIENT
# ============================================================================

class OllamaClient:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.timeout = 300.0  # 5 minutes for large models
    
    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate a response using the specified model."""
        
        # Build prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"Conversation context:\n{context}\n\nNew question: {prompt}"
        
        # System prompt for code
        if not system_prompt:
            system_prompt = """You are DuilioCode, an expert programming assistant.

Your characteristics:
- Provide clean, well-documented code following best practices
- Explain concepts clearly and didactically
- Suggest performance and security improvements
- Know multiple languages: Python, JavaScript, TypeScript, Kotlin, Java, Go, Rust, C++
- Understand software architecture: Clean Architecture, SOLID, Design Patterns
- Provide practical examples whenever possible

When providing code:
- Use code blocks with the specified language (```python, ```javascript, etc)
- Add explanatory comments
- Indicate possible errors or edge cases"""

        payload = {
            "model": model,
            "prompt": full_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.host}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "response": data.get("response", ""),
                    "model": model,
                    "tokens_used": data.get("eval_count", 0),
                    "time_ms": int(data.get("total_duration", 0) / 1_000_000)
                }
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error connecting to Ollama: {str(e)}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
            except Exception:
                return []
    
    async def check_health(self) -> bool:
        """Check if Ollama is running."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
            except Exception:
                return False


# ============================================================================
# FILE MANAGER
# ============================================================================

class FileManager:
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.kt': 'kotlin',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.md': 'markdown',
        '.sql': 'sql',
        '.dockerfile': 'dockerfile',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
    }
    
    @classmethod
    def get_language(cls, path: str) -> str:
        """Detect language by file extension."""
        ext = Path(path).suffix.lower()
        return cls.LANGUAGE_MAP.get(ext, 'text')
    
    @classmethod
    def read_file(cls, path: str) -> Dict[str, Any]:
        """Read a file and return its content."""
        file_path = Path(path).expanduser()
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return {
                "path": str(file_path),
                "content": content,
                "language": cls.get_language(path),
                "size": len(content)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
    @classmethod
    def write_file(cls, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        file_path = Path(path).expanduser()
        
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup if file exists
            if file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
            
            # Write new content
            file_path.write_text(content, encoding='utf-8')
            
            return {
                "path": str(file_path),
                "content": content,
                "language": cls.get_language(path),
                "size": len(content),
                "saved": True
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    @classmethod
    def list_directory(cls, path: str = ".") -> List[Dict[str, Any]]:
        """List files and folders in a directory."""
        dir_path = Path(path).expanduser()
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
        
        items = []
        try:
            for item in sorted(dir_path.iterdir()):
                # Ignore hidden files and common directories
                if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'venv', '.git']:
                    continue
                
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_directory": item.is_dir(),
                    "language": cls.get_language(item.name) if item.is_file() else None,
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return items
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error listing directory: {str(e)}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="DuilioCode Studio",
    description="Local programming assistant with AI",
    version="1.0.0"
)

# Clients
ollama = OllamaClient()
file_manager = FileManager()


# ============================================================================
# ROUTES - PAGES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Main page."""
    template_path = settings.TEMPLATES_DIR / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>DuilioCode Studio</h1><p>Template not found</p>")


# ============================================================================
# ROUTES - API
# ============================================================================

@app.get("/health")
async def health_check():
    """Check server status."""
    ollama_healthy = await ollama.check_health()
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama": "connected" if ollama_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/models")
async def list_models():
    """List available models."""
    models = await ollama.list_models()
    
    # Filter and enrich information
    code_models = []
    for model in models:
        name = model.get("name", "")
        
        # Filter code models
        if any(kw in name.lower() for kw in ['coder', 'code', 'deepseek', 'starcoder']):
            size_bytes = model.get("size", 0)
            size_gb = round(size_bytes / (1024**3), 1)
            
            code_models.append({
                "name": name,
                "size": f"{size_gb}GB",
                "parameters": model.get("details", {}).get("parameter_size", ""),
                "recommended": "qwen2.5-coder:14b" in name
            })
    
    # Add suggested models if not installed
    suggested = [
        {"name": "qwen2.5-coder:14b", "size": "9GB", "description": "Recommended - Best cost-benefit"},
        {"name": "qwen2.5-coder:7b", "size": "4.7GB", "description": "Fast - Good for simple tasks"},
        {"name": "qwen2.5-coder:32b", "size": "19GB", "description": "Advanced - Maximum quality"},
    ]
    
    return {
        "installed": code_models,
        "suggested": suggested
    }


@app.post("/api/code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    """Main endpoint for code generation."""
    model = request.model or settings.DEFAULT_MODEL
    
    result = await ollama.generate(
        prompt=request.prompt,
        model=model,
        context=request.context,
        temperature=request.temperature or 0.7,
        max_tokens=request.max_tokens or 4096
    )
    
    return CodeResponse(**result)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with message history."""
    model = request.model or settings.DEFAULT_MODEL
    
    # Build chat context
    context_parts = []
    for msg in request.messages[-10:]:  # Last 10 messages
        role = "User" if msg.role == "user" else "Assistant"
        context_parts.append(f"{role}: {msg.content}")
    
    context = "\n".join(context_parts)
    
    # Last message is the current question
    prompt = request.messages[-1].content if request.messages else ""
    
    result = await ollama.generate(
        prompt=prompt,
        model=model,
        context=context if len(request.messages) > 1 else None
    )
    
    return result


# ============================================================================
# ROUTES - FILES
# ============================================================================

@app.get("/api/files")
async def list_files(path: str = "."):
    """List files in a directory."""
    return file_manager.list_directory(path)


@app.get("/api/files/read")
async def read_file(path: str):
    """Read file content."""
    return file_manager.read_file(path)


@app.post("/api/files/write")
async def write_file(request: FileRequest):
    """Save content to a file."""
    if not request.content:
        raise HTTPException(status_code=400, detail="Content not provided")
    return file_manager.write_file(request.path, request.content)


# ============================================================================
# STATIC FILES
# ============================================================================

# Mount static files if they exist
static_path = settings.WEB_DIR / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=False
    )

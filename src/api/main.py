"""
DuilioCode Studio - API Principal
Assistente de programação local com Ollama + Qwen2.5-Coder
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
# CONFIGURAÇÕES
# ============================================================================

class Settings:
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5-coder:14b")
    FALLBACK_MODEL = "qwen2.5-coder:7b"
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7
    
    # Diretórios
    BASE_DIR = Path(__file__).parent.parent.parent
    WEB_DIR = BASE_DIR / "web"
    TEMPLATES_DIR = WEB_DIR / "templates"


settings = Settings()


# ============================================================================
# MODELOS DE REQUEST/RESPONSE
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
    role: str  # 'user' ou 'assistant'
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
# CLIENTE OLLAMA
# ============================================================================

class OllamaClient:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.timeout = 300.0  # 5 minutos para modelos grandes
    
    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Gera uma resposta usando o modelo especificado."""
        
        # Construir prompt com contexto
        full_prompt = prompt
        if context:
            full_prompt = f"Contexto da conversa:\n{context}\n\nNova pergunta: {prompt}"
        
        # System prompt para código
        if not system_prompt:
            system_prompt = """Você é DuilioCode, um assistente de programação expert.

Suas características:
- Responde em Português do Brasil
- Fornece código limpo, bem documentado e seguindo boas práticas
- Explica conceitos de forma clara e didática
- Sugere melhorias de performance e segurança
- Conhece múltiplas linguagens: Python, JavaScript, TypeScript, Kotlin, Java, Go, Rust, C++
- Entende arquitetura de software: Clean Architecture, SOLID, Design Patterns
- Fornece exemplos práticos sempre que possível

Ao fornecer código:
- Use blocos de código com a linguagem especificada (```python, ```javascript, etc)
- Adicione comentários explicativos
- Indique possíveis erros ou edge cases"""

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
                raise HTTPException(status_code=500, detail=f"Erro ao conectar com Ollama: {str(e)}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Lista modelos disponíveis no Ollama."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
            except Exception:
                return []
    
    async def check_health(self) -> bool:
        """Verifica se o Ollama está rodando."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
            except Exception:
                return False


# ============================================================================
# GERENCIADOR DE ARQUIVOS
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
        """Detecta a linguagem pelo extensão do arquivo."""
        ext = Path(path).suffix.lower()
        return cls.LANGUAGE_MAP.get(ext, 'text')
    
    @classmethod
    def read_file(cls, path: str) -> Dict[str, Any]:
        """Lê um arquivo e retorna seu conteúdo."""
        file_path = Path(path).expanduser()
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {path}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Caminho não é um arquivo: {path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return {
                "path": str(file_path),
                "content": content,
                "language": cls.get_language(path),
                "size": len(content)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo: {str(e)}")
    
    @classmethod
    def write_file(cls, path: str, content: str) -> Dict[str, Any]:
        """Escreve conteúdo em um arquivo."""
        file_path = Path(path).expanduser()
        
        try:
            # Criar diretório se não existir
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup se arquivo existir
            if file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
            
            # Escrever novo conteúdo
            file_path.write_text(content, encoding='utf-8')
            
            return {
                "path": str(file_path),
                "content": content,
                "language": cls.get_language(path),
                "size": len(content),
                "saved": True
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
    
    @classmethod
    def list_directory(cls, path: str = ".") -> List[Dict[str, Any]]:
        """Lista arquivos e pastas em um diretório."""
        dir_path = Path(path).expanduser()
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Diretório não encontrado: {path}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Caminho não é um diretório: {path}")
        
        items = []
        try:
            for item in sorted(dir_path.iterdir()):
                # Ignorar arquivos ocultos e diretórios comuns
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
            raise HTTPException(status_code=500, detail=f"Erro ao listar diretório: {str(e)}")


# ============================================================================
# APLICAÇÃO FASTAPI
# ============================================================================

app = FastAPI(
    title="DuilioCode Studio",
    description="Assistente de programação local com IA",
    version="1.0.0"
)

# Clientes
ollama = OllamaClient()
file_manager = FileManager()


# ============================================================================
# ROTAS - PÁGINAS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Página principal."""
    template_path = settings.TEMPLATES_DIR / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>DuilioCode Studio</h1><p>Template não encontrado</p>")


# ============================================================================
# ROTAS - API
# ============================================================================

@app.get("/health")
async def health_check():
    """Verifica status do servidor."""
    ollama_healthy = await ollama.check_health()
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama": "connected" if ollama_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/models")
async def list_models():
    """Lista modelos disponíveis."""
    models = await ollama.list_models()
    
    # Filtrar e enriquecer informações
    code_models = []
    for model in models:
        name = model.get("name", "")
        
        # Filtrar modelos de código
        if any(kw in name.lower() for kw in ['coder', 'code', 'deepseek', 'starcoder']):
            size_bytes = model.get("size", 0)
            size_gb = round(size_bytes / (1024**3), 1)
            
            code_models.append({
                "name": name,
                "size": f"{size_gb}GB",
                "parameters": model.get("details", {}).get("parameter_size", ""),
                "recommended": "qwen2.5-coder:14b" in name
            })
    
    # Adicionar modelos sugeridos se não estiverem instalados
    suggested = [
        {"name": "qwen2.5-coder:14b", "size": "9GB", "description": "Recomendado - Melhor custo-benefício"},
        {"name": "qwen2.5-coder:7b", "size": "4.7GB", "description": "Rápido - Bom para tarefas simples"},
        {"name": "qwen2.5-coder:32b", "size": "19GB", "description": "Avançado - Máxima qualidade"},
    ]
    
    return {
        "installed": code_models,
        "suggested": suggested
    }


@app.post("/api/code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    """Endpoint principal para geração de código."""
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
    """Chat com histórico de mensagens."""
    model = request.model or settings.DEFAULT_MODEL
    
    # Construir contexto do chat
    context_parts = []
    for msg in request.messages[-10:]:  # Últimas 10 mensagens
        role = "Usuário" if msg.role == "user" else "Assistente"
        context_parts.append(f"{role}: {msg.content}")
    
    context = "\n".join(context_parts)
    
    # Última mensagem é a pergunta atual
    prompt = request.messages[-1].content if request.messages else ""
    
    result = await ollama.generate(
        prompt=prompt,
        model=model,
        context=context if len(request.messages) > 1 else None
    )
    
    return result


# ============================================================================
# ROTAS - ARQUIVOS
# ============================================================================

@app.get("/api/files")
async def list_files(path: str = "."):
    """Lista arquivos em um diretório."""
    return file_manager.list_directory(path)


@app.get("/api/files/read")
async def read_file(path: str):
    """Lê conteúdo de um arquivo."""
    return file_manager.read_file(path)


@app.post("/api/files/write")
async def write_file(request: FileRequest):
    """Salva conteúdo em um arquivo."""
    if not request.content:
        raise HTTPException(status_code=400, detail="Conteúdo não fornecido")
    return file_manager.write_file(request.path, request.content)


# ============================================================================
# STATIC FILES
# ============================================================================

# Montar arquivos estáticos se existirem
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

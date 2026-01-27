"""
Documentation API endpoints
Serves documentation files and provides API for documentation viewer
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/docs", tags=["Documentation"])


class DocItem(BaseModel):
    """Documentation item model"""
    id: str
    title: str
    category: Optional[str] = None
    path: str


class DocContent(BaseModel):
    """Documentation content model"""
    id: str
    title: str
    content: str
    category: Optional[str] = None


def get_docs_dir() -> Path:
    """Get documentation directory path"""
    base_dir = Path(__file__).parent.parent.parent.parent
    return base_dir / "docs"


def parse_markdown_title(content: str) -> str:
    """Extract title from markdown content"""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
        if line.startswith('## '):
            return line[3:].strip()
    return "Untitled"


def get_category_from_filename(filename: str) -> str:
    """Determine category from filename"""
    if filename.startswith('00-'):
        return '📚 Índice'
    if filename.startswith('01-') or filename.startswith('02-') or filename.startswith('03-'):
        return '🚀 Início Rápido'
    if filename.startswith('04-') or filename.startswith('05-') or filename.startswith('06-'):
        return '🏗️ Arquitetura'
    if filename.startswith('07-') or filename.startswith('08-') or filename.startswith('09-'):
        return '🔌 Integrações'
    if filename.startswith('10-') or filename.startswith('11-') or filename.startswith('12-'):
        return '💬 Sistema de Chat'
    if filename.startswith('13-') or filename.startswith('14-') or filename.startswith('15-'):
        return '📁 Operações de Arquivos'
    if filename.startswith('16-') or filename.startswith('17-') or filename.startswith('18-'):
        return '🧠 Inteligência e Análise'
    if filename.startswith('19-') or filename.startswith('20-') or filename.startswith('21-'):
        return '🗄️ Banco de Dados'
    if filename.startswith('22-') or filename.startswith('23-') or filename.startswith('24-'):
        return '🔒 Segurança'
    if filename.startswith('25-') or filename.startswith('26-') or filename.startswith('27-'):
        return '📊 Observabilidade'
    if filename.startswith('28-') or filename.startswith('29-'):
        return '🧪 Testes'
    if filename.startswith('30-') or filename.startswith('31-') or filename.startswith('32-'):
        return '🔧 Serviços e Algoritmos'
    if filename.startswith('33-') or filename.startswith('34-'):
        return '🚀 Deploy e Produção'
    return '📝 Outros'


@router.get("/list")
async def list_docs(lang: str = Query("pt", description="Language: pt or en")) -> List[DocItem]:
    """
    List all available documentation files
    
    Args:
        lang: Language code (pt or en)
    
    Returns:
        List of documentation items
    """
    docs_dir = get_docs_dir()
    lang_dir = docs_dir / lang
    
    if not lang_dir.exists():
        return []
    
    docs = []
    for md_file in sorted(lang_dir.glob("*.md")):
        try:
            content = md_file.read_text(encoding='utf-8')
            title = parse_markdown_title(content)
            doc_id = md_file.stem
            category = get_category_from_filename(md_file.name)
            
            docs.append(DocItem(
                id=doc_id,
                title=title,
                category=category,
                path=str(md_file.relative_to(docs_dir))
            ))
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
            continue
    
    return docs


@router.get("/content")
async def get_doc_content(
    lang: str = Query(..., description="Language: pt or en"),
    doc: str = Query(..., description="Document ID (filename without .md)")
) -> DocContent:
    """
    Get documentation content
    
    Args:
        lang: Language code (pt or en)
        doc: Document ID (filename without .md extension)
    
    Returns:
        Documentation content
    """
    docs_dir = get_docs_dir()
    doc_file = docs_dir / lang / f"{doc}.md"
    
    if not doc_file.exists():
        raise HTTPException(status_code=404, detail=f"Document {doc} not found in {lang}")
    
    try:
        content = doc_file.read_text(encoding='utf-8')
        title = parse_markdown_title(content)
        category = get_category_from_filename(doc_file.name)
        
        return DocContent(
            id=doc,
            title=title,
            content=content,
            category=category
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading document: {str(e)}")


@router.get("/viewer", response_class=HTMLResponse)
async def docs_viewer():
    """
    Serve documentation viewer HTML page
    """
    viewer_file = Path(__file__).parent.parent.parent.parent / "web" / "templates" / "docs.html"
    
    if not viewer_file.exists():
        raise HTTPException(status_code=404, detail="Documentation viewer not found")
    
    return HTMLResponse(content=viewer_file.read_text(encoding='utf-8'))

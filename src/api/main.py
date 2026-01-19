"""
DuilioAI - FastAPI Server
=========================
Unified API for chat, code and image generation.

100% Local - No restrictions - Optimized for Apple Silicon
"""

import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from loguru import logger

from config.settings import settings
from src.chat.ollama_client import OllamaClient

# Try to import image generation (optional - requires torch)
try:
    from src.image_gen.sd_client import (
        ImageGenerator, 
        image_to_base64, 
        base64_to_image
    )
    IMAGE_GEN_AVAILABLE = True
except ImportError as e:
    IMAGE_GEN_AVAILABLE = False
    logger.warning(f"⚠️ Image generation not available: {e}")


# === Request/Response Models ===

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    system: Optional[str] = None
    conversation_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    model: str
    conversation_id: Optional[str] = None


class GenerateImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = "blurry, low quality, distorted, ugly"
    width: int = Field(default=512, ge=256, le=512)
    height: int = Field(default=512, ge=256, le=512)
    steps: int = Field(default=20, ge=5, le=50)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    num_images: int = Field(default=1, ge=1, le=2)
    seed: Optional[int] = None


class EditImageRequest(BaseModel):
    image: str  # Base64
    prompt: str
    negative_prompt: str = "blurry, low quality, distorted"
    strength: float = Field(default=0.7, ge=0.1, le=1.0)
    steps: int = Field(default=20, ge=5, le=50)
    seed: Optional[int] = None
    quick: bool = False


class InpaintRequest(BaseModel):
    image: str  # Base64
    mask: str   # Base64 (white = edit, black = keep)
    prompt: str
    negative_prompt: str = "blurry, low quality, distorted"
    steps: int = Field(default=20, ge=5, le=50)
    seed: Optional[int] = None


class ImageResponse(BaseModel):
    images: List[str]  # Base64 encoded
    seed: Optional[int] = None


# === Global State ===

ollama_client: Optional[OllamaClient] = None
image_generator: Optional[ImageGenerator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    global ollama_client, image_generator
    
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    
    # Initialize chat client
    ollama_client = OllamaClient()
    
    # Initialize image generator if available
    if IMAGE_GEN_AVAILABLE:
        try:
            # preload=True loads models at startup (takes ~30-60s)
            # This prevents timeout errors on first API request
            logger.info("⏳ Initializing image generator with model preloading...")
            image_generator = ImageGenerator(preload=True)
            logger.info("✅ Image generation enabled and models ready!")
        except Exception as e:
            logger.error(f"❌ Failed to init image generator: {e}")
            image_generator = None
    else:
        logger.info("⚠️ Image generation disabled (install torch & diffusers)")
    
    logger.info(f"✅ Server ready at http://{settings.HOST}:{settings.PORT}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    if image_generator:
        image_generator.unload()


# === App Setup ===

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS - Allow all for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
web_dir = Path(__file__).parent.parent.parent / "web"
if web_dir.exists():
    static_dir = web_dir / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")


# === Routes ===

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve web interface."""
    index_path = web_dir / "templates" / "index.html"
    if index_path.exists():
        return index_path.read_text()
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>{settings.PROJECT_NAME}</title>
            <style>
                body {{ font-family: system-ui; background: #0a0a0f; color: #e8e8f0; 
                       display: flex; justify-content: center; align-items: center; 
                       min-height: 100vh; margin: 0; }}
                .container {{ text-align: center; padding: 40px; }}
                h1 {{ font-size: 3em; margin-bottom: 20px; }}
                p {{ color: #a0a0b0; }}
                a {{ color: #6366f1; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎨 {settings.PROJECT_NAME}</h1>
                <p>API is running!</p>
                <p>Visit <a href="/docs">/docs</a> for API documentation</p>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "features": {
            "chat": True,
            "code": True,
            "image_generation": image_generator is not None,
        }
    }


# === Chat Endpoints ===

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with LLM."""
    try:
        response = await ollama_client.chat(
            message=request.message,
            model=request.model,
            system=request.system,
            stream=False
        )
        
        return ChatResponse(
            response=response,
            model=request.model or ollama_client.model,
            conversation_id=request.conversation_id
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/clear")
async def clear_chat():
    """Clear conversation history."""
    ollama_client.clear_history()
    return {"status": "cleared"}


@app.get("/api/models")
async def list_models():
    """List available Ollama models."""
    try:
        models = await ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list models: {e}")


@app.post("/api/code")
async def generate_code(request: ChatRequest):
    """Generate code with specialized code model."""
    try:
        code_model = request.model or settings.OLLAMA_CODE_MODEL
        
        response = await ollama_client.chat(
            message=request.message,
            model=code_model,
            system="Você é um programador expert. Gere código limpo, eficiente e bem comentado. Responda apenas com o código solicitado.",
            keep_history=False
        )
        return {"code": response}
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Image Generation Endpoints ===

def _check_image_gen():
    """Check if image generation is available."""
    if not image_generator:
        raise HTTPException(
            status_code=503,
            detail="Image generation not available. Install: pip install torch torchvision diffusers"
        )


@app.post("/api/image/generate", response_model=ImageResponse)
async def generate_image(request: GenerateImageRequest):
    """Generate image from text prompt."""
    _check_image_gen()
    
    try:
        logger.info(f"📷 Generate request: '{request.prompt[:50]}...'")
        
        images = image_generator.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            num_images=request.num_images,
            seed=request.seed
        )
        
        return ImageResponse(
            images=[image_to_base64(img) for img in images],
            seed=request.seed
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/image/edit", response_model=ImageResponse)
async def edit_image(request: EditImageRequest):
    """Edit existing image with prompt."""
    _check_image_gen()
    
    try:
        logger.info(f"✏️ Edit request: '{request.prompt[:50]}...'")
        
        source_image = base64_to_image(request.image)
        
        if request.quick:
            images = image_generator.quick_edit(
                image=source_image,
                prompt=request.prompt,
                strength=request.strength
            )
        else:
            images = image_generator.edit(
                image=source_image,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                strength=request.strength,
                steps=request.steps,
                seed=request.seed,
                max_size=512
            )
        
        return ImageResponse(
            images=[image_to_base64(img) for img in images],
            seed=request.seed
        )
    except Exception as e:
        logger.error(f"Edit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/image/inpaint", response_model=ImageResponse)
async def inpaint_image(request: InpaintRequest):
    """
    Inpaint: edit specific area of image using mask.
    - White in mask = area to edit
    - Black in mask = area to keep
    """
    _check_image_gen()
    
    try:
        logger.info(f"🖌️ Inpaint request: '{request.prompt[:50]}...'")
        
        source_image = base64_to_image(request.image)
        mask_image = base64_to_image(request.mask)
        
        images = image_generator.inpaint(
            image=source_image,
            mask=mask_image,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            steps=request.steps,
            seed=request.seed,
            max_size=512
        )
        
        return ImageResponse(
            images=[image_to_base64(img) for img in images],
            seed=request.seed
        )
    except Exception as e:
        logger.error(f"Inpaint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Run Server ===

def main():
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    main()

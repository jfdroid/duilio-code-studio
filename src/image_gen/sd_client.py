"""
DuilioAI - Stable Diffusion Client
===================================
Optimized for Apple Silicon (MPS) with critical fixes for image generation.

SOLID Principles Applied:
- Single Responsibility: Each class has one job
- Open/Closed: Extensible via inheritance
- Liskov Substitution: Pipelines are interchangeable
- Interface Segregation: Minimal interfaces
- Dependency Inversion: Depends on abstractions
"""

import io
import gc
import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Union, Callable, Protocol
from dataclasses import dataclass
from enum import Enum

import torch
from PIL import Image, ImageDraw
from loguru import logger


# === Domain Models (Single Responsibility) ===

class DeviceType(Enum):
    """Supported compute devices."""
    MPS = "mps"
    CUDA = "cuda"
    CPU = "cpu"


@dataclass
class ImageConfig:
    """Configuration for image generation."""
    max_size: int = 512
    min_size: int = 256
    default_steps: int = 20
    quick_steps: int = 12
    guidance_scale: float = 7.5
    

@dataclass
class GenerationResult:
    """Result of image generation."""
    images: List[Image.Image]
    seed: Optional[int] = None
    steps_used: int = 0
    

# === Interfaces (Interface Segregation) ===

class ImageProcessor(Protocol):
    """Interface for image processing."""
    def load(self, source: Union[str, bytes, Image.Image]) -> Image.Image: ...
    def prepare(self, image: Image.Image, max_size: int) -> Image.Image: ...
    def to_base64(self, image: Image.Image) -> str: ...


class ImagePipeline(ABC):
    """Abstract base for image pipelines (Open/Closed)."""
    
    @abstractmethod
    def process(self, **kwargs) -> List[Image.Image]:
        pass
    
    @abstractmethod
    def unload(self) -> None:
        pass


# === Device Manager (Single Responsibility) ===

class DeviceManager:
    """Manages compute device selection and configuration."""
    
    def __init__(self):
        self._device = self._detect_device()
        self._dtype = self._get_optimal_dtype()
        logger.info(f"🖥️ Device: {self._device.value}, Dtype: {self._dtype}")
    
    @property
    def device(self) -> str:
        return self._device.value
    
    @property
    def dtype(self) -> torch.dtype:
        return self._dtype
    
    @property
    def is_mps(self) -> bool:
        return self._device == DeviceType.MPS
    
    def _detect_device(self) -> DeviceType:
        """Detect best available compute device."""
        if torch.backends.mps.is_available():
            logger.info("🍎 Apple Silicon detected - Using MPS (Metal)")
            return DeviceType.MPS
        elif torch.cuda.is_available():
            logger.info("🎮 NVIDIA GPU detected - Using CUDA")
            return DeviceType.CUDA
        logger.info("💻 Using CPU (slower)")
        return DeviceType.CPU
    
    def _get_optimal_dtype(self) -> torch.dtype:
        """
        Get optimal dtype for device.
        
        CRITICAL FIX: MPS has issues with float16 for many SD models,
        causing black images. Use float32 for stability.
        """
        if self._device == DeviceType.MPS:
            # CRITICAL: float16 causes black images on MPS for many models
            # Using float32 for stability (slightly slower but works)
            return torch.float32
        elif self._device == DeviceType.CUDA:
            return torch.float16
        return torch.float32
    
    def create_generator(self, seed: Optional[int] = None) -> Optional[torch.Generator]:
        """
        Create generator with proper device handling.
        
        CRITICAL FIX: MPS generator must be on CPU to avoid black images.
        """
        if seed is None:
            return None
        
        # CRITICAL: For MPS, generator MUST be on CPU
        if self._device == DeviceType.MPS:
            generator = torch.Generator(device="cpu")
        else:
            generator = torch.Generator(device=self.device)
        
        generator.manual_seed(seed)
        return generator
    
    def clear_cache(self) -> None:
        """Clear device memory cache."""
        gc.collect()
        if self._device == DeviceType.MPS:
            torch.mps.empty_cache()
        elif self._device == DeviceType.CUDA:
            torch.cuda.empty_cache()


# === Image Processor (Single Responsibility) ===

class DefaultImageProcessor:
    """Handles image loading, preparation and conversion."""
    
    def load(self, source: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """Load image from various sources."""
        if isinstance(source, Image.Image):
            return source.convert("RGB")
        
        if isinstance(source, bytes):
            return Image.open(io.BytesIO(source)).convert("RGB")
        
        if isinstance(source, (str, Path)):
            source_str = str(source)
            # Check if base64
            if source_str.startswith("data:") or len(source_str) > 500:
                return self.from_base64(source_str)
            return Image.open(source_str).convert("RGB")
        
        raise ValueError(f"Unsupported image type: {type(source)}")
    
    def prepare(self, image: Image.Image, max_size: int = 512) -> Image.Image:
        """Prepare image for SD (resize and ensure multiple of 8)."""
        w, h = image.size
        
        # Limit max size for memory
        if w > max_size or h > max_size:
            ratio = min(max_size / w, max_size / h)
            w, h = int(w * ratio), int(h * ratio)
        
        # Ensure multiple of 8 (SD requirement)
        w = (w // 8) * 8
        h = (h // 8) * 8
        
        # Minimum size
        w = max(w, 256)
        h = max(h, 256)
        
        return image.resize((w, h), Image.Resampling.LANCZOS)
    
    def to_base64(self, image: Image.Image, format: str = "PNG") -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format=format, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode()
    
    def from_base64(self, b64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image."""
        if "," in b64_string:
            b64_string = b64_string.split(",")[1]
        image_data = base64.b64decode(b64_string)
        return Image.open(io.BytesIO(image_data)).convert("RGB")


# === Pipeline Factory (Dependency Inversion) ===

class PipelineFactory:
    """Creates and configures SD pipelines."""
    
    # Verified official models
    MODELS = {
        "txt2img": "stable-diffusion-v1-5/stable-diffusion-v1-5",
        "img2img": "stable-diffusion-v1-5/stable-diffusion-v1-5",
        "inpaint": "runwayml/stable-diffusion-inpainting",
    }
    
    def __init__(self, device_manager: DeviceManager):
        self._device = device_manager
        self._pipelines = {}
    
    def get_txt2img(self):
        """Get text-to-image pipeline."""
        if "txt2img" not in self._pipelines:
            from diffusers import StableDiffusionPipeline
            
            logger.info("📥 Loading text-to-image model (first time may take a while)...")
            
            pipe = StableDiffusionPipeline.from_pretrained(
                self.MODELS["txt2img"],
                torch_dtype=self._device.dtype,
                safety_checker=None,
                requires_safety_checker=False,
            )
            
            self._pipelines["txt2img"] = self._configure_pipeline(pipe)
            logger.info("✅ Text-to-image model loaded")
        
        return self._pipelines["txt2img"]
    
    def get_img2img(self):
        """Get image-to-image pipeline."""
        if "img2img" not in self._pipelines:
            from diffusers import StableDiffusionImg2ImgPipeline
            
            logger.info("📥 Loading image-to-image model...")
            
            try:
                # First try to load from local cache (faster, no network)
                pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    self.MODELS["img2img"],
                    torch_dtype=self._device.dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                    local_files_only=True,  # Use cached files only
                )
            except Exception as e:
                logger.info("📡 Model not in cache, downloading...")
                pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    self.MODELS["img2img"],
                    torch_dtype=self._device.dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
            
            self._pipelines["img2img"] = self._configure_pipeline(pipe)
            logger.info("✅ Image-to-image model loaded")
        
        return self._pipelines["img2img"]
    
    def get_inpaint(self):
        """Get inpainting pipeline."""
        if "inpaint" not in self._pipelines:
            from diffusers import StableDiffusionInpaintPipeline
            
            logger.info("📥 Loading inpainting model...")
            
            try:
                # First try to load from local cache (faster, no network)
                pipe = StableDiffusionInpaintPipeline.from_pretrained(
                    self.MODELS["inpaint"],
                    torch_dtype=self._device.dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                    local_files_only=True,  # Use cached files only
                )
            except Exception as e:
                logger.info("📡 Model not in cache, downloading...")
                pipe = StableDiffusionInpaintPipeline.from_pretrained(
                    self.MODELS["inpaint"],
                    torch_dtype=self._device.dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
            
            self._pipelines["inpaint"] = self._configure_pipeline(pipe)
            logger.info("✅ Inpainting model loaded")
        
        return self._pipelines["inpaint"]
    
    def _configure_pipeline(self, pipe):
        """Apply optimizations to pipeline."""
        # Move to device
        pipe = pipe.to(self._device.device)
        
        # Memory optimizations
        if hasattr(pipe, 'enable_attention_slicing'):
            pipe.enable_attention_slicing("auto")
        
        if hasattr(pipe, 'enable_vae_slicing'):
            pipe.enable_vae_slicing()
        
        # MPS specific: channels_last may help
        if self._device.is_mps:
            try:
                pipe.unet = pipe.unet.to(memory_format=torch.channels_last)
            except Exception:
                pass  # Not critical
        
        return pipe
    
    def unload_all(self):
        """Unload all pipelines and free memory."""
        self._pipelines.clear()
        self._device.clear_cache()
        logger.info("🧹 All models unloaded, memory cleared")


# === Image Generator (Facade Pattern) ===

class ImageGenerator:
    """
    Main image generation interface.
    
    Facade that coordinates all image operations with proper
    error handling and MPS-specific fixes.
    """
    
    def __init__(self, preload: bool = False):
        self._device = DeviceManager()
        self._factory = PipelineFactory(self._device)
        self._processor = DefaultImageProcessor()
        self._config = ImageConfig()
        
        logger.info(f"🎨 DuilioAI ImageGenerator initialized (Device: {self._device.device})")
        
        # Optionally preload models at startup
        if preload:
            self.preload_models()
    
    def preload_models(self):
        """
        Pre-load models at startup to avoid timeout on first request.
        This takes ~30-60 seconds but prevents API timeouts.
        """
        logger.info("⏳ Pre-loading models (this may take 30-60 seconds)...")
        
        try:
            # Load img2img (most used)
            logger.info("   📥 Loading img2img model...")
            self._factory.get_img2img()
            
            # Load inpaint
            logger.info("   📥 Loading inpaint model...")  
            self._factory.get_inpaint()
            
            logger.info("✅ All models pre-loaded and ready!")
            
        except Exception as e:
            logger.error(f"❌ Failed to preload models: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "blurry, low quality, distorted, ugly",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        guidance_scale: float = 7.5,
        num_images: int = 1,
        seed: Optional[int] = None,
    ) -> List[Image.Image]:
        """Generate image from text prompt."""
        
        # Validate and constrain dimensions
        width = min(max(width, self._config.min_size), self._config.max_size)
        height = min(max(height, self._config.min_size), self._config.max_size)
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        pipe = self._factory.get_txt2img()
        generator = self._device.create_generator(seed)
        
        logger.info(f"🎨 Generating {width}x{height} image: '{prompt[:50]}...'")
        
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                num_images_per_prompt=num_images,
                generator=generator,
            )
            
            logger.info(f"✅ Generated {len(result.images)} image(s)")
            return result.images
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            raise
    
    def edit(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        negative_prompt: str = "blurry, low quality, distorted",
        strength: float = 0.7,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        max_size: int = 512,
    ) -> List[Image.Image]:
        """Edit entire image based on prompt."""
        
        # Load and prepare image
        source = self._processor.load(image)
        source = self._processor.prepare(source, max_size)
        
        pipe = self._factory.get_img2img()
        generator = self._device.create_generator(seed)
        
        logger.info(f"✏️ Editing {source.size} image: '{prompt[:50]}...'")
        
        try:
            result = pipe(
                prompt=prompt,
                image=source,
                negative_prompt=negative_prompt,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
            
            logger.info(f"✅ Edit complete")
            return result.images
            
        except Exception as e:
            logger.error(f"❌ Edit failed: {e}")
            raise
    
    def inpaint(
        self,
        image: Union[str, Image.Image],
        mask: Union[str, Image.Image],
        prompt: str,
        negative_prompt: str = "blurry, low quality, distorted",
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        max_size: int = 512,
    ) -> List[Image.Image]:
        """Edit specific area of image using mask."""
        
        # Load and prepare images
        source = self._processor.load(image)
        mask_img = self._processor.load(mask).convert("L")
        
        source = self._processor.prepare(source, max_size)
        mask_img = mask_img.resize(source.size, Image.Resampling.LANCZOS)
        
        pipe = self._factory.get_inpaint()
        generator = self._device.create_generator(seed)
        
        logger.info(f"🖌️ Inpainting {source.size}: '{prompt[:50]}...'")
        
        try:
            result = pipe(
                prompt=prompt,
                image=source,
                mask_image=mask_img,
                negative_prompt=negative_prompt,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
            
            logger.info(f"✅ Inpaint complete")
            return result.images
            
        except Exception as e:
            logger.error(f"❌ Inpaint failed: {e}")
            raise
    
    def quick_edit(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        strength: float = 0.5,
    ) -> List[Image.Image]:
        """Quick edit with reduced quality for preview."""
        return self.edit(
            image=image,
            prompt=prompt,
            strength=strength,
            steps=self._config.quick_steps,
            max_size=384,
        )
    
    def unload(self):
        """Release all resources."""
        self._factory.unload_all()


# === Convenience Functions ===

def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64."""
    processor = DefaultImageProcessor()
    return processor.to_base64(image, format)


def base64_to_image(b64_string: str) -> Image.Image:
    """Convert base64 to PIL Image."""
    processor = DefaultImageProcessor()
    return processor.from_base64(b64_string)


# Singleton instance
_generator: Optional[ImageGenerator] = None


def get_generator() -> ImageGenerator:
    """Get or create singleton generator instance."""
    global _generator
    if _generator is None:
        _generator = ImageGenerator()
    return _generator


def generate(prompt: str, **kwargs) -> List[Image.Image]:
    """Generate image from prompt."""
    return get_generator().generate(prompt, **kwargs)


def edit(image, prompt: str, **kwargs) -> List[Image.Image]:
    """Edit image with prompt."""
    return get_generator().edit(image, prompt, **kwargs)


def inpaint(image, mask, prompt: str, **kwargs) -> List[Image.Image]:
    """Inpaint masked area of image."""
    return get_generator().inpaint(image, mask, prompt, **kwargs)

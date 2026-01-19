"""Image generation module with Stable Diffusion (optional - requires torch)."""

try:
    from .sd_client import ImageGenerator, generate, edit, inpaint
    __all__ = ["ImageGenerator", "generate", "edit", "inpaint"]
except ImportError:
    # torch not installed
    __all__ = []

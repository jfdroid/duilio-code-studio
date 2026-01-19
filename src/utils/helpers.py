"""
Utility helpers for image processing and file operations.
"""

import io
import base64
from pathlib import Path
from datetime import datetime
from typing import Union

from PIL import Image


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode()


def base64_to_image(b64_string: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    # Remove data URL prefix if present
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    
    image_data = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(image_data))


def save_image(
    image: Image.Image,
    path: Union[str, Path] = None,
    format: str = "PNG"
) -> Path:
    """Save image to file. Auto-generates path if not provided."""
    if path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(f"output_{timestamp}.{format.lower()}")
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format=format)
    
    return path


def load_image(path: Union[str, Path]) -> Image.Image:
    """Load image from file."""
    return Image.open(path).convert("RGB")


def resize_image(
    image: Image.Image,
    max_size: int = 1024,
    maintain_aspect: bool = True
) -> Image.Image:
    """Resize image to fit within max_size while maintaining aspect ratio."""
    if not maintain_aspect:
        return image.resize((max_size, max_size))
    
    ratio = min(max_size / image.width, max_size / image.height)
    if ratio >= 1:
        return image
    
    new_size = (int(image.width * ratio), int(image.height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def create_mask_from_selection(
    image_size: tuple,
    selection: dict
) -> Image.Image:
    """Create a mask image from selection coordinates.
    
    selection format: {"x": int, "y": int, "width": int, "height": int}
    """
    mask = Image.new("L", image_size, 0)
    
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    
    x, y = selection["x"], selection["y"]
    w, h = selection["width"], selection["height"]
    
    draw.rectangle([x, y, x + w, y + h], fill=255)
    
    return mask

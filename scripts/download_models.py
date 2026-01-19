#!/usr/bin/env python3
"""
Download Stable Diffusion models for offline use.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from diffusers import StableDiffusionInpaintPipeline
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


MODELS = {
    "txt2img": "stabilityai/stable-diffusion-2-1",
    "inpaint": "stabilityai/stable-diffusion-2-inpainting",
}


def download_models():
    """Download and cache SD models."""
    console.print("\n[bold cyan]🎨 Downloading Stable Diffusion Models[/]")
    console.print("[dim]Models will be cached in ~/.cache/huggingface/[/]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Text to Image
        task = progress.add_task("Downloading SD 2.1 (txt2img)...", total=None)
        try:
            StableDiffusionPipeline.from_pretrained(
                MODELS["txt2img"],
                safety_checker=None,
                requires_safety_checker=False,
            )
            progress.update(task, description="[green]✓ SD 2.1 (txt2img) downloaded[/]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ txt2img failed: {e}[/]")
        
        # Inpainting
        task = progress.add_task("Downloading SD 2.1 (inpaint)...", total=None)
        try:
            StableDiffusionInpaintPipeline.from_pretrained(
                MODELS["inpaint"],
                safety_checker=None,
                requires_safety_checker=False,
            )
            progress.update(task, description="[green]✓ SD 2.1 (inpaint) downloaded[/]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ inpaint failed: {e}[/]")
    
    console.print("\n[bold green]✅ Model download complete![/]")
    console.print("[dim]Models are cached and ready for offline use.[/]\n")


if __name__ == "__main__":
    download_models()

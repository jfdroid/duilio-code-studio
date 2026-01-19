#!/usr/bin/env python3
"""
DuilioAI - Model Downloader
===========================
Downloads all required Stable Diffusion models BEFORE starting the server.
Run this ONCE, then the server will start instantly.

Usage: python download_models.py
"""

import os
import sys
import shutil

# Clear incomplete downloads
CACHE_DIR = os.path.expanduser("~/.cache/huggingface/hub")

def clear_incomplete_downloads():
    """Remove incomplete model downloads."""
    print("🧹 Checking for incomplete downloads...")
    
    if not os.path.exists(CACHE_DIR):
        print("   No cache found")
        return
    
    incomplete_count = 0
    for root, dirs, files in os.walk(CACHE_DIR):
        for f in files:
            if f.endswith('.incomplete'):
                path = os.path.join(root, f)
                os.remove(path)
                incomplete_count += 1
                print(f"   Removed: {f}")
    
    if incomplete_count > 0:
        print(f"   ✅ Removed {incomplete_count} incomplete files")
    else:
        print("   ✅ No incomplete files found")

def download_models():
    """Download all required models."""
    print("\n" + "=" * 60)
    print("🎨 DuilioAI - Model Downloader")
    print("=" * 60)
    
    # Clear incomplete files first
    clear_incomplete_downloads()
    
    print("\n📦 Installing/checking dependencies...")
    
    # Check torch
    try:
        import torch
        print(f"   ✅ PyTorch {torch.__version__}")
        if torch.backends.mps.is_available():
            print("   🍎 Apple Silicon (MPS) available")
    except ImportError:
        print("   ❌ PyTorch not installed! Run: pip install torch")
        sys.exit(1)
    
    # Check diffusers
    try:
        import diffusers
        print(f"   ✅ Diffusers {diffusers.__version__}")
    except ImportError:
        print("   ❌ Diffusers not installed! Run: pip install diffusers")
        sys.exit(1)
    
    # Download models
    from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipeline
    
    models = [
        ("stable-diffusion-v1-5/stable-diffusion-v1-5", "img2img", StableDiffusionImg2ImgPipeline),
        ("runwayml/stable-diffusion-inpainting", "inpaint", StableDiffusionInpaintPipeline),
    ]
    
    for model_id, name, pipeline_class in models:
        print(f"\n📥 Downloading {name} model: {model_id}")
        print("   This may take 5-10 minutes on first download...")
        
        try:
            pipe = pipeline_class.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            
            # Move to device to verify it works
            if torch.backends.mps.is_available():
                pipe = pipe.to("mps")
            
            print(f"   ✅ {name} model downloaded and verified!")
            
            # Cleanup
            del pipe
            import gc
            gc.collect()
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
                
        except Exception as e:
            print(f"   ❌ Error downloading {name}: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ALL MODELS DOWNLOADED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNow you can start the server:")
    print("  ./venv/bin/python3 -m src.api.main")
    print("\nThe server will start MUCH faster now (~10-30 seconds)")

if __name__ == "__main__":
    download_models()

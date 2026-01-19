#!/usr/bin/env python3
"""
Local AI Studio - Quick Start Examples
======================================
Examples of using the AI capabilities programmatically.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def chat_example():
    """Example: Simple chat with LLM."""
    from src.chat import chat
    
    print("=" * 50)
    print("💬 Chat Example")
    print("=" * 50)
    
    response = await chat("Explain quantum computing in simple terms")
    print(f"\n{response}\n")


async def code_example():
    """Example: Generate code."""
    from src.chat.ollama_client import OllamaClient
    
    print("=" * 50)
    print("💻 Code Generation Example")
    print("=" * 50)
    
    client = OllamaClient()
    code = await client.code(
        "Create a Python function that calculates fibonacci numbers",
        language="python"
    )
    print(f"\n{code}\n")


async def image_example():
    """Example: Generate an image."""
    from src.image_gen import generate
    from src.utils import save_image
    
    print("=" * 50)
    print("🎨 Image Generation Example")
    print("=" * 50)
    
    images = generate(
        prompt="A futuristic city at sunset, cyberpunk style, neon lights",
        negative_prompt="blurry, low quality",
        steps=25,
        width=512,
        height=512
    )
    
    path = save_image(images[0], "output/generated_city.png")
    print(f"\n✅ Image saved to: {path}\n")


async def vision_example():
    """Example: Analyze an image."""
    from src.chat import analyze_image
    
    print("=" * 50)
    print("👁️ Image Analysis Example")
    print("=" * 50)
    
    # You need to provide an actual image path
    image_path = "path/to/your/image.jpg"
    
    if Path(image_path).exists():
        analysis = await analyze_image(image_path, "What objects are in this image?")
        print(f"\n{analysis}\n")
    else:
        print("\n⚠️ Provide a valid image path to test vision\n")


async def streaming_example():
    """Example: Streaming chat response."""
    from src.chat.ollama_client import OllamaClient
    
    print("=" * 50)
    print("🌊 Streaming Chat Example")
    print("=" * 50)
    
    client = OllamaClient()
    
    print("\nStreaming response:")
    async for chunk in await client.chat(
        "Write a haiku about programming",
        stream=True
    ):
        print(chunk, end="", flush=True)
    print("\n")


async def main():
    """Run all examples."""
    print("\n🚀 Local AI Studio - Examples\n")
    
    # Chat
    await chat_example()
    
    # Code generation
    await code_example()
    
    # Streaming
    await streaming_example()
    
    # Uncomment to run image generation (requires SD models):
    # await image_example()
    
    # Uncomment to run vision (requires llava model):
    # await vision_example()
    
    print("✅ Examples complete!")


if __name__ == "__main__":
    asyncio.run(main())

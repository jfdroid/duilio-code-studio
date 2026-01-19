#!/bin/bash
# ====================
# DuilioAI Studio - Git Setup
# ====================

cd /Users/jeffersonsilva/Desen/duilio-ai-studio

echo "🔧 Setting up Git repository..."

# Initialize git if not already
if [ ! -d ".git" ]; then
    git init
    echo "   ✅ Git initialized"
else
    echo "   ✅ Git already initialized"
fi

# Add remote
git remote remove origin 2>/dev/null
git remote add origin https://github.com/jfdroid/duilio-ai-studio.git
echo "   ✅ Remote added: https://github.com/jfdroid/duilio-ai-studio.git"

# Create master branch
git branch -M master
echo "   ✅ Branch master created"

# Add all files
git add .
echo "   ✅ Files staged"

# Commit
git commit -m "feat: Initial commit - DuilioAI Studio

🎨 100% Local AI for image editing, chat and code generation
- Stable Diffusion v1.5 for img2img and txt2img
- RunwayML Inpainting model
- Optimized for Apple Silicon (MPS + float32)
- SOLID architecture
- FastAPI backend
- Modern web interface

Features:
- Generate: Create images from text
- Edit: Modify entire images
- Inpaint: Edit specific areas with mask
- Chat: Conversational AI with Ollama
- Code: Code generation with Qwen2.5-Coder"

echo "   ✅ Committed"

# Push
echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin master

echo ""
echo "✅ Done! Repository configured at:"
echo "   https://github.com/jfdroid/duilio-ai-studio"

#!/bin/bash
# DuilioCode Studio - Script de Inicialização

cd "$(dirname "$0")"

echo "🚀 DuilioCode Studio"
echo "===================="
echo ""

# Verificar Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama não encontrado!"
    echo "   Instale com: brew install ollama"
    exit 1
fi

# Verificar se Ollama está rodando
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama não está rodando. Iniciando..."
    ollama serve &
    sleep 3
fi

# Verificar modelo
echo "📦 Verificando modelo Qwen2.5-Coder..."
if ! ollama list | grep -q "qwen2.5-coder:14b"; then
    echo "⏳ Modelo não encontrado. Para baixar:"
    echo "   ollama pull qwen2.5-coder:14b"
    echo ""
    echo "   Ou use o modelo 7B (mais rápido):"
    echo "   ollama pull qwen2.5-coder:7b"
    echo ""
fi

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Ambiente virtual ativado"
else
    echo "⚠️  Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install fastapi uvicorn httpx pydantic
fi

echo ""
echo "🌐 Interface: http://127.0.0.1:8080"
echo "📖 API Docs:  http://127.0.0.1:8080/docs"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

# Iniciar servidor
cd src/api
python -m uvicorn main:app --host 127.0.0.1 --port 8080 --reload

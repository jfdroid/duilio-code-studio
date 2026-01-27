# Ollama - Motor de IA Local

## O que é Ollama?

Ollama é um servidor que roda modelos de linguagem (LLMs) **diretamente no seu computador**. É como ter um ChatGPT rodando localmente, sem precisar de internet ou enviar dados para servidores externos.

## Por que Usamos Ollama?

### ✅ Vantagens
- **Privacidade**: Seus códigos nunca saem do seu computador
- **Velocidade**: Não depende de conexão com internet
- **Controle**: Você escolhe qual modelo usar
- **Gratuito**: Não há custos de API
- **Offline**: Funciona sem internet

### ❌ Desvantagens
- **Recursos**: Precisa de RAM suficiente (modelos grandes)
- **Velocidade**: Pode ser mais lento que APIs cloud (depende do hardware)

## Como Funciona?

```
DuilioCode → HTTP Request → Ollama Server → Modelo Qwen → Resposta → DuilioCode
```

### Fluxo Detalhado

1. **DuilioCode envia prompt** para Ollama via HTTP
2. **Ollama processa** usando o modelo instalado (Qwen2.5-Coder)
3. **Modelo gera resposta** baseada no prompt
4. **Ollama retorna** a resposta para DuilioCode
5. **DuilioCode processa** a resposta e executa ações se necessário

## Instalação

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Baixe do site: https://ollama.com

## Iniciando o Servidor

### Automático
O `start.sh` verifica e inicia automaticamente.

### Manual
```bash
ollama serve
```

O servidor roda em `http://localhost:11434`

## Modelos Disponíveis

### Qwen2.5-Coder (Recomendado)
```bash
# Versão 14B (mais inteligente, mais lenta)
ollama pull qwen2.5-coder:14b

# Versão 7B (mais rápida, menos precisa)
ollama pull qwen2.5-coder:7b
```

### Outros Modelos
```bash
# Listar modelos instalados
ollama list

# Baixar outros modelos
ollama pull llama2
ollama pull codellama
```

## Integração no DuilioCode

### Código: `src/services/ollama_service.py`

```python
class OllamaService:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def generate(self, prompt, model, system_prompt=None):
        # Envia requisição para Ollama
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt
            }
        )
        return response.json()
```

### Como é Usado

1. **Chat Handler** chama `ollama.generate()`
2. **Ollama Service** faz requisição HTTP
3. **Ollama Server** processa e retorna
4. **Resposta** é processada e exibida

## Configuração

### Variáveis de Ambiente
```bash
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:14b
```

### No Código
```python
# src/core/config.py
OLLAMA_HOST: str = "http://localhost:11434"
DEFAULT_MODEL: str = "qwen2.5-coder:14b"
```

## Health Check

DuilioCode verifica se Ollama está rodando:

```python
async def health_check(self):
    try:
        response = await self.client.get(f"{self.base_url}/api/tags")
        return {"status": "running", "models": response.json()}
    except:
        return {"status": "offline"}
```

## Streaming (Respostas em Tempo Real)

Ollama suporta streaming - respostas aparecem palavra por palavra:

```python
async def generate_stream(self, prompt, model):
    async with self.client.stream(
        "POST",
        f"{self.base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": True}
    ) as response:
        async for line in response.aiter_lines():
            if line:
                yield json.loads(line)
```

## Troubleshooting

### Ollama não inicia
```bash
# Verificar se está instalado
which ollama

# Verificar logs
ollama serve
```

### Modelo não encontrado
```bash
# Listar modelos
ollama list

# Baixar modelo
ollama pull qwen2.5-coder:14b
```

### Porta ocupada
```bash
# Verificar processo
lsof -i :11434

# Matar processo
kill -9 <PID>
```

## Próximos Passos

- [Qwen2.5-Coder - Modelo de Linguagem](08-qwen.md)
- [Como Funciona o Chat](11-chat-funcionamento.md)

# Qwen2.5-Coder - Modelo de Linguagem

## O que é Qwen2.5-Coder?

Qwen2.5-Coder é um modelo de linguagem **especializado em código**. Ele foi treinado especificamente para entender, gerar e trabalhar com código em várias linguagens de programação.

## Por que Qwen2.5-Coder?

### ✅ Especializado em Código
- Entende sintaxe de múltiplas linguagens
- Gera código funcional e correto
- Compreende contexto de projetos

### ✅ Multilíngue
- Funciona bem em Português e Inglês
- Responde no mesmo idioma que você escreve

### ✅ Tamanhos Disponíveis
- **14B**: Mais inteligente, precisa de mais RAM (16GB+)
- **7B**: Mais rápido, precisa de menos RAM (8GB+)

## Como Funciona?

### Processamento de Prompt

```
Seu prompt → Qwen processa → Gera resposta baseada em:
  - Contexto fornecido
  - Instruções do system prompt
  - Histórico da conversa
  - Conhecimento pré-treinado
```

### Exemplo Prático

**Input:**
```
System Prompt: "Você é DuilioCode. Você pode criar arquivos usando ```create-file:path"
User: "crie um arquivo teste.txt com 'Hello World'"
```

**Output:**
```
```create-file:teste.txt
Hello World
```
```

## System Prompts

### O que são?

System prompts são **instruções** que dizem ao modelo como se comportar. No DuilioCode, usamos system prompts para:

1. **Definir identidade**: "Você é DuilioCode"
2. **Capacidades**: "Você pode criar arquivos usando create-file:"
3. **Formato**: "Use ```create-file:path format"
4. **Regras**: "NUNCA diga que não pode criar arquivos"

### Exemplo de System Prompt

```python
CODE_SYSTEM_PROMPT = """You are DuilioCode. You have DIRECT ACCESS to files.

CRITICAL RULES:
- When user asks to create, use ```create-file:path format
- DO NOT say "I cannot create files" - YOU CAN!
- Start response IMMEDIATELY with create-file blocks
"""
```

## Temperatura (Temperature)

### O que é?

Temperatura controla a **criatividade** da resposta:
- **0.0-0.3**: Muito determinístico (melhor para código)
- **0.7**: Balanceado (padrão)
- **1.0-2.0**: Muito criativo (pode gerar código incorreto)

### No DuilioCode

```python
# Para listagem de arquivos (precisão)
temperature = 0.2

# Para geração de código (criatividade controlada)
temperature = 0.7

# Para explicações (mais natural)
temperature = 0.9
```

## Context Window

### O que é?

Context window é o **tamanho máximo** de texto que o modelo pode processar de uma vez.

### Qwen2.5-Coder
- **14B**: ~32,000 tokens
- **7B**: ~32,000 tokens

### Como Usamos

1. **File Listing**: Lista de arquivos do projeto
2. **Codebase Context**: Análise do código
3. **Conversation History**: Mensagens anteriores
4. **System Info**: Informações do sistema

Tudo isso é enviado junto no prompt!

## Tokens

### O que são?

Tokens são **pedaços de texto** que o modelo processa. Não são exatamente palavras:

- "Hello" = 1 token
- "Hello World" = 2 tokens
- "crie um arquivo" = 4 tokens (em português)

### Limites

- **Input**: Máximo de tokens no prompt
- **Output**: Máximo de tokens na resposta
- **Total**: Soma de input + output

### No DuilioCode

```python
MAX_TOKENS = 4096  # Máximo de tokens na resposta
```

## Streaming

### O que é?

Streaming permite que a resposta apareça **palavra por palavra** em tempo real, ao invés de esperar tudo pronto.

### Como Funciona

```
Sem Streaming:
  [Aguarda 10 segundos] → Resposta completa aparece

Com Streaming:
  "Olá" → "Olá, como" → "Olá, como posso" → ... (aparece em tempo real)
```

### Implementação

```python
async def generate_stream(self, prompt, model):
    async for chunk in ollama.stream(prompt, model):
        yield chunk["response"]  # Envia cada pedaço
```

## Fine-tuning e Adaptação

### Como Adaptamos o Modelo?

Não modificamos o modelo em si, mas **adaptamos os prompts**:

1. **System Prompts Específicos**: Para cada tipo de operação
2. **Few-shot Learning**: Exemplos no prompt
3. **Context Injection**: Informações relevantes
4. **Temperature Adjustment**: Ajuste por tipo de tarefa

### Exemplo de Adaptação

```python
# Para criação de arquivos
system_prompt = """
CRITICAL FORMAT:
```create-file:path/to/file.ext
[content]
```
"""

# Para listagem
system_prompt = """
Use FILE LISTING in context.
Answer: "I see X files and Y folders"
"""
```

## Performance

### Fatores que Afetam Velocidade

1. **Tamanho do Modelo**: 7B é mais rápido que 14B
2. **Tamanho do Prompt**: Prompts maiores = mais lento
3. **Hardware**: CPU/GPU, RAM disponível
4. **Temperature**: Valores baixos são mais rápidos

### Otimizações no DuilioCode

- **Cache de Contexto**: Evita re-análise do codebase
- **Streaming**: Respostas aparecem mais rápido
- **Prompt Simplificado**: Menos tokens = mais rápido

## Troubleshooting

### Respostas Incorretas
- Ajuste temperature
- Melhore system prompt
- Adicione mais contexto

### Muito Lento
- Use modelo 7B ao invés de 14B
- Reduza tamanho do contexto
- Verifique recursos do sistema

### Erros de Memória
- Feche outros aplicativos
- Use modelo menor (7B)
- Reduza MAX_TOKENS

## Próximos Passos

- [FastAPI - Framework Web](09-fastapi.md)
- [Como Funciona o Chat](11-chat-funcionamento.md)

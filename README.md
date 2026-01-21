# 🚀 DuilioCode Studio

Assistente de programação local e offline, powered by **Qwen2.5-Coder**.

## ✨ Features

- 💻 **100% Local** - Funciona sem internet
- 🔒 **Privado** - Seu código nunca sai do seu computador
- ⚡ **Rápido** - Otimizado para Apple Silicon
- 🎨 **Interface Moderna** - UI estilo VS Code/Cursor
- 📁 **Edição de Arquivos** - Lê e escreve arquivos diretamente

## 🏃 Quick Start

```bash
cd /Users/jeffersonsilva/Desen/duilio-code-studio
./start.sh
```

Acesse: **http://127.0.0.1:8080**

## 📦 Modelos Disponíveis

| Modelo | Tamanho | Qualidade | Velocidade |
|--------|---------|-----------|------------|
| qwen2.5-coder:7b | 4.7GB | ⭐⭐⭐ | ⚡⚡⚡⚡ |
| qwen2.5-coder:14b | 9GB | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| qwen2.5-coder:32b | 19GB | ⭐⭐⭐⭐⭐ | ⚡⚡ |

### Instalar Modelo

```bash
# Recomendado (melhor custo-benefício)
ollama pull qwen2.5-coder:14b

# Rápido (para tarefas simples)
ollama pull qwen2.5-coder:7b

# Avançado (máxima qualidade)
ollama pull qwen2.5-coder:32b
```

## 🎯 O que ele faz bem

- ✅ Gerar código em múltiplas linguagens
- ✅ Explicar conceitos de programação
- ✅ Code review e sugestões
- ✅ Debug e correção de erros
- ✅ Refatoração de código
- ✅ Documentação automática
- ✅ Testes unitários
- ✅ Arquitetura e design patterns

## ⚠️ Limitações (vs Claude 4.5 Opus)

| Aspecto | DuilioCode Local | Claude 4.5 Opus |
|---------|------------------|-----------------|
| Raciocínio complexo | Médio | Excelente |
| Contexto longo | ~8K tokens | ~200K tokens |
| Conhecimento atual | Até data de treino | Mais recente |
| Velocidade | Depende do hardware | Rápido |
| Custo | 💚 GRÁTIS | 💰 Por token |
| Privacidade | 💚 100% Local | ☁️ Na nuvem |

## 📁 Estrutura

```
duilio-code-studio/
├── src/
│   └── api/
│       └── main.py      # API FastAPI
├── web/
│   └── templates/
│       └── index.html   # Interface
├── start.sh             # Script de início
└── requirements.txt     # Dependências
```

## 🔧 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Interface web |
| `/health` | GET | Status do servidor |
| `/api/code` | POST | Gerar código |
| `/api/chat` | POST | Chat com histórico |
| `/api/models` | GET | Listar modelos |
| `/api/files` | GET | Listar arquivos |
| `/api/files/read` | GET | Ler arquivo |
| `/api/files/write` | POST | Salvar arquivo |

## 💡 Dicas de Uso

### Prompts eficientes:

```
# Gerar função
"Crie uma função em Python que valida CPF"

# Explicar código
"Explique este código linha por linha: [cole o código]"

# Code review
"Revise este código e sugira melhorias: [cole o código]"

# Arquitetura
"Como implementar Repository Pattern em Kotlin com Clean Architecture?"
```

## 🆚 Comparativo com Outras Ferramentas

| Ferramenta | Tipo | Custo | Offline |
|------------|------|-------|---------|
| **DuilioCode** | Local | Grátis | ✅ |
| Cursor AI | IDE Cloud | Pago | ❌ |
| GitHub Copilot | Extension | Pago | ❌ |
| ChatGPT | Web | Pago | ❌ |
| Claude | Web | Pago | ❌ |

---

**DuilioCode Studio** - Seu Cursor offline! 🚀

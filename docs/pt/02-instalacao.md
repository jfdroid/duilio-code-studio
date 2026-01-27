# Instalação Passo a Passo

## Pré-requisitos

- **Sistema Operacional**: macOS, Linux ou Windows
- **Python**: 3.9 ou superior
- **RAM**: Mínimo 8GB (16GB recomendado para modelo 14B)
- **Espaço em Disco**: ~10GB (para modelo e dependências)

## Passo 1: Instalar Ollama

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
1. Baixe o instalador em: https://ollama.com
2. Execute o instalador
3. Siga as instruções

### Verificar Instalação
```bash
ollama --version
```

## Passo 2: Iniciar Ollama

### Iniciar Servidor
```bash
ollama serve
```

O servidor roda em `http://localhost:11434`

### Verificar se Está Rodando
```bash
curl http://localhost:11434/api/tags
```

Se retornar JSON, está funcionando!

## Passo 3: Baixar Modelo Qwen2.5-Coder

### Opção 1: Modelo 14B (Recomendado - Mais Inteligente)
```bash
ollama pull qwen2.5-coder:14b
```

**Requisitos**: 16GB+ RAM

### Opção 2: Modelo 7B (Mais Rápido)
```bash
ollama pull qwen2.5-coder:7b
```

**Requisitos**: 8GB+ RAM

### Verificar Modelo
```bash
ollama list
```

Deve aparecer `qwen2.5-coder:14b` ou `qwen2.5-coder:7b`

## Passo 4: Clonar Repositório

```bash
git clone <repository-url>
cd duilio-code-studio
```

## Passo 5: Criar Ambiente Virtual

### Criar Virtual Environment
```bash
python3 -m venv venv
```

### Ativar Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

Você deve ver `(venv)` no início do prompt.

## Passo 6: Instalar Dependências

### Atualizar pip
```bash
pip install --upgrade pip
```

### Instalar Dependências
```bash
pip install -r requirements.txt
```

Isso instala:
- FastAPI
- SQLAlchemy
- Alembic
- diskcache
- E todas as outras dependências

### Verificar Instalação
```bash
python3 -c "import fastapi; import sqlalchemy; print('✅ Dependências OK')"
```

## Passo 7: Configurar Ambiente (Opcional)

### Criar arquivo .env
```bash
cp .env.example .env  # Se existir
# Ou criar manualmente
```

### Editar .env
```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:14b

# Database
DATABASE_URL=sqlite:///./data/duiliocode.db

# Server
HOST=127.0.0.1
PORT=8080
```

## Passo 8: Inicializar Banco de Dados

### Automático (Recomendado)
O banco é criado automaticamente na primeira execução.

### Manual (Opcional)
```bash
cd src
python3 -c "from core.database import init_database; init_database()"
```

## Passo 9: Iniciar Servidor

### Usando Script (Recomendado)
```bash
./start.sh
```

### Manualmente
```bash
cd src
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8080 --reload
```

## Passo 10: Verificar Funcionamento

### 1. Abrir no Navegador
```
http://127.0.0.1:8080
```

### 2. Verificar Health Check
```bash
curl http://127.0.0.1:8080/health
```

Deve retornar:
```json
{"status": "ok", "service": "DuilioCode Studio"}
```

### 3. Verificar Ollama
```bash
curl http://127.0.0.1:8080/health/ollama
```

### 4. Testar Chat
1. Abra a interface web
2. Selecione um modelo
3. Digite uma mensagem
4. Verifique se recebe resposta

## Troubleshooting

### Erro: "Ollama not found"
```bash
# Verificar instalação
which ollama

# Reinstalar se necessário
brew install ollama  # macOS
```

### Erro: "Model not found"
```bash
# Listar modelos
ollama list

# Baixar modelo
ollama pull qwen2.5-coder:14b
```

### Erro: "Port 8080 already in use"
```bash
# Encontrar processo
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Matar processo ou mudar porta
# Edite .env: PORT=8081
```

### Erro: "Module not found"
```bash
# Verificar se venv está ativo
which python3  # Deve apontar para venv/bin/python3

# Reinstalar dependências
pip install -r requirements.txt
```

### Erro: "Database locked"
```bash
# Fechar outras conexões
# Ou deletar e recriar
rm data/duiliocode.db
# Reiniciar servidor
```

## Verificação Final

### Checklist
- [ ] Ollama instalado e rodando
- [ ] Modelo Qwen2.5-Coder baixado
- [ ] Python 3.9+ instalado
- [ ] Virtual environment criado e ativo
- [ ] Dependências instaladas
- [ ] Servidor iniciado sem erros
- [ ] Interface web acessível
- [ ] Health check retorna OK
- [ ] Chat funciona

## Próximos Passos

- [Primeiros Passos](03-primeiros-passos.md)
- [Arquitetura do Sistema](04-arquitetura.md)

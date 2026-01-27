# SQLite e SQLAlchemy

## O que é SQLite?

SQLite é um **banco de dados relacional** que armazena dados em um único arquivo. É perfeito para aplicações locais porque:
- ✅ Não precisa de servidor separado
- ✅ Arquivo único (fácil backup)
- ✅ Rápido para pequenos/médios volumes
- ✅ Suporta SQL completo

## O que é SQLAlchemy?

SQLAlchemy é um **ORM (Object-Relational Mapping)** para Python. Ele permite trabalhar com banco de dados usando **classes Python** ao invés de SQL direto.

## Por que Usamos?

### Antes (Sem Database)
- ❌ Preferências perdidas no restart
- ❌ Histórico de chat não persistia
- ❌ Métricas não eram salvas

### Agora (Com Database)
- ✅ Preferências persistem
- ✅ Histórico de chat salvo
- ✅ Métricas para análise

## Estrutura no DuilioCode

### 1. Database Setup

**Código**: `src/core/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cria engine (conexão com banco)
engine = create_engine("sqlite:///./data/duiliocode.db")

# Cria session factory
SessionLocal = sessionmaker(bind=engine)

# Cria tabelas
Base.metadata.create_all(bind=engine)
```

### 2. Modelos (Tabelas)

**Código**: `src/core/models.py`

```python
class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)
    key = Column(String)
    value = Column(Text)
    created_at = Column(DateTime)
```

### 3. Service Layer

**Código**: `src/services/database_service.py`

```python
class DatabaseService:
    def set_preference(self, user_id, key, value):
        db = get_db_session()
        # Salva no banco
        db.commit()
```

## Modelos de Dados

### 1. UserPreference

**O que armazena:**
- Preferências do usuário (tema, configurações, etc.)

**Estrutura:**
```python
{
    "id": 1,
    "user_id": "user123",
    "key": "theme",
    "value": "dark",
    "created_at": "2025-01-27T10:00:00"
}
```

**Uso:**
```python
db = get_database_service()
db.set_preference('user123', 'theme', 'dark')
theme = db.get_preference('user123', 'theme')  # 'dark'
```

### 2. ConversationHistory

**O que armazena:**
- Histórico completo de conversas
- Mensagens de usuário e assistente
- Metadados (modelo usado, tokens, etc.)

**Estrutura:**
```python
{
    "id": 1,
    "user_id": "user123",
    "session_id": "session456",
    "role": "user",
    "content": "crie um arquivo teste.txt",
    "model": "qwen2.5-coder:14b",
    "workspace_path": "/path/to/project",
    "extra_data": {"tokens": 150},
    "created_at": "2025-01-27T10:00:00"
}
```

**Uso:**
```python
db = get_database_service()
db.save_message('user123', 'session456', 'user', 'Hello')
history = db.get_conversation_history('user123', 'session456')
```

### 3. SystemMetric

**O que armazena:**
- Métricas de performance
- Duração de operações
- Taxa de erro

**Estrutura:**
```python
{
    "id": 1,
    "operation": "chat_completion",
    "duration_ms": 1234.5,
    "success": True,
    "error": None,
    "extra_data": {"tokens": 200},
    "created_at": "2025-01-27T10:00:00"
}
```

**Uso:**
```python
db = get_database_service()
db.save_metric('chat_completion', 1234.5, success=True)
metrics = db.get_metrics('chat_completion')
```

## Localização do Banco

### Padrão
```
data/duiliocode.db
```

### Configurável
```bash
# Via ambiente
DATABASE_URL=sqlite:///./meu_banco.db

# Via .env
DATABASE_URL=sqlite:///./custom/path/db.db
```

## Migrações com Alembic

### O que são Migrações?

Migrações são **mudanças no schema** do banco de dados. Permitem:
- Adicionar novas tabelas
- Adicionar/modificar colunas
- Manter histórico de mudanças

### Criar Migração

```bash
# Cria migração automática
alembic revision --autogenerate -m "add new column"

# Cria migração manual
alembic revision -m "create users table"
```

### Aplicar Migrações

```bash
# Aplica todas as migrações pendentes
alembic upgrade head

# Aplica até uma versão específica
alembic upgrade abc123

# Reverte última migração
alembic downgrade -1
```

### Estrutura de Migrações

```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_metrics.py
│   └── ...
├── env.py
└── script.py.mako
```

## Queries (Consultas)

### Exemplo: Buscar Preferências

```python
db = get_db_session()

# Buscar uma preferência
pref = db.query(UserPreference).filter(
    UserPreference.user_id == 'user123',
    UserPreference.key == 'theme'
).first()

if pref:
    print(pref.value)  # 'dark'
```

### Exemplo: Histórico Recente

```python
# Últimas 10 mensagens
messages = db.query(ConversationHistory).filter(
    ConversationHistory.user_id == 'user123'
).order_by(
    ConversationHistory.created_at.desc()
).limit(10).all()
```

### Exemplo: Métricas Agregadas

```python
from sqlalchemy import func

# Média de duração por operação
stats = db.query(
    SystemMetric.operation,
    func.avg(SystemMetric.duration_ms).label('avg_duration')
).group_by(
    SystemMetric.operation
).all()
```

## Transações

### O que são?

Transações garantem que **múltiplas operações** sejam executadas juntas ou nenhuma:

```python
db = get_db_session()
try:
    # Operação 1
    db.add(user_pref1)
    # Operação 2
    db.add(user_pref2)
    # Se tudo OK, salva
    db.commit()
except:
    # Se erro, desfaz tudo
    db.rollback()
finally:
    db.close()
```

## Performance

### Índices

Índices aceleram buscas:

```python
class ConversationHistory(Base):
    user_id = Column(String, index=True)  # ← Índice!
    session_id = Column(String, index=True)  # ← Índice!
    created_at = Column(DateTime, index=True)  # ← Índice!
```

### Connection Pooling

SQLAlchemy gerencia conexões automaticamente:

```python
engine = create_engine(
    "sqlite:///./data/duiliocode.db",
    poolclass=StaticPool,  # Para SQLite
    pool_size=5  # Máximo de conexões
)
```

## Backup e Restore

### Backup

```bash
# Simplesmente copiar o arquivo
cp data/duiliocode.db data/duiliocode.db.backup
```

### Restore

```bash
# Restaurar backup
cp data/duiliocode.db.backup data/duiliocode.db
```

## Troubleshooting

### Banco Corrompido

```bash
# SQLite tem comando de reparo
sqlite3 data/duiliocode.db ".recover" | sqlite3 data/duiliocode_fixed.db
```

### Resetar Banco

```bash
# Deletar e recriar
rm data/duiliocode.db
# Reiniciar servidor (cria automaticamente)
```

### Ver Dados

```bash
# Usar sqlite3 CLI
sqlite3 data/duiliocode.db

# Ver tabelas
.tables

# Ver dados
SELECT * FROM user_preferences;
```

## Próximos Passos

- [Modelos de Dados](20-modelos.md)
- [Migrações com Alembic](21-migracoes.md)

# SQLite and SQLAlchemy

## What is SQLite?

SQLite is a **relational database** that stores data in a single file. It's perfect for local applications because:
- ✅ No separate server needed
- ✅ Single file (easy backup)
- ✅ Fast for small/medium volumes
- ✅ Full SQL support

## What is SQLAlchemy?

SQLAlchemy is an **ORM (Object-Relational Mapping)** for Python. It allows working with databases using **Python classes** instead of direct SQL.

## Why Do We Use It?

### Before (Without Database)
- ❌ Preferences lost on restart
- ❌ Chat history didn't persist
- ❌ Metrics weren't saved

### Now (With Database)
- ✅ Preferences persist
- ✅ Chat history saved
- ✅ Metrics for analysis

## Structure in DuilioCode

### 1. Database Setup

**Code**: `src/core/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine (database connection)
engine = create_engine("sqlite:///./data/duiliocode.db")

# Create session factory
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
```

### 2. Models (Tables)

**Code**: `src/core/models.py`

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

**Code**: `src/services/database_service.py`

```python
class DatabaseService:
    def set_preference(self, user_id, key, value):
        db = get_db_session()
        # Saves to database
        db.commit()
```

## Data Models

### 1. UserPreference

**What it stores:**
- User preferences (theme, settings, etc.)

**Structure:**
```python
{
    "id": 1,
    "user_id": "user123",
    "key": "theme",
    "value": "dark",
    "created_at": "2025-01-27T10:00:00"
}
```

**Usage:**
```python
db = get_database_service()
db.set_preference('user123', 'theme', 'dark')
theme = db.get_preference('user123', 'theme')  # 'dark'
```

### 2. ConversationHistory

**What it stores:**
- Complete conversation history
- User and assistant messages
- Metadata (model used, tokens, etc.)

**Structure:**
```python
{
    "id": 1,
    "user_id": "user123",
    "session_id": "session456",
    "role": "user",
    "content": "create a file teste.txt",
    "model": "qwen2.5-coder:14b",
    "workspace_path": "/path/to/project",
    "extra_data": {"tokens": 150},
    "created_at": "2025-01-27T10:00:00"
}
```

**Usage:**
```python
db = get_database_service()
db.save_message('user123', 'session456', 'user', 'Hello')
history = db.get_conversation_history('user123', 'session456')
```

### 3. SystemMetric

**What it stores:**
- Performance metrics
- Operation duration
- Error rate

**Structure:**
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

**Usage:**
```python
db = get_database_service()
db.save_metric('chat_completion', 1234.5, success=True)
metrics = db.get_metrics('chat_completion')
```

## Database Location

### Default
```
data/duiliocode.db
```

### Configurable
```bash
# Via environment
DATABASE_URL=sqlite:///./my_database.db

# Via .env
DATABASE_URL=sqlite:///./custom/path/db.db
```

## Migrations with Alembic

### What Are Migrations?

Migrations are **changes to the database schema**. They allow:
- Adding new tables
- Adding/modifying columns
- Keeping change history

### Create Migration

```bash
# Create automatic migration
alembic revision --autogenerate -m "add new column"

# Create manual migration
alembic revision -m "create users table"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply up to specific version
alembic upgrade abc123

# Revert last migration
alembic downgrade -1
```

### Migration Structure

```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_metrics.py
│   └── ...
├── env.py
└── script.py.mako
```

## Queries

### Example: Get Preferences

```python
db = get_db_session()

# Get a preference
pref = db.query(UserPreference).filter(
    UserPreference.user_id == 'user123',
    UserPreference.key == 'theme'
).first()

if pref:
    print(pref.value)  # 'dark'
```

### Example: Recent History

```python
# Last 10 messages
messages = db.query(ConversationHistory).filter(
    ConversationHistory.user_id == 'user123'
).order_by(
    ConversationHistory.created_at.desc()
).limit(10).all()
```

### Example: Aggregated Metrics

```python
from sqlalchemy import func

# Average duration per operation
stats = db.query(
    SystemMetric.operation,
    func.avg(SystemMetric.duration_ms).label('avg_duration')
).group_by(
    SystemMetric.operation
).all()
```

## Transactions

### What Are They?

Transactions ensure that **multiple operations** are executed together or none:

```python
db = get_db_session()
try:
    # Operation 1
    db.add(user_pref1)
    # Operation 2
    db.add(user_pref2)
    # If all OK, save
    db.commit()
except:
    # If error, undo everything
    db.rollback()
finally:
    db.close()
```

## Performance

### Indexes

Indexes speed up searches:

```python
class ConversationHistory(Base):
    user_id = Column(String, index=True)  # ← Index!
    session_id = Column(String, index=True)  # ← Index!
    created_at = Column(DateTime, index=True)  # ← Index!
```

### Connection Pooling

SQLAlchemy manages connections automatically:

```python
engine = create_engine(
    "sqlite:///./data/duiliocode.db",
    poolclass=StaticPool,  # For SQLite
    pool_size=5  # Maximum connections
)
```

## Backup and Restore

### Backup

```bash
# Simply copy the file
cp data/duiliocode.db data/duiliocode.db.backup
```

### Restore

```bash
# Restore backup
cp data/duiliocode.db.backup data/duiliocode.db
```

## Troubleshooting

### Corrupted Database

```bash
# SQLite has repair command
sqlite3 data/duiliocode.db ".recover" | sqlite3 data/duiliocode_fixed.db
```

### Reset Database

```bash
# Delete and recreate
rm data/duiliocode.db
# Restart server (creates automatically)
```

### View Data

```bash
# Use sqlite3 CLI
sqlite3 data/duiliocode.db

# View tables
.tables

# View data
SELECT * FROM user_preferences;
```

## Next Steps

- [Data Models](20-models.md)
- [Migrations with Alembic](21-migrations.md)

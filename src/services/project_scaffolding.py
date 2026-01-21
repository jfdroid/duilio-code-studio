"""
Project Scaffolding Service
===========================
Generate complete project structures from templates.
Supports multiple frameworks and languages.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProjectTemplate:
    """A project template definition."""
    name: str
    description: str
    language: str
    framework: Optional[str]
    files: Dict[str, str]  # path -> content
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)
    post_create_commands: List[str] = field(default_factory=list)


class ProjectScaffolder:
    """
    Service for generating project scaffolds.
    
    Templates available:
    - Python: FastAPI, Flask, Django, CLI
    - JavaScript: React, Vue, Express, Node CLI
    - Kotlin: Android, Ktor
    - General: Monorepo, Library
    """
    
    def __init__(self):
        """Initialize scaffolder with built-in templates."""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, ProjectTemplate]:
        """Load all built-in templates."""
        return {
            'fastapi': self._template_fastapi(),
            'fastapi-full': self._template_fastapi_full(),
            'flask': self._template_flask(),
            'python-cli': self._template_python_cli(),
            'python-lib': self._template_python_library(),
            'express': self._template_express(),
            'react': self._template_react(),
            'node-cli': self._template_node_cli(),
            'typescript-lib': self._template_typescript_library(),
        }
    
    # === Python Templates ===
    
    def _template_fastapi(self) -> ProjectTemplate:
        """Basic FastAPI project."""
        return ProjectTemplate(
            name="FastAPI Basic",
            description="Simple FastAPI REST API project",
            language="python",
            framework="fastapi",
            dependencies=[
                'fastapi>=0.100.0',
                'uvicorn[standard]>=0.22.0',
                'pydantic>=2.0.0',
            ],
            dev_dependencies=[
                'pytest>=7.0.0',
                'httpx>=0.24.0',
                'black>=23.0.0',
                'ruff>=0.0.280',
            ],
            files={
                'src/__init__.py': '',
                'src/main.py': '''"""
FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="${project_name}",
    description="${project_description}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to ${project_name}!"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
                'src/routes/__init__.py': '',
                'src/routes/api.py': '''"""
API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["API"])


class Item(BaseModel):
    name: str
    description: str = ""
    price: float


items_db = []


@router.get("/items")
async def list_items():
    """List all items."""
    return {"items": items_db}


@router.post("/items")
async def create_item(item: Item):
    """Create a new item."""
    items_db.append(item.dict())
    return {"message": "Item created", "item": item}


@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item by ID."""
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]
''',
                'tests/__init__.py': '',
                'tests/test_main.py': '''"""
Tests for main application.
"""
import pytest
from httpx import AsyncClient
from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
''',
                'requirements.txt': '''fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
''',
                'requirements-dev.txt': '''pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
black>=23.0.0
ruff>=0.0.280
''',
                '.gitignore': '''__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
''',
                'README.md': '''# ${project_name}

${project_description}

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn src.main:app --reload
```

## Test

```bash
pytest
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
''',
                'pyproject.toml': '''[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I"]
''',
            },
            scripts={
                'start': 'uvicorn src.main:app --reload',
                'test': 'pytest',
                'lint': 'ruff check src tests',
                'format': 'black src tests',
            },
            post_create_commands=[
                'python -m venv venv',
                'pip install -r requirements.txt',
            ]
        )
    
    def _template_fastapi_full(self) -> ProjectTemplate:
        """Full FastAPI project with auth, database, etc."""
        base = self._template_fastapi()
        base.name = "FastAPI Full"
        base.description = "Complete FastAPI with auth, database, and more"
        base.dependencies.extend([
            'sqlalchemy>=2.0.0',
            'alembic>=1.11.0',
            'python-jose[cryptography]>=3.3.0',
            'passlib[bcrypt]>=1.7.0',
            'python-multipart>=0.0.6',
        ])
        base.files.update({
            'src/database.py': '''"""
Database configuration.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
            'src/models/__init__.py': '',
            'src/models/user.py': '''"""
User model.
"""
from sqlalchemy import Column, Integer, String, Boolean
from src.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
''',
            'src/auth/__init__.py': '',
            'src/auth/security.py': '''"""
Security utilities.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here"  # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
''',
            'alembic.ini': '''# Alembic configuration
[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./app.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
''',
        })
        return base
    
    def _template_flask(self) -> ProjectTemplate:
        """Flask project template."""
        return ProjectTemplate(
            name="Flask Basic",
            description="Simple Flask web application",
            language="python",
            framework="flask",
            dependencies=[
                'flask>=2.3.0',
                'flask-cors>=4.0.0',
                'python-dotenv>=1.0.0',
            ],
            files={
                'app/__init__.py': '''"""
Flask application factory.
"""
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    from app.routes import main
    app.register_blueprint(main.bp)
    
    return app
''',
                'app/routes/__init__.py': '',
                'app/routes/main.py': '''"""
Main routes.
"""
from flask import Blueprint, jsonify

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return jsonify({"message": "Welcome to ${project_name}!"})


@bp.route('/health')
def health():
    return jsonify({"status": "healthy"})
''',
                'run.py': '''"""
Run the Flask application.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
''',
                'requirements.txt': '''flask>=2.3.0
flask-cors>=4.0.0
python-dotenv>=1.0.0
gunicorn>=21.0.0
''',
                '.gitignore': '''__pycache__/
*.py[cod]
.env
.venv/
venv/
instance/
.pytest_cache/
''',
                'README.md': '''# ${project_name}

${project_description}

## Run

```bash
pip install -r requirements.txt
python run.py
```
''',
            }
        )
    
    def _template_python_cli(self) -> ProjectTemplate:
        """Python CLI application."""
        return ProjectTemplate(
            name="Python CLI",
            description="Command-line application with Click",
            language="python",
            framework="click",
            dependencies=[
                'click>=8.1.0',
                'rich>=13.0.0',
            ],
            files={
                'src/__init__.py': '',
                'src/cli.py': '''"""
CLI Application
"""
import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """${project_name} - ${project_description}"""
    pass


@cli.command()
@click.argument('name')
def hello(name: str):
    """Say hello to NAME."""
    console.print(f"[bold green]Hello, {name}![/bold green]")


@cli.command()
@click.option('--count', '-c', default=5, help='Number of items')
def list_items(count: int):
    """List sample items."""
    table = Table(title="Items")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    
    for i in range(count):
        table.add_row(str(i + 1), f"Item {i + 1}")
    
    console.print(table)


if __name__ == '__main__':
    cli()
''',
                'pyproject.toml': '''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "${project_name}"
version = "1.0.0"
description = "${project_description}"
requires-python = ">=3.9"
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
]

[project.scripts]
${project_name} = "src.cli:cli"
''',
                'README.md': '''# ${project_name}

${project_description}

## Install

```bash
pip install -e .
```

## Usage

```bash
${project_name} --help
${project_name} hello World
${project_name} list-items --count 10
```
''',
            }
        )
    
    def _template_python_library(self) -> ProjectTemplate:
        """Python library template."""
        return ProjectTemplate(
            name="Python Library",
            description="Reusable Python library package",
            language="python",
            framework=None,
            files={
                'src/${project_name}/__init__.py': '''"""
${project_name} - ${project_description}
"""

__version__ = "1.0.0"

from .core import *
''',
                'src/${project_name}/core.py': '''"""
Core functionality.
"""

def hello(name: str = "World") -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


class Calculator:
    """Simple calculator class."""
    
    @staticmethod
    def add(a: float, b: float) -> float:
        return a + b
    
    @staticmethod
    def subtract(a: float, b: float) -> float:
        return a - b
    
    @staticmethod
    def multiply(a: float, b: float) -> float:
        return a * b
    
    @staticmethod
    def divide(a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
''',
                'tests/__init__.py': '',
                'tests/test_core.py': '''"""
Tests for core module.
"""
import pytest
from ${project_name} import hello
from ${project_name}.core import Calculator


def test_hello():
    assert hello() == "Hello, World!"
    assert hello("Python") == "Hello, Python!"


class TestCalculator:
    def test_add(self):
        assert Calculator.add(2, 3) == 5
    
    def test_divide_by_zero(self):
        with pytest.raises(ValueError):
            Calculator.divide(10, 0)
''',
                'pyproject.toml': '''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "${project_name}"
version = "1.0.0"
description = "${project_description}"
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=23.0.0", "ruff>=0.0.280"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.black]
line-length = 100
''',
                'README.md': '''# ${project_name}

${project_description}

## Install

```bash
pip install ${project_name}
```

## Usage

```python
from ${project_name} import hello
from ${project_name}.core import Calculator

print(hello("World"))

calc = Calculator()
print(calc.add(2, 3))
```
''',
                'LICENSE': '''MIT License

Copyright (c) ${year} ${author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
''',
            }
        )
    
    # === JavaScript/Node Templates ===
    
    def _template_express(self) -> ProjectTemplate:
        """Express.js API template."""
        return ProjectTemplate(
            name="Express API",
            description="REST API with Express.js",
            language="javascript",
            framework="express",
            dependencies=[
                'express',
                'cors',
                'helmet',
                'morgan',
                'dotenv',
            ],
            dev_dependencies=[
                'nodemon',
                'jest',
                'supertest',
            ],
            files={
                'src/index.js': '''/**
 * ${project_name} - Express Server
 */
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const routes = require('./routes');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());

// Routes
app.use('/api', routes);

app.get('/', (req, res) => {
    res.json({ message: 'Welcome to ${project_name}!' });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

// Error handler
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

module.exports = app;
''',
                'src/routes/index.js': '''/**
 * API Routes
 */
const express = require('express');
const router = express.Router();

const items = [];

router.get('/items', (req, res) => {
    res.json({ items });
});

router.post('/items', (req, res) => {
    const item = req.body;
    items.push(item);
    res.status(201).json({ message: 'Item created', item });
});

router.get('/items/:id', (req, res) => {
    const { id } = req.params;
    if (id >= items.length) {
        return res.status(404).json({ error: 'Item not found' });
    }
    res.json(items[id]);
});

module.exports = router;
''',
                'tests/app.test.js': '''/**
 * API Tests
 */
const request = require('supertest');
const app = require('../src/index');

describe('API Endpoints', () => {
    test('GET / returns welcome message', async () => {
        const res = await request(app).get('/');
        expect(res.statusCode).toBe(200);
        expect(res.body.message).toBeDefined();
    });

    test('GET /health returns healthy', async () => {
        const res = await request(app).get('/health');
        expect(res.statusCode).toBe(200);
        expect(res.body.status).toBe('healthy');
    });
});
''',
                'package.json': '''{
  "name": "${project_name}",
  "version": "1.0.0",
  "description": "${project_description}",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest"
  },
  "keywords": [],
  "author": "${author}",
  "license": "MIT"
}
''',
                '.env.example': '''PORT=3000
NODE_ENV=development
''',
                '.gitignore': '''node_modules/
.env
coverage/
dist/
*.log
''',
                'README.md': '''# ${project_name}

${project_description}

## Setup

```bash
npm install
cp .env.example .env
```

## Run

```bash
npm run dev
```

## Test

```bash
npm test
```
''',
            },
            scripts={
                'start': 'node src/index.js',
                'dev': 'nodemon src/index.js',
                'test': 'jest',
            },
            post_create_commands=['npm install']
        )
    
    def _template_react(self) -> ProjectTemplate:
        """React application template (Vite-based)."""
        return ProjectTemplate(
            name="React App",
            description="React application with Vite",
            language="javascript",
            framework="react",
            files={
                'index.html': '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''',
                'src/main.jsx': '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',
                'src/App.jsx': '''import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="app">
      <h1>${project_name}</h1>
      <p>${project_description}</p>
      
      <div className="card">
        <button onClick={() => setCount(c => c + 1)}>
          Count: {count}
        </button>
      </div>
    </div>
  )
}

export default App
''',
                'src/App.css': '''.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.card {
  padding: 2rem;
}

button {
  padding: 0.6rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
  border: 1px solid transparent;
  border-radius: 8px;
  background-color: #1a1a1a;
  color: white;
  transition: all 0.2s;
}

button:hover {
  border-color: #646cff;
  background-color: #2a2a2a;
}
''',
                'src/index.css': ''':root {
  font-family: Inter, system-ui, sans-serif;
  line-height: 1.5;
  color: #213547;
  background-color: #ffffff;
}

body {
  margin: 0;
  min-height: 100vh;
}
''',
                'package.json': '''{
  "name": "${project_name}",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.4.0"
  }
}
''',
                'vite.config.js': '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''',
                '.gitignore': '''node_modules/
dist/
.env
*.log
''',
                'README.md': '''# ${project_name}

${project_description}

## Setup

```bash
npm install
```

## Run

```bash
npm run dev
```

## Build

```bash
npm run build
```
''',
            },
            scripts={
                'dev': 'vite',
                'build': 'vite build',
            },
            post_create_commands=['npm install']
        )
    
    def _template_node_cli(self) -> ProjectTemplate:
        """Node.js CLI application."""
        return ProjectTemplate(
            name="Node CLI",
            description="Command-line application with Node.js",
            language="javascript",
            framework="commander",
            files={
                'src/index.js': '''#!/usr/bin/env node
/**
 * ${project_name} CLI
 */
const { Command } = require('commander');
const chalk = require('chalk');

const program = new Command();

program
    .name('${project_name}')
    .description('${project_description}')
    .version('1.0.0');

program
    .command('hello <name>')
    .description('Say hello')
    .action((name) => {
        console.log(chalk.green(`Hello, ${name}!`));
    });

program
    .command('list')
    .description('List items')
    .option('-c, --count <number>', 'number of items', '5')
    .action((options) => {
        const count = parseInt(options.count);
        console.log(chalk.blue('\\nItems:'));
        for (let i = 1; i <= count; i++) {
            console.log(`  ${i}. Item ${i}`);
        }
    });

program.parse();
''',
                'package.json': '''{
  "name": "${project_name}",
  "version": "1.0.0",
  "description": "${project_description}",
  "bin": {
    "${project_name}": "src/index.js"
  },
  "dependencies": {
    "commander": "^11.0.0",
    "chalk": "^4.1.2"
  }
}
''',
                'README.md': '''# ${project_name}

${project_description}

## Install

```bash
npm install -g .
```

## Usage

```bash
${project_name} --help
${project_name} hello World
${project_name} list --count 10
```
''',
            },
            post_create_commands=['npm install']
        )
    
    def _template_typescript_library(self) -> ProjectTemplate:
        """TypeScript library template."""
        return ProjectTemplate(
            name="TypeScript Library",
            description="Reusable TypeScript library",
            language="typescript",
            framework=None,
            files={
                'src/index.ts': '''/**
 * ${project_name}
 * ${project_description}
 */

export function hello(name: string = 'World'): string {
    return `Hello, ${name}!`;
}

export class Calculator {
    add(a: number, b: number): number {
        return a + b;
    }
    
    subtract(a: number, b: number): number {
        return a - b;
    }
    
    multiply(a: number, b: number): number {
        return a * b;
    }
    
    divide(a: number, b: number): number {
        if (b === 0) throw new Error('Cannot divide by zero');
        return a / b;
    }
}
''',
                'tests/index.test.ts': '''import { hello, Calculator } from '../src';

describe('hello', () => {
    it('returns greeting', () => {
        expect(hello()).toBe('Hello, World!');
        expect(hello('TypeScript')).toBe('Hello, TypeScript!');
    });
});

describe('Calculator', () => {
    const calc = new Calculator();
    
    it('adds numbers', () => {
        expect(calc.add(2, 3)).toBe(5);
    });
    
    it('throws on divide by zero', () => {
        expect(() => calc.divide(10, 0)).toThrow();
    });
});
''',
                'package.json': '''{
  "name": "${project_name}",
  "version": "1.0.0",
  "description": "${project_description}",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "prepublishOnly": "npm run build"
  },
  "devDependencies": {
    "@types/jest": "^29.5.0",
    "@types/node": "^20.0.0",
    "jest": "^29.5.0",
    "ts-jest": "^29.1.0",
    "typescript": "^5.0.0"
  }
}
''',
                'tsconfig.json': '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "declaration": true,
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
''',
                'jest.config.js': '''module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
};
''',
                '.gitignore': '''node_modules/
dist/
*.log
''',
                'README.md': '''# ${project_name}

${project_description}

## Install

```bash
npm install ${project_name}
```

## Usage

```typescript
import { hello, Calculator } from '${project_name}';

console.log(hello('World'));

const calc = new Calculator();
console.log(calc.add(2, 3));
```
''',
            },
            post_create_commands=['npm install']
        )
    
    # === Scaffold Methods ===
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        return [
            {
                'id': key,
                'name': template.name,
                'description': template.description,
                'language': template.language,
                'framework': template.framework,
            }
            for key, template in self.templates.items()
        ]
    
    def create_project(
        self,
        template_id: str,
        target_path: str,
        project_name: str,
        project_description: str = "",
        author: str = "DuilioCode User",
        variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new project from template.
        
        Args:
            template_id: ID of the template to use
            target_path: Directory to create project in
            project_name: Name of the project
            project_description: Description of the project
            author: Author name
            variables: Additional template variables
            
        Returns:
            Dict with created files and status
        """
        if template_id not in self.templates:
            return {
                'success': False,
                'error': f"Template not found: {template_id}",
                'available': list(self.templates.keys())
            }
        
        template = self.templates[template_id]
        target = Path(target_path).resolve()
        
        # Create target directory
        target.mkdir(parents=True, exist_ok=True)
        
        # Prepare variables
        vars = {
            'project_name': project_name,
            'project_description': project_description or f"A {template.name} project",
            'author': author,
            'year': str(datetime.now().year),
            **(variables or {})
        }
        
        created_files = []
        errors = []
        
        # Create each file
        for file_path, content in template.files.items():
            try:
                # Replace variables in path and content
                actual_path = file_path
                for var, value in vars.items():
                    actual_path = actual_path.replace(f'${{{var}}}', value)
                    content = content.replace(f'${{{var}}}', value)
                
                # Create file
                full_path = target / actual_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                
                created_files.append(str(actual_path))
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'template': template.name,
            'path': str(target),
            'files_created': created_files,
            'total_files': len(created_files),
            'errors': errors,
            'post_create_commands': template.post_create_commands,
            'scripts': template.scripts
        }


# Singleton instance
_scaffolder: Optional[ProjectScaffolder] = None


def get_project_scaffolder() -> ProjectScaffolder:
    """Get project scaffolder instance."""
    global _scaffolder
    if _scaffolder is None:
        _scaffolder = ProjectScaffolder()
    return _scaffolder

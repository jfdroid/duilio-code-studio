# CRUD - Criar, Ler, Atualizar, Deletar

## O que é CRUD?

CRUD são as **4 operações básicas** que você pode fazer com arquivos:
- **C**reate (Criar)
- **R**ead (Ler)
- **U**pdate (Atualizar)
- **D**elete (Deletar)

## Como Funciona no DuilioCode?

### 1. CREATE (Criar)

#### Criar Arquivo

**Você pede:**
```
"crie um arquivo teste.txt com 'Hello World'"
```

**DuilioCode detecta:**
- Intenção: `create = True`
- Tipo: arquivo
- Nome: `teste.txt`
- Conteúdo: `Hello World`

**DuilioCode gera:**
```
```create-file:teste.txt
Hello World
```
```

**Action Processor executa:**
```python
# src/services/action_processor.py
def execute_create_file(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content)
```

**Resultado:**
✅ Arquivo `teste.txt` criado com sucesso!

#### Criar Diretório

**Você pede:**
```
"crie o diretorio projeto-teste"
```

**DuilioCode detecta:**
- Intenção: `create_directory = True`
- Nome: `projeto-teste`

**DuilioCode gera:**
```
```create-directory:projeto-teste
```
```

**Action Processor executa:**
```python
Path("projeto-teste").mkdir(parents=True, exist_ok=True)
```

**Resultado:**
✅ Diretório `projeto-teste` criado!

### 2. READ (Ler)

**Você pede:**
```
"mostre o conteúdo do arquivo app.js"
```

**DuilioCode detecta:**
- Intenção: `read = True`
- Arquivo: `app.js`

**DuilioCode lê:**
```python
# src/api/routes/chat/chat_handler.py
file_content = read_file("app.js", workspace_path)
```

**DuilioCode responde:**
```
O arquivo app.js contém:

```javascript
function App() {
  return <div>Hello</div>;
}
```
```

### 3. UPDATE (Atualizar)

**Você pede:**
```
"adicione uma função de validação no arquivo utils.js"
```

**DuilioCode detecta:**
- Intenção: `update = True`
- Arquivo: `utils.js`
- Ação: adicionar função

**DuilioCode:**
1. Lê o arquivo atual
2. Gera código com a função adicionada
3. Gera ação:

```
```modify-file:utils.js
// Código existente + nova função
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
```
```

**Action Processor executa:**
```python
# Substitui arquivo completo com novo conteúdo
Path("utils.js").write_text(new_content)
```

**Resultado:**
✅ Arquivo atualizado!

### 4. DELETE (Deletar)

**Você pede:**
```
"delete o arquivo teste.txt"
```

**DuilioCode detecta:**
- Intenção: `delete = True`
- Arquivo: `teste.txt`

**DuilioCode gera:**
```
```delete-file:teste.txt
```
```

**Action Processor executa:**
```python
Path("teste.txt").unlink()  # Deleta arquivo
```

**Resultado:**
✅ Arquivo deletado!

## Detecção de Intenção

### Como Detectamos?

**Código**: `src/api/routes/chat/chat_handler.py`

```python
def _detect_crud_intent(self, message: str):
    message_lower = message.lower()
    
    create_keywords = [
        'criar arquivo', 'create file', 'criar pasta',
        'crie um', 'criar um', 'novo arquivo'
    ]
    
    read_keywords = [
        'ler arquivo', 'read file', 'ver arquivo',
        'mostrar arquivo', 'conteúdo do arquivo'
    ]
    
    update_keywords = [
        'modificar arquivo', 'edit file', 'atualizar',
        'adicionar', 'alterar'
    ]
    
    delete_keywords = [
        'deletar arquivo', 'delete file', 'remover',
        'apagar', 'excluir'
    ]
    
    return {
        'create': any(kw in message_lower for kw in create_keywords),
        'read': any(kw in message_lower for kw in read_keywords),
        'update': any(kw in message_lower for kw in update_keywords),
        'delete': any(kw in message_lower for kw in delete_keywords)
    }
```

## Formatos de Ação

### CREATE FILE
```
```create-file:path/to/file.ext
[conteúdo completo do arquivo]
```
```

### CREATE DIRECTORY
```
```create-directory:path/to/dir
```
```

### MODIFY FILE
```
```modify-file:path/to/file.ext
[conteúdo COMPLETO do arquivo com alterações]
```
```

### DELETE FILE
```
```delete-file:path/to/file.ext
```
```

### DELETE DIRECTORY
```
```delete-directory:path/to/dir
```
```

## Action Processor

### O que é?

Action Processor é o **executor de ações**. Ele:
1. Lê as ações geradas pela IA
2. Valida segurança (path traversal, etc.)
3. Executa no sistema de arquivos
4. Retorna resultado

**Código**: `src/services/action_processor.py`

```python
class ActionProcessor:
    def extract_actions(self, response_text: str):
        # Procura por ```create-file:, ```modify-file:, etc.
        patterns = [
            r'```create-file:([^\n]+)\n([\s\S]*?)```',
            r'```create-directory:([^\n]+)```',
            # ...
        ]
        # Extrai todas as ações
        return actions
    
    async def process_actions(self, response_text, workspace_path):
        actions = self.extract_actions(response_text)
        
        for action in actions:
            if action['type'] == 'create-file':
                self.create_file(action['path'], action['content'])
            elif action['type'] == 'create-directory':
                self.create_directory(action['path'])
            # ...
        
        return {"success": True, "actions_executed": len(actions)}
```

## Segurança

### Validações

1. **Path Traversal**: Impede `../../../etc/passwd`
2. **Workspace Boundary**: Só permite dentro do workspace
3. **File Size**: Limite de tamanho de arquivo
4. **Permissions**: Verifica permissões antes de escrever

**Código**: `src/core/security.py`

```python
def sanitize_path(path, workspace_path):
    # Remove path traversal
    if '../' in path:
        raise ValueError("Path traversal detected")
    
    # Garante que está dentro do workspace
    normalized = Path(path).resolve()
    workspace_root = Path(workspace_path).resolve()
    
    if not str(normalized).startswith(str(workspace_root)):
        raise ValueError("Path outside workspace")
    
    return str(normalized)
```

## Exemplos Completos

### Criar Projeto React Completo

**Input:**
```
"crie um projeto React completo chamado meu-app"
```

**Processamento:**
1. Detecta: `create = True`, `project = True`
2. Gera múltiplas ações:
   ```
   ```create-directory:meu-app
   ```
   ```create-file:meu-app/package.json
   {...}
   ```
   ```create-file:meu-app/src/index.js
   ...
   ```
   ```
3. Executa todas as ações
4. Projeto completo criado!

### Modificar Múltiplos Arquivos

**Input:**
```
"adicione validação em todos os arquivos de formulário"
```

**Processamento:**
1. Detecta: `update = True`
2. Encontra arquivos de formulário
3. Lê cada arquivo
4. Adiciona validação
5. Gera ações `modify-file` para cada um
6. Executa todas

## Próximos Passos

- [Action Processor - Execução Automática](14-action-processor.md)
- [Workspace Service - Gerenciamento de Projetos](15-workspace.md)

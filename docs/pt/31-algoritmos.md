# Algoritmos Complexos

## Visão Geral

DuilioCode usa vários algoritmos complexos para processar código, entender intenções e executar ações. Este documento explica os principais.

## 1. Dependency Graph (Grafo de Dependências)

### O que é?

Um **grafo de dependências** mostra quais arquivos dependem de quais outros arquivos.

### Por que Precisamos?

Ao criar múltiplos arquivos, precisamos criar na **ordem correta**:
- Arquivo A importa Arquivo B
- Precisamos criar B antes de A

### Como Funciona?

**Código**: `src/services/dependency_graph.py`

```python
class FileDependencyGraph:
    def build_graph(self, files):
        # Analisa imports em cada arquivo
        graph = {}
        for file in files:
            imports = self.extract_imports(file)
            graph[file] = imports
        
        # Ordena topologicamente
        return self.topological_sort(graph)
    
    def topological_sort(self, graph):
        # Ordena para que dependências venham antes
        # Exemplo: [B, A] se A depende de B
        return sorted_order
```

### Exemplo

**Arquivos:**
- `utils.js` (sem dependências)
- `app.js` (importa `utils.js`)
- `main.js` (importa `app.js`)

**Ordem de Criação:**
1. `utils.js` (primeiro)
2. `app.js` (segundo)
3. `main.js` (terceiro)

## 2. File Tree Traversal (Navegação de Árvore)

### O que é?

Algoritmo para **navegar** pela estrutura de pastas e contar arquivos.

### Problema

Contar arquivos recursivamente pode ser **muito lento** em projetos grandes.

### Solução: Limite de Profundidade

**Código**: `src/api/routes/chat/chat_handler.py`

```python
def count_files_accurate(path: Path, max_files: int = 50000):
    files_count = 0
    folders_count = 0
    
    def scan(p: Path, depth: int = 0):
        nonlocal files_count, folders_count
        
        # Limite de profundidade (evita loops infinitos)
        if depth > 15:
            return
        
        # Limite de arquivos (evita travamento)
        if files_count > max_files:
            return
        
        for item in p.iterdir():
            if item.is_dir():
                folders_count += 1
                scan(item, depth + 1)  # Recursivo
            elif item.is_file():
                files_count += 1
    
    scan(path)
    return files_count, folders_count
```

### Otimizações

1. **Skip dot-files**: Ignora `.git`, `.node_modules`, etc.
2. **Depth limit**: Máximo 15 níveis
3. **File limit**: Máximo 50,000 arquivos
4. **Early return**: Para quando atinge limites

## 3. Intent Detection (Detecção de Intenção)

### O que é?

Algoritmo que **entende o que o usuário quer fazer** baseado na mensagem.

### Abordagem Híbrida

Combinamos **3 métodos**:

#### 1. Keyword Matching (Simples)
```python
if 'criar arquivo' in message:
    return 'create'
```

#### 2. Linguistic Analysis (Avançado)
```python
# Analisa verbos, conectores, padrões
analysis = linguistic_analyzer.analyze(message)
if analysis.requires_action:
    return 'create'
```

#### 3. AI Classification (Inteligente)
```python
# Usa IA para classificar
classification = await ollama.classify(message)
return classification.intent
```

### Algoritmo de Decisão

```python
def detect_intent(message):
    # 1. Tenta keyword matching (rápido)
    simple_intent = keyword_match(message)
    if simple_intent and confidence > 0.8:
        return simple_intent
    
    # 2. Tenta linguistic analysis (médio)
    linguistic_intent = linguistic_analyze(message)
    if linguistic_intent.confidence > 0.7:
        return linguistic_intent.intent
    
    # 3. Usa IA (lento, mas preciso)
    ai_intent = await ai_classify(message)
    return ai_intent
```

## 4. Context Building (Construção de Contexto)

### Problema

Prompts muito grandes = **lento e caro**

### Solução: Context Relevance

**Código**: `src/api/routes/chat/context_builder.py`

```python
def build_codebase_context(workspace_path, query=None):
    # 1. Analisa codebase
    files = analyze_codebase(workspace_path)
    
    # 2. Se tem query, filtra por relevância
    if query:
        files = filter_by_relevance(files, query)
    
    # 3. Limita tamanho
    files = files[:100]  # Máximo 100 arquivos
    
    # 4. Formata para prompt
    return format_for_prompt(files)
```

### Algoritmo de Relevância

```python
def filter_by_relevance(files, query):
    scores = []
    for file in files:
        # Score baseado em:
        # - Nome do arquivo contém palavras da query
        # - Conteúdo do arquivo contém palavras da query
        # - Caminho do arquivo é relevante
        score = calculate_relevance(file, query)
        scores.append((file, score))
    
    # Ordena por score e retorna top N
    scores.sort(key=lambda x: x[1], reverse=True)
    return [f for f, s in scores[:50]]
```

## 5. Action Extraction (Extração de Ações)

### Problema

IA pode gerar ações em **vários formatos**:
- ````create-file:path\ncontent\n````
- `create-file:path` (sem backticks)
- Múltiplas ações misturadas

### Solução: Regex Multi-Pattern

**Código**: `src/services/action_processor.py`

```python
def extract_actions(self, response_text: str):
    actions = []
    
    # Pattern 1: ```create-file:path\ncontent\n```
    pattern1 = r'```create-file:([^\n]+)\n([\s\S]*?)```'
    matches1 = re.finditer(pattern1, response_text)
    for match in matches1:
        actions.append({
            'type': 'create-file',
            'path': match.group(1),
            'content': match.group(2)
        })
    
    # Pattern 2: create-file:path (sem backticks)
    pattern2 = r'create-file:([^\n]+)'
    matches2 = re.finditer(pattern2, response_text)
    # ...
    
    # Pattern 3: create-directory:path
    pattern3 = r'```create-directory:([^\n]+)```'
    # ...
    
    return actions
```

### Ordenação por Dependências

```python
def order_actions(actions):
    # Separa por tipo
    directories = [a for a in actions if a['type'] == 'create-directory']
    files = [a for a in actions if a['type'] == 'create-file']
    
    # Ordena arquivos por dependências
    ordered_files = dependency_sort(files)
    
    # Retorna: diretórios primeiro, depois arquivos ordenados
    return directories + ordered_files
```

## 6. Cache Strategy (Estratégia de Cache)

### Problema

Analisar codebase é **caro** (lento). Não queremos fazer toda vez.

### Solução: Multi-Layer Cache

**Código**: `src/services/cache_service.py`

```python
class CacheService:
    def __init__(self):
        # Layer 1: Memória (LRU cache)
        self.memory_cache = {}
        
        # Layer 2: Disco (diskcache)
        self.disk_cache = diskcache.Cache('.cache/duiliocode')
    
    def get(self, key):
        # 1. Tenta memória (mais rápido)
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # 2. Tenta disco (rápido)
        if key in self.disk_cache:
            value = self.disk_cache[key]
            # Promove para memória
            self.memory_cache[key] = value
            return value
        
        # 3. Não encontrou
        return None
    
    def set(self, key, value, ttl=3600):
        # Salva em ambos
        self.memory_cache[key] = value
        self.disk_cache.set(key, value, expire=ttl)
```

### TTL (Time To Live)

```python
# Cache expira após 1 hora
cache.set('codebase_context', context, ttl=3600)

# Após 1 hora, precisa recalcular
```

## 7. Prompt Optimization (Otimização de Prompts)

### Problema

Prompts muito longos = **lento e caro**

### Solução: Prompt Builder

**Código**: `src/services/prompt_builder.py`

```python
class PromptBuilder:
    @staticmethod
    def build_crud_prompt(operation, context):
        # Base prompt (curto)
        prompt = BASE_SYSTEM_PROMPT
        
        # Adiciona apenas o necessário
        if operation == OperationType.CREATE:
            prompt += _build_create_prompt(context)
        elif operation == OperationType.READ:
            prompt += _build_read_prompt(context)
        # ...
        
        return prompt  # Otimizado, não verboso
```

### Estratégias

1. **Operation-Specific**: Prompts diferentes por operação
2. **Context-Aware**: Adiciona contexto apenas se necessário
3. **Minimal**: Remove boilerplate desnecessário

## 8. Path Intelligence (Inteligência de Caminhos)

### Problema

Usuário diz: "crie arquivo teste.js"
- Onde criar? Raiz? `src/`? `components/`?

### Solução: Análise de Contexto

**Código**: `src/services/path_intelligence.py`

```python
class PathIntelligence:
    @classmethod
    def detect_path_intention(cls, prompt, filename):
        # Padrões que indicam subdiretório
        if 'src/' in prompt or 'components/' in prompt:
            return f"src/{filename}", False
        
        # Padrões que indicam raiz
        if 'arquivo chamado' in prompt:
            return filename, True
        
        # Padrões que indicam projeto paralelo
        if 'paralelo' in prompt or 'fora' in prompt:
            return f"/absolute/path/{filename}", False
        
        # Default: raiz
        return filename, True
```

## 9. Codebase Analysis (Análise de Codebase)

### Algoritmo de Análise

```python
def analyze_codebase(path, max_files=100):
    # 1. Coleta arquivos
    files = collect_files(path, max_files)
    
    # 2. Agrupa por linguagem
    by_language = group_by_language(files)
    
    # 3. Identifica entry points
    entry_points = find_entry_points(files)
    
    # 4. Analisa dependências
    dependencies = analyze_dependencies(files)
    
    # 5. Gera contexto estruturado
    return format_context(
        files=files,
        languages=by_language,
        entry_points=entry_points,
        dependencies=dependencies
    )
```

## 10. Temperature Adjustment (Ajuste de Temperatura)

### Algoritmo

```python
def adjust_temperature(message, base_temp=0.7):
    # Listagem de arquivos: precisa de precisão
    if is_file_listing_request(message):
        return 0.2  # Muito determinístico
    
    # Geração de código: precisa de criatividade controlada
    if is_code_generation(message):
        return 0.7  # Balanceado
    
    # Explicações: pode ser mais criativo
    if is_explanation_request(message):
        return 0.9  # Mais natural
    
    return base_temp
```

## Performance Considerations

### Big O Notation

- **File Tree Traversal**: O(n) onde n = número de arquivos
- **Dependency Sort**: O(V + E) onde V = vértices, E = arestas
- **Intent Detection**: O(1) para keywords, O(n) para linguistic
- **Context Building**: O(n) onde n = arquivos analisados

### Otimizações Aplicadas

1. **Caching**: Evita recálculos
2. **Early Returns**: Para quando possível
3. **Limits**: Limita profundidade/tamanho
4. **Lazy Loading**: Carrega só quando necessário

## Próximos Passos

- [Fluxos de Dados](32-fluxos.md)
- [Lista de Serviços](30-servicos.md)

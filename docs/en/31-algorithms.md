# Complex Algorithms

## Overview

DuilioCode uses several complex algorithms to process code, understand intentions, and execute actions. This document explains the main ones.

## 1. Dependency Graph (Dependency Graph)

### What Is It?

A **dependency graph** shows which files depend on which other files.

### Why Do We Need It?

When creating multiple files, we need to create them in the **correct order**:
- File A imports File B
- We need to create B before A

### How Does It Work?

**Code**: `src/services/dependency_graph.py`

```python
class FileDependencyGraph:
    def build_graph(self, files):
        # Analyzes imports in each file
        graph = {}
        for file in files:
            imports = self.extract_imports(file)
            graph[file] = imports
        
        # Orders topologically
        return self.topological_sort(graph)
    
    def topological_sort(self, graph):
        # Orders so dependencies come first
        # Example: [B, A] if A depends on B
        return sorted_order
```

### Example

**Files:**
- `utils.js` (no dependencies)
- `app.js` (imports `utils.js`)
- `main.js` (imports `app.js`)

**Creation Order:**
1. `utils.js` (first)
2. `app.js` (second)
3. `main.js` (third)

## 2. File Tree Traversal (Tree Navigation)

### What Is It?

Algorithm to **navigate** folder structure and count files.

### Problem

Counting files recursively can be **very slow** in large projects.

### Solution: Depth Limit

**Code**: `src/api/routes/chat/chat_handler.py`

```python
def count_files_accurate(path: Path, max_files: int = 50000):
    files_count = 0
    folders_count = 0
    
    def scan(p: Path, depth: int = 0):
        nonlocal files_count, folders_count
        
        # Depth limit (avoids infinite loops)
        if depth > 15:
            return
        
        # File limit (avoids freezing)
        if files_count > max_files:
            return
        
        for item in p.iterdir():
            if item.is_dir():
                folders_count += 1
                scan(item, depth + 1)  # Recursive
            elif item.is_file():
                files_count += 1
    
    scan(path)
    return files_count, folders_count
```

### Optimizations

1. **Skip dot-files**: Ignores `.git`, `.node_modules`, etc.
2. **Depth limit**: Maximum 15 levels
3. **File limit**: Maximum 50,000 files
4. **Early return**: Stops when limits reached

## 3. Intent Detection (Intent Detection)

### What Is It?

Algorithm that **understands what the user wants to do** based on the message.

### Hybrid Approach

We combine **3 methods**:

#### 1. Keyword Matching (Simple)
```python
if 'create file' in message:
    return 'create'
```

#### 2. Linguistic Analysis (Advanced)
```python
# Analyzes verbs, connectors, patterns
analysis = linguistic_analyzer.analyze(message)
if analysis.requires_action:
    return 'create'
```

#### 3. AI Classification (Intelligent)
```python
# Uses AI to classify
classification = await ollama.classify(message)
return classification.intent
```

### Decision Algorithm

```python
def detect_intent(message):
    # 1. Try keyword matching (fast)
    simple_intent = keyword_match(message)
    if simple_intent and confidence > 0.8:
        return simple_intent
    
    # 2. Try linguistic analysis (medium)
    linguistic_intent = linguistic_analyze(message)
    if linguistic_intent.confidence > 0.7:
        return linguistic_intent.intent
    
    # 3. Use AI (slow, but accurate)
    ai_intent = await ai_classify(message)
    return ai_intent
```

## 4. Context Building (Context Construction)

### Problem

Very large prompts = **slow and expensive**

### Solution: Context Relevance

**Code**: `src/api/routes/chat/context_builder.py`

```python
def build_codebase_context(workspace_path, query=None):
    # 1. Analyzes codebase
    files = analyze_codebase(workspace_path)
    
    # 2. If has query, filters by relevance
    if query:
        files = filter_by_relevance(files, query)
    
    # 3. Limits size
    files = files[:100]  # Maximum 100 files
    
    # 4. Formats for prompt
    return format_for_prompt(files)
```

### Relevance Algorithm

```python
def filter_by_relevance(files, query):
    scores = []
    for file in files:
        # Score based on:
        # - File name contains query words
        # - File content contains query words
        # - File path is relevant
        score = calculate_relevance(file, query)
        scores.append((file, score))
    
    # Sorts by score and returns top N
    scores.sort(key=lambda x: x[1], reverse=True)
    return [f for f, s in scores[:50]]
```

## 5. Action Extraction (Action Extraction)

### Problem

AI can generate actions in **various formats**:
- ````create-file:path\ncontent\n````
- `create-file:path` (without backticks)
- Multiple actions mixed

### Solution: Multi-Pattern Regex

**Code**: `src/services/action_processor.py`

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
    
    # Pattern 2: create-file:path (without backticks)
    pattern2 = r'create-file:([^\n]+)'
    matches2 = re.finditer(pattern2, response_text)
    # ...
    
    # Pattern 3: create-directory:path
    pattern3 = r'```create-directory:([^\n]+)```'
    # ...
    
    return actions
```

### Ordering by Dependencies

```python
def order_actions(actions):
    # Separates by type
    directories = [a for a in actions if a['type'] == 'create-directory']
    files = [a for a in actions if a['type'] == 'create-file']
    
    # Orders files by dependencies
    ordered_files = dependency_sort(files)
    
    # Returns: directories first, then ordered files
    return directories + ordered_files
```

## 6. Cache Strategy (Cache Strategy)

### Problem

Analyzing codebase is **expensive** (slow). We don't want to do it every time.

### Solution: Multi-Layer Cache

**Code**: `src/services/cache_service.py`

```python
class CacheService:
    def __init__(self):
        # Layer 1: Memory (LRU cache)
        self.memory_cache = {}
        
        # Layer 2: Disk (diskcache)
        self.disk_cache = diskcache.Cache('.cache/duiliocode')
    
    def get(self, key):
        # 1. Try memory (fastest)
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # 2. Try disk (fast)
        if key in self.disk_cache:
            value = self.disk_cache[key]
            # Promotes to memory
            self.memory_cache[key] = value
            return value
        
        # 3. Not found
        return None
    
    def set(self, key, value, ttl=3600):
        # Saves in both
        self.memory_cache[key] = value
        self.disk_cache.set(key, value, expire=ttl)
```

### TTL (Time To Live)

```python
# Cache expires after 1 hour
cache.set('codebase_context', context, ttl=3600)

# After 1 hour, needs to recalculate
```

## 7. Prompt Optimization (Prompt Optimization)

### Problem

Very long prompts = **slow and expensive**

### Solution: Prompt Builder

**Code**: `src/services/prompt_builder.py`

```python
class PromptBuilder:
    @staticmethod
    def build_crud_prompt(operation, context):
        # Base prompt (short)
        prompt = BASE_SYSTEM_PROMPT
        
        # Adds only what's necessary
        if operation == OperationType.CREATE:
            prompt += _build_create_prompt(context)
        elif operation == OperationType.READ:
            prompt += _build_read_prompt(context)
        # ...
        
        return prompt  # Optimized, not verbose
```

### Strategies

1. **Operation-Specific**: Different prompts per operation
2. **Context-Aware**: Adds context only if necessary
3. **Minimal**: Removes unnecessary boilerplate

## 8. Path Intelligence (Path Intelligence)

### Problem

User says: "create file teste.js"
- Where to create? Root? `src/`? `components/`?

### Solution: Context Analysis

**Code**: `src/services/path_intelligence.py`

```python
class PathIntelligence:
    @classmethod
    def detect_path_intention(cls, prompt, filename):
        # Patterns that indicate subdirectory
        if 'src/' in prompt or 'components/' in prompt:
            return f"src/{filename}", False
        
        # Patterns that indicate root
        if 'file called' in prompt:
            return filename, True
        
        # Patterns that indicate parallel project
        if 'parallel' in prompt or 'outside' in prompt:
            return f"/absolute/path/{filename}", False
        
        # Default: root
        return filename, True
```

## 9. Codebase Analysis (Codebase Analysis)

### Analysis Algorithm

```python
def analyze_codebase(path, max_files=100):
    # 1. Collects files
    files = collect_files(path, max_files)
    
    # 2. Groups by language
    by_language = group_by_language(files)
    
    # 3. Identifies entry points
    entry_points = find_entry_points(files)
    
    # 4. Analyzes dependencies
    dependencies = analyze_dependencies(files)
    
    # 5. Generates structured context
    return format_context(
        files=files,
        languages=by_language,
        entry_points=entry_points,
        dependencies=dependencies
    )
```

## 10. Temperature Adjustment (Temperature Adjustment)

### Algorithm

```python
def adjust_temperature(message, base_temp=0.7):
    # File listing: needs precision
    if is_file_listing_request(message):
        return 0.2  # Very deterministic
    
    # Code generation: needs controlled creativity
    if is_code_generation(message):
        return 0.7  # Balanced
    
    # Explanations: can be more creative
    if is_explanation_request(message):
        return 0.9  # More natural
    
    return base_temp
```

## Performance Considerations

### Big O Notation

- **File Tree Traversal**: O(n) where n = number of files
- **Dependency Sort**: O(V + E) where V = vertices, E = edges
- **Intent Detection**: O(1) for keywords, O(n) for linguistic
- **Context Building**: O(n) where n = files analyzed

### Applied Optimizations

1. **Caching**: Avoids recalculations
2. **Early Returns**: Stops when possible
3. **Limits**: Limits depth/size
4. **Lazy Loading**: Loads only when necessary

## Next Steps

- [Data Flows](32-flows.md)
- [Service List](30-services.md)

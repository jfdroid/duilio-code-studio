# Lista de Serviços

## Visão Geral

DuilioCode Studio possui **36+ serviços** organizados por responsabilidade. Este documento lista todos e explica suas funções.

## Serviços Principais

### 1. OllamaService
**Arquivo**: `src/services/ollama_service.py`

**Função**: Comunicação com servidor Ollama

**Métodos Principais**:
- `generate()` - Gera resposta do modelo
- `generate_stream()` - Geração em streaming
- `health_check()` - Verifica status do Ollama

**Uso**:
```python
ollama = get_ollama_service()
response = await ollama.generate(prompt, model)
```

### 2. ActionProcessor
**Arquivo**: `src/services/action_processor.py`

**Função**: Processa e executa ações geradas pela IA

**Métodos Principais**:
- `extract_actions()` - Extrai ações do texto
- `process_actions()` - Executa ações
- `create_file()` - Cria arquivo
- `create_directory()` - Cria diretório

**Uso**:
```python
processor = get_action_processor()
actions = processor.extract_actions(response_text)
await processor.process_actions(actions, workspace_path)
```

### 3. LinguisticAnalyzer
**Arquivo**: `src/services/linguistic_analyzer.py`

**Função**: Análise linguística avançada (verbos, conectores, padrões)

**Métodos Principais**:
- `analyze()` - Analisa texto completo
- `_extract_verbs()` - Extrai verbos
- `_extract_connectors()` - Extrai conectores
- `build_structured_context()` - Cria contexto estruturado

**Uso**:
```python
analyzer = get_linguistic_analyzer()
analysis = analyzer.analyze("por que você não criou?")
if analysis.requires_explanation:
    # Adiciona instruções de explicação
```

### 4. IntentDetector
**Arquivo**: `src/services/intent_detector.py`

**Função**: Detecta intenções CRUD (Create, Read, Update, Delete)

**Métodos Principais**:
- `detect_file_intent()` - Detecta intenção de arquivo
- `detect_crud_intent()` - Detecta operação CRUD

**Uso**:
```python
detector = get_intent_detector()
intent = detector.detect_crud_intent("crie um arquivo")
# Retorna: {'create': True, 'read': False, ...}
```

### 5. CodebaseAnalyzer
**Arquivo**: `src/services/codebase_analyzer.py`

**Função**: Analisa estrutura do codebase

**Métodos Principais**:
- `analyze()` - Analisa codebase completo
- `get_file_tree()` - Obtém árvore de arquivos
- `get_dependencies()` - Obtém dependências

**Uso**:
```python
analyzer = get_codebase_analyzer()
context = analyzer.analyze(workspace_path)
```

### 6. WorkspaceService
**Arquivo**: `src/services/workspace_service.py`

**Função**: Gerenciamento de workspace

**Métodos Principais**:
- `get_current_path()` - Obtém caminho atual
- `set_workspace()` - Define workspace
- `list_files()` - Lista arquivos

**Uso**:
```python
workspace = get_workspace_service()
files = workspace.list_files(workspace_path)
```

### 7. FileService
**Arquivo**: `src/services/file_service.py`

**Função**: Operações de arquivo

**Métodos Principais**:
- `read_file()` - Lê arquivo
- `write_file()` - Escreve arquivo
- `delete_file()` - Deleta arquivo
- `file_exists()` - Verifica existência

**Uso**:
```python
file_service = get_file_service()
content = file_service.read_file("teste.txt", workspace_path)
```

### 8. CacheService
**Arquivo**: `src/services/cache_service.py`

**Função**: Cache de dados (memória + disco)

**Métodos Principais**:
- `get()` - Obtém do cache
- `set()` - Salva no cache
- `clear()` - Limpa cache

**Uso**:
```python
cache = get_cache_service()
context = cache.get("codebase_context")
if not context:
    context = analyze_codebase()
    cache.set("codebase_context", context, ttl=3600)
```

### 9. PromptBuilder
**Arquivo**: `src/services/prompt_builder.py`

**Função**: Construção de prompts otimizados

**Métodos Principais**:
- `build_system_prompt()` - Constrói system prompt
- `build_file_listing_context()` - Constrói contexto de arquivos
- `_build_create_prompt()` - Prompt para CREATE
- `_build_read_prompt()` - Prompt para READ

**Uso**:
```python
builder = get_prompt_builder()
prompt = builder.build_system_prompt(
    operation=OperationType.CREATE,
    context=context
)
```

### 10. SystemInfoService
**Arquivo**: `src/services/system_info.py`

**Função**: Coleta informações do sistema

**Métodos Principais**:
- `get_system_info()` - Obtém info completa
- `get_os_info()` - Info do OS
- `get_cpu_info()` - Info da CPU
- `get_memory_info()` - Info de memória

**Uso**:
```python
info_service = get_system_info_service()
system_info = info_service.get_system_info()
# Retorna: OS, CPU, Memory, User, Hostname
```

## Serviços de Suporte

### 11. DatabaseService
**Arquivo**: `src/services/database_service.py`

**Função**: Operações de banco de dados

**Métodos**:
- `get_preference()` - Obtém preferência
- `set_preference()` - Define preferência
- `save_message()` - Salva mensagem
- `get_conversation_history()` - Obtém histórico
- `save_metric()` - Salva métrica

### 12. UserPreferencesService
**Arquivo**: `src/services/user_preferences.py`

**Função**: Gerenciamento de preferências do usuário

### 13. ConversationMemoryService
**Arquivo**: `src/services/conversation_memory.py`

**Função**: Memória de conversação

### 14. GitService
**Arquivo**: `src/services/git_service.py`

**Função**: Operações Git

**Métodos**:
- `get_status()` - Status do Git
- `commit()` - Faz commit
- `get_diff()` - Obtém diff

### 15. CodeExecutor
**Arquivo**: `src/services/code_executor.py`

**Função**: Execução segura de código

**Métodos**:
- `execute()` - Executa código
- `execute_safe()` - Execução com sandbox

## Serviços de Análise

### 16. FileIntelligence
**Arquivo**: `src/services/file_intelligence.py`

**Função**: Análise inteligente de arquivos

### 17. PathIntelligence
**Arquivo**: `src/services/path_intelligence.py`

**Função**: Inteligência de caminhos

### 18. ProjectDetector
**Arquivo**: `src/services/project_detector.py`

**Função**: Detecta tipo de projeto

### 19. LanguageDetector
**Arquivo**: `src/services/language_detector.py`

**Função**: Detecta linguagem de programação

### 20. DependencyGraph
**Arquivo**: `src/services/dependency_graph.py`

**Função**: Grafo de dependências

## Serviços de Geração

### 21. IntelligentScaffolder
**Arquivo**: `src/services/intelligent_scaffolder.py`

**Função**: Scaffolding inteligente de projetos

### 22. ProjectScaffolding
**Arquivo**: `src/services/project_scaffolding.py`

**Função**: Scaffolding de projetos

### 23. DocumentationGenerator
**Arquivo**: `src/services/documentation_generator.py`

**Função**: Geração de documentação

## Serviços de Validação

### 24. IntelligentValidator
**Arquivo**: `src/services/intelligent_validator.py`

**Função**: Validação inteligente de código

### 25. SOLIDValidator
**Arquivo**: `src/services/solid_validator.py`

**Função**: Validação de princípios SOLID

### 26. SecurityScanner
**Arquivo**: `src/services/security_scanner.py`

**Função**: Escaneamento de segurança

## Serviços de Refatoração

### 27. RefactoringService
**Arquivo**: `src/services/refactoring_service.py`

**Função**: Refatoração de código

## Serviços de RAG

### 28. RAGService
**Arquivo**: `src/services/rag_service.py`

**Função**: Retrieval-Augmented Generation

## Serviços de Prompt

### 29. PromptClassifier
**Arquivo**: `src/services/prompt_classifier.py`

**Função**: Classificação de prompts

### 30. PromptExamples
**Arquivo**: `src/services/prompt_examples.py`

**Função**: Exemplos de prompts

### 31. PromptRegistry
**Arquivo**: `src/services/prompt_registry.py`

**Função**: Registro de prompts

## Serviços de Utilitários

### 32. DirectoryTree
**Arquivo**: `src/services/directory_tree.py`

**Função**: Árvore de diretórios

### 33. RelevanceScorer
**Arquivo**: `src/services/relevance_scorer.py`

**Função**: Score de relevância

### 34. AgentService
**Arquivo**: `src/services/agent_service.py`

**Função**: Serviço de agente

## Como Usar

### Obter Serviço

```python
from core.container import get_ollama_service

ollama = get_ollama_service()
```

### Injetar Dependência

```python
@router.post("/chat")
async def chat(
    ollama: OllamaService = Depends(get_ollama_service)
):
    response = await ollama.generate(...)
```

## Próximos Passos

- [Algoritmos Complexos](31-algoritmos.md)
- [Fluxos de Dados](32-fluxos.md)

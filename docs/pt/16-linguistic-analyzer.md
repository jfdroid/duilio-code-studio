# Linguistic Analyzer - Análise de Linguagem

## O que é?

Linguistic Analyzer é um sistema que **analisa a linguagem natural** do usuário para entender melhor suas intenções. Ele vai além de simples palavras-chave, analisando **verbos, conectores e padrões linguísticos**.

## Por que Precisamos?

### Problema com Palavras-Chave Simples

**Exemplo:**
```
"por que você não criou o arquivo?"
```

Com palavras-chave simples:
- ❌ Não detecta "criar" (está no passado)
- ❌ Não entende que é uma pergunta de explicação

Com Linguistic Analyzer:
- ✅ Detecta verbo "criar" (mesmo no passado)
- ✅ Detecta conector "por que" (causal/interrogativo)
- ✅ Entende: usuário quer EXPLICAÇÃO, não ação

## Como Funciona?

### 1. Extração de Verbos

**Código**: `src/services/linguistic_analyzer.py`

```python
def _extract_verbs(self, text: str):
    # Carrega verbos de data/linguistic/verbs.json
    verbs_data = self._load_verbs()
    
    # Procura por verbos e suas conjugações
    for category, verbs in verbs_data.items():
        for verb_info in verbs:
            base = verb_info['base']
            conjugations = verb_info['conjugations']
            
            # Procura por "criar", "crie", "criou", etc.
            pattern = r'\b(' + '|'.join([base] + conjugations) + r')\b'
            if re.search(pattern, text, re.IGNORECASE):
                return verb_info
    
    return None
```

### 2. Extração de Conectores

**Conectores** são palavras que ligam ideias:
- **Causal**: "por que", "porque", "why"
- **Interrogativo**: "qual", "quando", "what"
- **Condicional**: "se", "if"
- **Contrastivo**: "mas", "porém", "but"

```python
def _extract_connectors(self, text: str):
    connectors_data = self._load_connectors()
    
    found = []
    for category, connectors in connectors_data.items():
        for conn in connectors:
            if conn['word'].lower() in text.lower():
                found.append(conn)
    
    return found
```

### 3. Análise de Padrões

**Padrões** são frases comuns que indicam intenção:

```json
{
  "patterns": [
    {
      "type": "explanation",
      "phrases": ["por que", "why", "como funciona", "explain"],
      "weight": 1.0
    }
  ]
}
```

## Estrutura de Dados

### Verbos (`data/linguistic/verbs.json`)

```json
{
  "QUERY": {
    "verbs": [
      {
        "base": "ver",
        "conjugations": ["vejo", "vê", "viu", "ver"],
        "weight": 1.0
      }
    ]
  },
  "COMMAND": {
    "verbs": [
      {
        "base": "criar",
        "conjugations": ["crie", "criar", "criou", "criando"],
        "weight": 1.0
      }
    ]
  }
}
```

### Conectores (`data/linguistic/connectors.json`)

```json
{
  "CAUSAL": {
    "connectors": [
      {"word": "por que", "weight": 1.0},
      {"word": "porque", "weight": 1.0}
    ]
  }
}
```

## Análise Completa

### Exemplo Real

**Input:**
```
"por que você não criou o arquivo que eu pedi?"
```

**Análise:**

1. **Verbos Detectados:**
   - "criou" → COMMAND (criar)
   - "pedi" → COMMAND (pedir)

2. **Conectores Detectados:**
   - "por que" → CAUSAL/INTERROGATIVE

3. **Padrões Detectados:**
   - "por que" → explanation pattern

4. **Resultado:**
```python
LinguisticAnalysis(
    main_verb="criar",
    verb_category="COMMAND",
    connectors=["por que"],
    connector_types=["CAUSAL", "INTERROGATIVE"],
    requires_explanation=True,  # ← Detectado!
    requires_data=False,
    requires_action=False
)
```

## Uso no Sistema

### Integração no Chat Handler

**Código**: `src/api/routes/chat/chat_handler.py`

```python
# Analisa linguagem
linguistic_analyzer = get_linguistic_analyzer()
analysis = linguistic_analyzer.analyze(last_user_message)

# Se precisa de explicação
if analysis.requires_explanation:
    system_prompt += "\n\nEXPLANATION REQUEST:"
    system_prompt += "\n- User asked WHY/HOW - provide detailed reasoning"
    system_prompt += "\n- Reference the FILE LISTING or context"

# Se precisa de dados
if analysis.requires_data:
    system_prompt += "\n\nDATA REQUEST:"
    system_prompt += "\n- Use FILE LISTING to provide exact numbers"
```

## Tipos de Análise

### 1. Requires Explanation

**Detecta quando usuário quer explicação:**
- "por que", "why", "como", "how", "explain"

**Exemplo:**
```
"por que você vê apenas 28 arquivos?"
→ requires_explanation = True
→ AI explica o processo de contagem
```

### 2. Requires Data

**Detecta quando usuário quer dados:**
- "quantos", "how many", "quais", "which"

**Exemplo:**
```
"quantos arquivos existem?"
→ requires_data = True
→ AI fornece número exato do FILE LISTING
```

### 3. Requires Action

**Detecta quando usuário quer ação:**
- Verbos de comando: "criar", "deletar", "modificar"

**Exemplo:**
```
"crie um arquivo teste.txt"
→ requires_action = True
→ AI gera ação create-file
```

## Confiança (Confidence)

### O que é?

Confidence é um **score de 0.0 a 1.0** que indica quão confiante estamos na análise:

```python
def _calculate_confidence(self, analysis):
    score = 0.0
    
    # Verbo encontrado: +0.4
    if analysis.main_verb:
        score += 0.4
    
    # Conectores encontrados: +0.3
    if analysis.connectors:
        score += 0.3
    
    # Padrões encontrados: +0.3
    if analysis.patterns:
        score += 0.3
    
    return min(1.0, score)
```

### Uso

```python
if analysis.confidence > 0.7:
    # Alta confiança - usa análise
    system_prompt += linguistic_context
else:
    # Baixa confiança - usa detecção simples
    system_prompt += simple_crud_prompt
```

## Contexto Estruturado

### Build Structured Context

Cria uma string estruturada para incluir no prompt:

```python
def build_structured_context(self, analysis):
    context = "=== LINGUISTIC ANALYSIS ===\n"
    context += f"Main Verb: {analysis.main_verb}\n"
    context += f"Verb Category: {analysis.verb_category}\n"
    context += f"Requires Explanation: {analysis.requires_explanation}\n"
    context += f"Requires Data: {analysis.requires_data}\n"
    context += f"Requires Action: {analysis.requires_action}\n"
    context += f"Confidence: {analysis.confidence}\n"
    return context
```

**Incluído no prompt:**
```
=== LINGUISTIC ANALYSIS ===
Main Verb: criar
Verb Category: COMMAND
Requires Explanation: False
Requires Data: False
Requires Action: True
Confidence: 0.85
```

## Extensibilidade

### Adicionar Novos Verbos

Edite `data/linguistic/verbs.json`:

```json
{
  "COMMAND": {
    "verbs": [
      {
        "base": "novo_verbo",
        "conjugations": ["conjugação1", "conjugação2"],
        "weight": 1.0
      }
    ]
  }
}
```

### Adicionar Novos Conectores

Edite `data/linguistic/connectors.json`:

```json
{
  "CAUSAL": {
    "connectors": [
      {"word": "novo_conector", "weight": 1.0}
    ]
  }
}
```

## Performance

### Cache

Dados linguísticos são **carregados uma vez** e cacheados:

```python
@lru_cache(maxsize=1)
def _load_verbs(self):
    # Carrega apenas uma vez
    with open('data/linguistic/verbs.json') as f:
        return json.load(f)
```

### Otimização

- Regex com word boundaries (`\b`) para matching preciso
- Carregamento lazy (só quando necessário)
- Cache em memória

## Próximos Passos

- [Intent Detector - Detecção de Intenções](17-intent-detector.md)
- [Como Funciona o Chat](11-chat-funcionamento.md)

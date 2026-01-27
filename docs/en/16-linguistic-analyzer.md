# Linguistic Analyzer - Language Analysis

## What Is It?

Linguistic Analyzer is a system that **analyzes the natural language** of the user to better understand their intentions. It goes beyond simple keywords, analyzing **verbs, connectors, and linguistic patterns**.

## Why Do We Need It?

### Problem with Simple Keywords

**Example:**
```
"why didn't you create the file?"
```

With simple keywords:
- ❌ Doesn't detect "create" (it's in the past)
- ❌ Doesn't understand it's an explanation question

With Linguistic Analyzer:
- ✅ Detects verb "create" (even in the past)
- ✅ Detects connector "why" (causal/interrogative)
- ✅ Understands: user wants EXPLANATION, not action

## How Does It Work?

### 1. Verb Extraction

**Code**: `src/services/linguistic_analyzer.py`

```python
def _extract_verbs(self, text: str):
    # Loads verbs from data/linguistic/verbs.json
    verbs_data = self._load_verbs()
    
    # Searches for verbs and their conjugations
    for category, verbs in verbs_data.items():
        for verb_info in verbs:
            base = verb_info['base']
            conjugations = verb_info['conjugations']
            
            # Searches for "create", "created", "creating", etc.
            pattern = r'\b(' + '|'.join([base] + conjugations) + r')\b'
            if re.search(pattern, text, re.IGNORECASE):
                return verb_info
    
    return None
```

### 2. Connector Extraction

**Connectors** are words that link ideas:
- **Causal**: "why", "because"
- **Interrogative**: "what", "when", "which"
- **Conditional**: "if"
- **Contrastive**: "but", "however"

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

### 3. Pattern Analysis

**Patterns** are common phrases that indicate intention:

```json
{
  "patterns": [
    {
      "type": "explanation",
      "phrases": ["why", "how does it work", "explain"],
      "weight": 1.0
    }
  ]
}
```

## Data Structure

### Verbs (`data/linguistic/verbs.json`)

```json
{
  "QUERY": {
    "verbs": [
      {
        "base": "see",
        "conjugations": ["see", "saw", "seeing", "seen"],
        "weight": 1.0
      }
    ]
  },
  "COMMAND": {
    "verbs": [
      {
        "base": "create",
        "conjugations": ["create", "created", "creating", "creates"],
        "weight": 1.0
      }
    ]
  }
}
```

### Connectors (`data/linguistic/connectors.json`)

```json
{
  "CAUSAL": {
    "connectors": [
      {"word": "why", "weight": 1.0},
      {"word": "because", "weight": 1.0}
    ]
  }
}
```

## Complete Analysis

### Real Example

**Input:**
```
"why didn't you create the file I asked for?"
```

**Analysis:**

1. **Verbs Detected:**
   - "create" → COMMAND (create)
   - "asked" → COMMAND (ask)

2. **Connectors Detected:**
   - "why" → CAUSAL/INTERROGATIVE

3. **Patterns Detected:**
   - "why" → explanation pattern

4. **Result:**
```python
LinguisticAnalysis(
    main_verb="create",
    verb_category="COMMAND",
    connectors=["why"],
    connector_types=["CAUSAL", "INTERROGATIVE"],
    requires_explanation=True,  # ← Detected!
    requires_data=False,
    requires_action=False
)
```

## Usage in System

### Integration in Chat Handler

**Code**: `src/api/routes/chat/chat_handler.py`

```python
# Analyzes language
linguistic_analyzer = get_linguistic_analyzer()
analysis = linguistic_analyzer.analyze(last_user_message)

# If needs explanation
if analysis.requires_explanation:
    system_prompt += "\n\nEXPLANATION REQUEST:"
    system_prompt += "\n- User asked WHY/HOW - provide detailed reasoning"
    system_prompt += "\n- Reference the FILE LISTING or context"

# If needs data
if analysis.requires_data:
    system_prompt += "\n\nDATA REQUEST:"
    system_prompt += "\n- Use FILE LISTING to provide exact numbers"
```

## Analysis Types

### 1. Requires Explanation

**Detects when user wants explanation:**
- "why", "how", "explain"

**Example:**
```
"why do you see only 28 files?"
→ requires_explanation = True
→ AI explains the counting process
```

### 2. Requires Data

**Detects when user wants data:**
- "how many", "which", "what"

**Example:**
```
"how many files exist?"
→ requires_data = True
→ AI provides exact number from FILE LISTING
```

### 3. Requires Action

**Detects when user wants action:**
- Command verbs: "create", "delete", "modify"

**Example:**
```
"create a file teste.txt"
→ requires_action = True
→ AI generates create-file action
```

## Confidence

### What Is It?

Confidence is a **score from 0.0 to 1.0** that indicates how confident we are in the analysis:

```python
def _calculate_confidence(self, analysis):
    score = 0.0
    
    # Verb found: +0.4
    if analysis.main_verb:
        score += 0.4
    
    # Connectors found: +0.3
    if analysis.connectors:
        score += 0.3
    
    # Patterns found: +0.3
    if analysis.patterns:
        score += 0.3
    
    return min(1.0, score)
```

### Usage

```python
if analysis.confidence > 0.7:
    # High confidence - uses analysis
    system_prompt += linguistic_context
else:
    # Low confidence - uses simple detection
    system_prompt += simple_crud_prompt
```

## Structured Context

### Build Structured Context

Creates a structured string to include in prompt:

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

**Included in prompt:**
```
=== LINGUISTIC ANALYSIS ===
Main Verb: create
Verb Category: COMMAND
Requires Explanation: False
Requires Data: False
Requires Action: True
Confidence: 0.85
```

## Extensibility

### Add New Verbs

Edit `data/linguistic/verbs.json`:

```json
{
  "COMMAND": {
    "verbs": [
      {
        "base": "new_verb",
        "conjugations": ["conjugation1", "conjugation2"],
        "weight": 1.0
      }
    ]
  }
}
```

### Add New Connectors

Edit `data/linguistic/connectors.json`:

```json
{
  "CAUSAL": {
    "connectors": [
      {"word": "new_connector", "weight": 1.0}
    ]
  }
}
```

## Performance

### Cache

Linguistic data is **loaded once** and cached:

```python
@lru_cache(maxsize=1)
def _load_verbs(self):
    # Loads only once
    with open('data/linguistic/verbs.json') as f:
        return json.load(f)
```

### Optimization

- Regex with word boundaries (`\b`) for precise matching
- Lazy loading (only when needed)
- In-memory cache

## Next Steps

- [Intent Detector - Intent Detection](17-intent-detector.md)
- [How Chat Works](11-chat-functionality.md)

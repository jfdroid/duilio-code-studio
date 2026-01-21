"""
Prompt Classifier Service
=========================
ML-like intelligent classification of user prompts.
Determines the best model and response strategy.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class PromptCategory(Enum):
    """Categories of user prompts."""
    CODE_GENERATION = "code_generation"       # Create new code
    CODE_EXPLANATION = "code_explanation"     # Explain existing code
    CODE_DEBUG = "code_debug"                 # Fix bugs/errors
    CODE_REFACTOR = "code_refactor"           # Improve/refactor code
    CODE_REVIEW = "code_review"               # Review code quality
    CODEBASE_ANALYSIS = "codebase_analysis"   # Analyze project structure
    GENERAL_QUESTION = "general_question"     # General knowledge
    CREATIVE_WRITING = "creative_writing"     # Stories, poems, etc
    DOCUMENTATION = "documentation"           # Write docs/README
    SHELL_COMMAND = "shell_command"           # Terminal commands
    DATABASE_QUERY = "database_query"         # SQL, database operations
    ARCHITECTURE = "architecture"             # System design
    TESTING = "testing"                       # Write tests


@dataclass
class ClassificationResult:
    """Result of prompt classification."""
    category: PromptCategory
    confidence: float
    is_code_related: bool
    recommended_model: str
    keywords_found: List[str]
    reasoning: str
    system_prompt_modifier: str


class PromptClassifier:
    """
    Intelligent prompt classifier.
    
    Uses pattern matching, keyword analysis, and heuristics
    to determine the best way to handle a prompt.
    """
    
    # Keywords by category with weights
    CATEGORY_KEYWORDS: Dict[PromptCategory, Dict[str, float]] = {
        PromptCategory.CODE_GENERATION: {
            'create': 1.0, 'write': 0.8, 'generate': 0.9, 'implement': 1.0,
            'build': 0.8, 'make': 0.6, 'add': 0.5, 'desenvolva': 1.0,
            'crie': 1.0, 'faça': 0.7, 'escreva': 0.8, 'implemente': 1.0,
            'function': 0.7, 'class': 0.7, 'component': 0.8, 'feature': 0.7,
            'new file': 1.0, 'novo arquivo': 1.0, 'criar arquivo': 1.0,
        },
        PromptCategory.CODE_EXPLANATION: {
            'explain': 1.0, 'what is': 0.8, 'how does': 0.9, 'what does': 0.9,
            'explique': 1.0, 'como funciona': 1.0, 'o que é': 0.8, 'o que faz': 0.9,
            'understand': 0.7, 'entenda': 0.7, 'describe': 0.8, 'descreva': 0.8,
            'purpose': 0.6, 'objetivo': 0.6, 'meaning': 0.6, 'significado': 0.6,
        },
        PromptCategory.CODE_DEBUG: {
            'bug': 1.0, 'error': 1.0, 'fix': 1.0, 'debug': 1.0,
            'erro': 1.0, 'corrigir': 1.0, 'consertar': 1.0, 'resolver': 0.8,
            'not working': 0.9, 'não funciona': 0.9, 'broken': 0.8, 'quebrado': 0.8,
            'issue': 0.7, 'problema': 0.7, 'crash': 0.9, 'exception': 0.9,
            'traceback': 1.0, 'stack trace': 1.0,
        },
        PromptCategory.CODE_REFACTOR: {
            'refactor': 1.0, 'refatorar': 1.0, 'improve': 0.8, 'melhorar': 0.8,
            'optimize': 0.9, 'otimizar': 0.9, 'clean': 0.7, 'limpar': 0.7,
            'reorganize': 0.8, 'reorganizar': 0.8, 'simplify': 0.8, 'simplificar': 0.8,
            'modernize': 0.9, 'modernizar': 0.9, 'update': 0.6, 'atualizar': 0.6,
        },
        PromptCategory.CODEBASE_ANALYSIS: {
            'codebase': 1.0, 'project': 0.7, 'projeto': 0.7, 'structure': 0.8,
            'estrutura': 0.8, 'analyze': 0.9, 'analisar': 0.9, 'overview': 0.8,
            'visão geral': 0.8, 'entender o': 0.7, 'understand the': 0.7,
            'como esse': 0.8, 'how this': 0.8, 'explorer': 0.6, 'workspace': 0.6,
        },
        PromptCategory.GENERAL_QUESTION: {
            'what': 0.4, 'why': 0.5, 'when': 0.4, 'who': 0.3,
            'o que': 0.4, 'por que': 0.5, 'quando': 0.4, 'quem': 0.3,
            'tell me': 0.5, 'me conte': 0.5, 'história': 0.8, 'story': 0.8,
            'life': 0.6, 'vida': 0.6, 'world': 0.5, 'mundo': 0.5,
        },
        PromptCategory.CREATIVE_WRITING: {
            'story': 1.0, 'história': 1.0, 'poem': 1.0, 'poema': 1.0,
            'write a': 0.6, 'escreva um': 0.6, 'creative': 0.8, 'criativo': 0.8,
            'imagine': 0.7, 'imagine': 0.7, 'fiction': 0.9, 'ficção': 0.9,
            'presentation': 0.8, 'apresentação': 0.8, 'book': 0.7, 'livro': 0.7,
        },
        PromptCategory.DOCUMENTATION: {
            'readme': 1.0, 'documentation': 1.0, 'documentação': 1.0,
            'document': 0.8, 'documentar': 0.8, 'docstring': 0.9,
            'comment': 0.6, 'comentário': 0.6, 'api doc': 0.9,
        },
        PromptCategory.SHELL_COMMAND: {
            'command': 0.8, 'comando': 0.8, 'terminal': 0.9, 'shell': 0.9,
            'bash': 1.0, 'cli': 0.9, 'script': 0.7, 'run': 0.5,
            'executar': 0.5, 'rodar': 0.5, 'install': 0.6, 'instalar': 0.6,
        },
        PromptCategory.DATABASE_QUERY: {
            'sql': 1.0, 'query': 0.8, 'database': 0.9, 'banco de dados': 0.9,
            'select': 0.7, 'insert': 0.7, 'mongodb': 1.0, 'postgres': 1.0,
            'mysql': 1.0, 'table': 0.6, 'tabela': 0.6,
        },
        PromptCategory.ARCHITECTURE: {
            'architecture': 1.0, 'arquitetura': 1.0, 'design': 0.7, 'pattern': 0.8,
            'padrão': 0.8, 'solid': 0.9, 'microservice': 1.0, 'microsserviço': 1.0,
            'scalable': 0.8, 'escalável': 0.8, 'system': 0.5, 'sistema': 0.5,
        },
        PromptCategory.TESTING: {
            'test': 0.9, 'teste': 0.9, 'unit test': 1.0, 'teste unitário': 1.0,
            'integration': 0.7, 'integração': 0.7, 'mock': 0.8, 'coverage': 0.8,
            'pytest': 1.0, 'jest': 1.0, 'tdd': 1.0, 'bdd': 1.0,
        },
    }
    
    # Language patterns that indicate code context
    CODE_LANGUAGE_PATTERNS = [
        r'\b(python|javascript|typescript|java|kotlin|go|rust|c\+\+|ruby|php|swift)\b',
        r'\b(react|vue|angular|django|flask|fastapi|spring|node)\b',
        r'\b(html|css|scss|json|yaml|xml|sql)\b',
    ]
    
    # Code syntax patterns
    CODE_SYNTAX_PATTERNS = [
        r'```\w*\n',           # Code blocks
        r'def\s+\w+\s*\(',    # Python function
        r'function\s+\w+\s*\(', # JS function
        r'class\s+\w+',        # Class definition
        r'=>',                  # Arrow function
        r'\{\s*\n',            # Block start
        r'import\s+\w+',       # Import statement
        r'from\s+\w+\s+import', # Python import
        r'require\s*\(',       # Node require
        r'\$\(\s*[\'"]',       # jQuery
    ]
    
    # Models for each category type
    CODE_MODELS = ['qwen2.5-coder:14b', 'qwen2.5-coder:7b', 'codellama', 'deepseek-coder']
    GENERAL_MODELS = ['llama3.2', 'llama3.1', 'mistral', 'gemma2', 'phi3']
    
    @classmethod
    def classify(cls, prompt: str, available_models: List[str] = None) -> ClassificationResult:
        """
        Classify a prompt and determine the best handling strategy.
        
        Args:
            prompt: User's prompt
            available_models: List of available models
            
        Returns:
            ClassificationResult with category, confidence, and recommendations
        """
        prompt_lower = prompt.lower()
        
        # Score each category
        scores: Dict[PromptCategory, float] = {}
        keywords_by_category: Dict[PromptCategory, List[str]] = {}
        
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            score = 0.0
            found_keywords = []
            
            for keyword, weight in keywords.items():
                if keyword in prompt_lower:
                    score += weight
                    found_keywords.append(keyword)
            
            scores[category] = score
            keywords_by_category[category] = found_keywords
        
        # Check for code patterns (boost code categories)
        has_code_syntax = any(
            re.search(pattern, prompt, re.IGNORECASE)
            for pattern in cls.CODE_SYNTAX_PATTERNS
        )
        
        has_code_language = any(
            re.search(pattern, prompt, re.IGNORECASE)
            for pattern in cls.CODE_LANGUAGE_PATTERNS
        )
        
        # Boost code-related categories if code patterns found
        if has_code_syntax or has_code_language:
            for category in [
                PromptCategory.CODE_GENERATION,
                PromptCategory.CODE_EXPLANATION,
                PromptCategory.CODE_DEBUG,
                PromptCategory.CODE_REFACTOR,
            ]:
                scores[category] = scores.get(category, 0) * 1.5 + 0.5
        
        # Find best category
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        # Calculate confidence (0-1)
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.5
        
        # Determine if code-related
        code_categories = {
            PromptCategory.CODE_GENERATION,
            PromptCategory.CODE_EXPLANATION,
            PromptCategory.CODE_DEBUG,
            PromptCategory.CODE_REFACTOR,
            PromptCategory.CODE_REVIEW,
            PromptCategory.CODEBASE_ANALYSIS,
            PromptCategory.DATABASE_QUERY,
            PromptCategory.TESTING,
            PromptCategory.SHELL_COMMAND,
            PromptCategory.ARCHITECTURE,
        }
        is_code_related = best_category in code_categories or has_code_syntax or has_code_language
        
        # Select model
        if available_models:
            model_names = [m.lower() if isinstance(m, str) else m.get('name', '').lower() for m in available_models]
            
            if is_code_related:
                for preferred in cls.CODE_MODELS:
                    for available in model_names:
                        if preferred in available:
                            recommended_model = available
                            break
                    else:
                        continue
                    break
                else:
                    recommended_model = model_names[0] if model_names else 'qwen2.5-coder:7b'
            else:
                for preferred in cls.GENERAL_MODELS:
                    for available in model_names:
                        if preferred in available:
                            recommended_model = available
                            break
                    else:
                        continue
                    break
                else:
                    recommended_model = model_names[0] if model_names else 'llama3.2:latest'
        else:
            recommended_model = 'qwen2.5-coder:7b' if is_code_related else 'llama3.2:latest'
        
        # Generate reasoning
        reasoning = cls._generate_reasoning(best_category, keywords_by_category[best_category], confidence)
        
        # Generate system prompt modifier
        system_modifier = cls._get_system_modifier(best_category)
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            is_code_related=is_code_related,
            recommended_model=recommended_model,
            keywords_found=keywords_by_category[best_category],
            reasoning=reasoning,
            system_prompt_modifier=system_modifier,
        )
    
    @classmethod
    def _generate_reasoning(cls, category: PromptCategory, keywords: List[str], confidence: float) -> str:
        """Generate explanation of classification."""
        confidence_str = "high" if confidence > 0.6 else "medium" if confidence > 0.3 else "low"
        
        if keywords:
            return f"Classified as {category.value} ({confidence_str} confidence) based on keywords: {', '.join(keywords[:5])}"
        return f"Classified as {category.value} ({confidence_str} confidence) based on pattern analysis"
    
    @classmethod
    def _get_system_modifier(cls, category: PromptCategory) -> str:
        """Get category-specific system prompt modifier."""
        modifiers = {
            PromptCategory.CODE_GENERATION: "Focus on creating clean, well-documented, production-ready code. Include error handling and edge cases.",
            PromptCategory.CODE_EXPLANATION: "Explain the code step by step, using simple language. Use analogies when helpful.",
            PromptCategory.CODE_DEBUG: "Analyze the error carefully. Identify the root cause and provide a fix with explanation.",
            PromptCategory.CODE_REFACTOR: "Focus on improving code quality: readability, performance, and maintainability. Follow SOLID principles.",
            PromptCategory.CODEBASE_ANALYSIS: "Provide a comprehensive analysis of the project structure, architecture, and key components.",
            PromptCategory.CREATIVE_WRITING: "Be creative and engaging. Use vivid language and storytelling techniques.",
            PromptCategory.DOCUMENTATION: "Write clear, comprehensive documentation following best practices.",
            PromptCategory.SHELL_COMMAND: "Provide exact commands with explanations. Consider cross-platform compatibility.",
            PromptCategory.DATABASE_QUERY: "Write efficient, safe queries. Consider indexes and performance.",
            PromptCategory.ARCHITECTURE: "Consider scalability, maintainability, and best practices in system design.",
            PromptCategory.TESTING: "Write comprehensive tests covering edge cases. Follow testing best practices.",
        }
        
        return modifiers.get(category, "Be helpful and thorough in your response.")


# Helper function for quick classification
def classify_prompt(prompt: str, models: List[str] = None) -> ClassificationResult:
    """Quick helper to classify a prompt."""
    return PromptClassifier.classify(prompt, models)

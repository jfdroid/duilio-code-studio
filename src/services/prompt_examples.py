"""
Prompt Examples Service
=======================
Provides semantic similarity matching with example prompts.
Helps the AI understand intent better through few-shot learning.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PromptExample:
    """An example prompt with expected behavior."""
    prompt: str
    category: str
    intent: str
    keywords: List[str]
    example_response_start: str


# Example prompts for few-shot learning
PROMPT_EXAMPLES: List[PromptExample] = [
    # === Code Generation Examples ===
    PromptExample(
        prompt="Create a Python function that calculates fibonacci",
        category="code_generation",
        intent="User wants to create new code - a specific function",
        keywords=["create", "function", "python", "fibonacci"],
        example_response_start="Here's a Python function to calculate Fibonacci numbers:\n\n```python\ndef fibonacci(n):"
    ),
    PromptExample(
        prompt="Write a React component for a login form",
        category="code_generation",
        intent="User wants a new React component for authentication",
        keywords=["write", "react", "component", "login", "form"],
        example_response_start="Here's a React login form component:\n\n```jsx\nimport React, { useState } from 'react';"
    ),
    PromptExample(
        prompt="crie uma classe kotlin para gerenciar usuarios",
        category="code_generation",
        intent="User wants a Kotlin class for user management (Portuguese)",
        keywords=["crie", "classe", "kotlin", "usuarios"],
        example_response_start="Aqui está uma classe Kotlin para gerenciar usuários:\n\n```kotlin\ndata class User("
    ),
    
    # === Code Explanation Examples ===
    PromptExample(
        prompt="Explain how this code works",
        category="code_explanation",
        intent="User wants to understand existing code",
        keywords=["explain", "how", "works", "code"],
        example_response_start="Let me break down this code step by step:\n\n1. First,"
    ),
    PromptExample(
        prompt="me explique como esse codebase funciona",
        category="codebase_analysis",
        intent="User wants to understand the entire project structure (Portuguese)",
        keywords=["explique", "codebase", "funciona"],
        example_response_start="Vou explicar a estrutura deste projeto:\n\n## Visão Geral\nEste projeto"
    ),
    PromptExample(
        prompt="What does this function do?",
        category="code_explanation",
        intent="User wants explanation of specific function",
        keywords=["what", "does", "function"],
        example_response_start="This function does the following:\n\n**Purpose:**"
    ),
    
    # === Debug Examples ===
    PromptExample(
        prompt="I'm getting an error: TypeError: Cannot read property",
        category="code_debug",
        intent="User has a JavaScript/TypeScript runtime error",
        keywords=["error", "TypeError", "cannot", "read", "property"],
        example_response_start="This error typically occurs when you're trying to access a property on an undefined or null value.\n\n**Possible causes:**"
    ),
    PromptExample(
        prompt="fix this bug: the function returns None instead of the result",
        category="code_debug",
        intent="User has a Python function that doesn't return correctly",
        keywords=["fix", "bug", "returns", "None"],
        example_response_start="The issue is likely that your function doesn't have a return statement, or it's returning before reaching the result.\n\n**Here's the fix:**"
    ),
    
    # === Codebase Analysis Examples ===
    PromptExample(
        prompt="analyze this project structure",
        category="codebase_analysis",
        intent="User wants project structure analysis",
        keywords=["analyze", "project", "structure"],
        example_response_start="## Project Analysis\n\n### Structure Overview\nThis project follows"
    ),
    PromptExample(
        prompt="what technologies are used in this codebase",
        category="codebase_analysis",
        intent="User wants tech stack information",
        keywords=["technologies", "used", "codebase"],
        example_response_start="Based on my analysis of the codebase, here are the technologies used:\n\n**Languages:**"
    ),
    
    # === Refactoring Examples ===
    PromptExample(
        prompt="refactor this code to follow SOLID principles",
        category="code_refactor",
        intent="User wants code improvement following best practices",
        keywords=["refactor", "SOLID", "principles"],
        example_response_start="I'll refactor this code following SOLID principles:\n\n**Before:** Your current code violates"
    ),
    PromptExample(
        prompt="improve the performance of this function",
        category="code_refactor",
        intent="User wants performance optimization",
        keywords=["improve", "performance", "function"],
        example_response_start="Here are the performance improvements:\n\n**Current Issues:**"
    ),
    
    # === General/Creative Examples ===
    PromptExample(
        prompt="write a story about a programmer",
        category="creative_writing",
        intent="User wants creative content",
        keywords=["write", "story"],
        example_response_start="# The Midnight Commit\n\nIt was 2 AM when Sarah finally found the bug"
    ),
    PromptExample(
        prompt="explain quantum computing to a 5 year old",
        category="general_question",
        intent="User wants simple explanation of complex topic",
        keywords=["explain", "quantum", "computing"],
        example_response_start="Imagine you have a magical coin that can be both heads AND tails at the same time"
    ),
    PromptExample(
        prompt="me conte sobre a historia do linux",
        category="general_question",
        intent="User wants historical information (Portuguese)",
        keywords=["conte", "historia", "linux"],
        example_response_start="A história do Linux começou em 1991, quando Linus Torvalds"
    ),
]


class PromptExamplesService:
    """
    Service for matching prompts with examples.
    
    Uses keyword matching and similarity scoring to find
    the most relevant examples for few-shot learning.
    """
    
    def __init__(self):
        self.examples = PROMPT_EXAMPLES
    
    def _calculate_similarity(self, prompt: str, example: PromptExample) -> float:
        """
        Calculate similarity score between prompt and example.
        
        Simple keyword-based scoring - could be enhanced with
        embeddings for true semantic similarity.
        """
        prompt_lower = prompt.lower()
        
        # Keyword match score
        keyword_matches = sum(
            1 for kw in example.keywords
            if kw.lower() in prompt_lower
        )
        keyword_score = keyword_matches / len(example.keywords) if example.keywords else 0
        
        # Word overlap score
        prompt_words = set(prompt_lower.split())
        example_words = set(example.prompt.lower().split())
        
        intersection = len(prompt_words & example_words)
        union = len(prompt_words | example_words)
        overlap_score = intersection / union if union > 0 else 0
        
        # Combined score
        return keyword_score * 0.7 + overlap_score * 0.3
    
    def find_similar_examples(
        self,
        prompt: str,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[Tuple[PromptExample, float]]:
        """
        Find the most similar examples for a prompt.
        
        Args:
            prompt: User's prompt
            category: Optional category filter
            top_k: Number of examples to return
            
        Returns:
            List of (example, similarity_score) tuples
        """
        candidates = self.examples
        
        if category:
            candidates = [e for e in candidates if e.category == category]
        
        scored = [
            (example, self._calculate_similarity(prompt, example))
            for example in candidates
        ]
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:top_k]
    
    def get_few_shot_context(
        self,
        prompt: str,
        category: Optional[str] = None,
        num_examples: int = 2
    ) -> str:
        """
        Generate few-shot learning context from similar examples.
        
        Args:
            prompt: User's prompt
            category: Optional category filter
            num_examples: Number of examples to include
            
        Returns:
            Formatted context string for AI
        """
        similar = self.find_similar_examples(prompt, category, num_examples)
        
        if not similar or similar[0][1] < 0.2:
            return ""
        
        context_parts = ["=== SIMILAR EXAMPLES ===\n"]
        
        for example, score in similar:
            if score < 0.2:
                continue
            
            context_parts.append(f"**Example Prompt:** {example.prompt}")
            context_parts.append(f"**Intent:** {example.intent}")
            context_parts.append(f"**Expected Response Style:**\n{example.example_response_start}\n")
        
        return "\n".join(context_parts)
    
    def get_intent_hint(self, prompt: str) -> Optional[str]:
        """
        Get a hint about the user's intent based on similar examples.
        
        Returns:
            Intent description or None
        """
        similar = self.find_similar_examples(prompt, top_k=1)
        
        if similar and similar[0][1] >= 0.4:
            return similar[0][0].intent
        
        return None
    
    def add_example(
        self,
        prompt: str,
        category: str,
        intent: str,
        keywords: List[str],
        example_response_start: str
    ) -> None:
        """Add a new example to the collection."""
        example = PromptExample(
            prompt=prompt,
            category=category,
            intent=intent,
            keywords=keywords,
            example_response_start=example_response_start
        )
        self.examples.append(example)


# Singleton instance
_prompt_examples_service: Optional[PromptExamplesService] = None


def get_prompt_examples_service() -> PromptExamplesService:
    """Get singleton prompt examples service instance."""
    global _prompt_examples_service
    if _prompt_examples_service is None:
        _prompt_examples_service = PromptExamplesService()
    return _prompt_examples_service

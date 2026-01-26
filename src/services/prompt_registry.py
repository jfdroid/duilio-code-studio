"""
Prompt Registry Service
======================
Centralized, optimized prompt management system.
Consolidates all prompts in a structured, reusable format.

Benefits:
- Single source of truth for all prompts
- Easy to update and maintain
- Version control friendly
- Enables prompt optimization and A/B testing
- Fast lookup and caching
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class PromptCategory(Enum):
    """Categories of prompts for organization."""
    FILE_CREATION = "file_creation"
    FILE_MODIFICATION = "file_modification"
    PROJECT_GENERATION = "project_generation"
    CODE_GENERATION = "code_generation"
    CODE_REFACTOR = "code_refactor"
    CODE_DEBUG = "code_debug"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class PromptComplexity(Enum):
    """Complexity levels for prompt optimization."""
    SIMPLE = "simple"  # < 50 tokens
    MEDIUM = "medium"  # 50-200 tokens
    COMPLEX = "complex"  # 200-500 tokens
    VERY_COMPLEX = "very_complex"  # > 500 tokens


@dataclass
class PromptTemplate:
    """A prompt template with metadata."""
    id: str
    name: str
    category: PromptCategory
    complexity: PromptComplexity
    template: str  # Template string with {placeholders}
    variables: List[str]  # List of variable names in template
    description: str
    tags: List[str]
    examples: List[Dict[str, str]]
    metadata: Dict[str, Any]
    
    def render(self, **kwargs) -> str:
        """Render template with provided variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
    
    def hash(self) -> str:
        """Generate hash for caching."""
        content = f"{self.id}:{self.template}"
        return hashlib.md5(content.encode()).hexdigest()


class PromptRegistry:
    """
    Centralized registry for all prompts.
    
    Features:
    - Fast lookup by ID, category, or tags
    - Template rendering with variables
    - Versioning and caching
    - Performance metrics tracking
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path(__file__).parent.parent.parent / "data" / "prompt_registry.json"
        self.prompts: Dict[str, PromptTemplate] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load prompts from registry file."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for prompt_data in data.get('prompts', []):
                    prompt = PromptTemplate(
                        id=prompt_data['id'],
                        name=prompt_data['name'],
                        category=PromptCategory(prompt_data['category']),
                        complexity=PromptComplexity(prompt_data['complexity']),
                        template=prompt_data['template'],
                        variables=prompt_data.get('variables', []),
                        description=prompt_data.get('description', ''),
                        tags=prompt_data.get('tags', []),
                        examples=prompt_data.get('examples', []),
                        metadata=prompt_data.get('metadata', {})
                    )
                    self.prompts[prompt.id] = prompt
        else:
            self._initialize_default_prompts()
            self._save_registry()
    
    def _initialize_default_prompts(self):
        """Initialize with default prompt templates."""
        default_prompts = [
            {
                'id': 'create_single_file',
                'name': 'Create Single File',
                'category': 'file_creation',
                'complexity': 'simple',
                'template': 'CREATE a {file_path} file using the create-file: format with {description}.\n\nIMPORTANT: Use the format ```create-file:{file_path} to create the file.',
                'variables': ['file_path', 'description'],
                'description': 'Template for creating a single file',
                'tags': ['file', 'create', 'basic'],
                'examples': [
                    {'input': {'file_path': 'utils.js', 'description': 'helper functions'}, 'output': 'CREATE a utils.js file...'}
                ],
                'metadata': {}
            },
            {
                'id': 'create_multiple_files',
                'name': 'Create Multiple Files',
                'category': 'file_creation',
                'complexity': 'complex',
                'template': 'CREATE {project_type} with ALL files using the create-file: format.\n\nCREATE ALL these files using multiple ```create-file: blocks:\n{file_list}\n\nCRITICAL:\n- Create ALL files with COMPLETE, FUNCTIONAL code\n- Use multiple ```create-file: blocks in a single response',
                'variables': ['project_type', 'file_list'],
                'description': 'Template for creating multiple files in a project',
                'tags': ['project', 'multiple', 'files'],
                'examples': [],
                'metadata': {}
            },
            {
                'id': 'modify_file',
                'name': 'Modify Existing File',
                'category': 'file_modification',
                'complexity': 'medium',
                'template': 'MODIFY the {file_path} file that already exists in the workspace. {task_description}.\n\nCRITICAL:\n- The {file_path} file ALREADY EXISTS in the workspace\n- You MUST use the format ```modify-file:{file_path} (NOT create-file)\n- You MUST include ALL existing file content\n- {additional_instructions}\n- DO NOT create new files, only MODIFY the existing file',
                'variables': ['file_path', 'task_description', 'additional_instructions'],
                'description': 'Template for modifying existing files',
                'tags': ['modify', 'file', 'update'],
                'examples': [],
                'metadata': {}
            },
            {
                'id': 'create_react_project',
                'name': 'Create React Project',
                'category': 'project_generation',
                'complexity': 'very_complex',
                'template': 'CREATE a complete React project using the create-file: format for EACH file:\n\nCREATE ALL these files using the format ```create-file:path:\n{react_file_list}\n\nIMPORTANT: Use multiple ```create-file: blocks to create ALL files in a single response.',
                'variables': ['react_file_list'],
                'description': 'Template for creating React projects',
                'tags': ['react', 'project', 'web'],
                'examples': [],
                'metadata': {'framework': 'react'}
            },
            {
                'id': 'create_android_project',
                'name': 'Create Android Project',
                'category': 'project_generation',
                'complexity': 'very_complex',
                'template': 'CREATE a complete Android Kotlin project with ALL necessary files using the create-file: format:\n\nCREATE ALL these files:\n{android_file_list}\n\nIMPORTANT: Use multiple ```create-file: blocks to create ALL files in a single response.',
                'variables': ['android_file_list'],
                'description': 'Template for creating Android projects',
                'tags': ['android', 'kotlin', 'mobile'],
                'examples': [],
                'metadata': {'platform': 'android', 'language': 'kotlin'}
            },
            {
                'id': 'create_fastapi_project',
                'name': 'Create FastAPI Project',
                'category': 'project_generation',
                'complexity': 'very_complex',
                'template': 'CREATE a complete FastAPI REST API project with ALL files using the create-file: format.\n\nCREATE ALL these files using multiple ```create-file: blocks:\n{fastapi_file_list}\n\nCRITICAL:\n- main.py MUST exist and import FastAPI\n- requirements.txt MUST include "fastapi" and "uvicorn"\n- Create ALL files with COMPLETE, FUNCTIONAL code\n- Use multiple ```create-file: blocks in a single response',
                'variables': ['fastapi_file_list'],
                'description': 'Template for creating FastAPI projects',
                'tags': ['fastapi', 'python', 'api'],
                'examples': [],
                'metadata': {'framework': 'fastapi', 'language': 'python'}
            }
        ]
        
        for prompt_data in default_prompts:
            prompt = PromptTemplate(
                id=prompt_data['id'],
                name=prompt_data['name'],
                category=PromptCategory(prompt_data['category']),
                complexity=PromptComplexity(prompt_data['complexity']),
                template=prompt_data['template'],
                variables=prompt_data.get('variables', []),
                description=prompt_data.get('description', ''),
                tags=prompt_data.get('tags', []),
                examples=prompt_data.get('examples', []),
                metadata=prompt_data.get('metadata', {})
            )
            self.prompts[prompt.id] = prompt
    
    def _save_registry(self):
        """Save prompts to registry file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'version': '1.0.0',
            'prompts': [asdict(prompt) for prompt in self.prompts.values()]
        }
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get(self, prompt_id: str) -> Optional[PromptTemplate]:
        """Get prompt by ID."""
        return self.prompts.get(prompt_id)
    
    def get_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """Get all prompts in a category."""
        return [p for p in self.prompts.values() if p.category == category]
    
    def get_by_tag(self, tag: str) -> List[PromptTemplate]:
        """Get prompts with a specific tag."""
        return [p for p in self.prompts.values() if tag in p.tags]
    
    def search(self, query: str) -> List[PromptTemplate]:
        """Search prompts by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for prompt in self.prompts.values():
            if (query_lower in prompt.name.lower() or
                query_lower in prompt.description.lower() or
                any(query_lower in tag.lower() for tag in prompt.tags)):
                results.append(prompt)
        return results
    
    def register(self, prompt: PromptTemplate):
        """Register a new prompt."""
        self.prompts[prompt.id] = prompt
        self._save_registry()
    
    def render(self, prompt_id: str, **kwargs) -> str:
        """Render a prompt template with variables."""
        prompt = self.get(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")
        return prompt.render(**kwargs)


# Singleton instance
_registry: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    """Get singleton prompt registry instance."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry

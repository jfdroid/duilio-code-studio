"""
Documentation Generator Service
================================
Generate documentation from code analysis.
Creates README, docstrings, API docs, and more.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DocSection:
    """A section of documentation."""
    title: str
    content: str
    order: int = 0


@dataclass
class FunctionDoc:
    """Documentation for a function."""
    name: str
    params: List[Tuple[str, str, str]]  # (name, type, description)
    returns: Tuple[str, str]  # (type, description)
    description: str
    example: str = ""


class DocumentationGenerator:
    """
    Service for generating documentation.
    
    Features:
    - README generation
    - Docstring generation
    - API documentation
    - Changelog generation
    - License generation
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize documentation generator."""
        self.workspace_path = workspace_path
    
    def generate_readme(
        self,
        project_name: str,
        project_description: str,
        language: str,
        features: List[str] = None,
        installation: str = None,
        usage: str = None,
        include_badges: bool = True,
        include_license: bool = True,
        include_contributing: bool = True
    ) -> str:
        """
        Generate a comprehensive README.md.
        
        Args:
            project_name: Name of the project
            project_description: Project description
            language: Primary language
            features: List of features
            installation: Installation instructions
            usage: Usage examples
            include_badges: Include badge section
            include_license: Include license section
            include_contributing: Include contributing section
            
        Returns:
            README content as string
        """
        sections = []
        
        # Title and description
        sections.append(f"# {project_name}\n\n{project_description}\n")
        
        # Badges
        if include_badges:
            badges = self._generate_badges(project_name, language)
            sections.append(badges + "\n")
        
        # Table of contents
        toc = "## Table of Contents\n\n"
        toc += "- [Features](#features)\n"
        toc += "- [Installation](#installation)\n"
        toc += "- [Usage](#usage)\n"
        if include_contributing:
            toc += "- [Contributing](#contributing)\n"
        if include_license:
            toc += "- [License](#license)\n"
        sections.append(toc)
        
        # Features
        if features:
            feat_section = "## Features\n\n"
            for feature in features:
                feat_section += f"- {feature}\n"
            sections.append(feat_section)
        
        # Installation
        install_section = "## Installation\n\n"
        if installation:
            install_section += installation
        else:
            install_section += self._generate_installation(language)
        sections.append(install_section)
        
        # Usage
        usage_section = "## Usage\n\n"
        if usage:
            usage_section += usage
        else:
            usage_section += self._generate_usage(language, project_name)
        sections.append(usage_section)
        
        # Contributing
        if include_contributing:
            contrib = """## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
"""
            sections.append(contrib)
        
        # License
        if include_license:
            license_section = """## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""
            sections.append(license_section)
        
        return '\n'.join(sections)
    
    def _generate_badges(self, project_name: str, language: str) -> str:
        """Generate badge section."""
        badges = []
        
        # Language badge
        lang_colors = {
            'python': '3776AB',
            'javascript': 'F7DF1E',
            'typescript': '3178C6',
            'go': '00ADD8',
            'rust': '000000',
            'java': '007396',
            'kotlin': '7F52FF',
        }
        color = lang_colors.get(language.lower(), '333333')
        badges.append(f"![{language}](https://img.shields.io/badge/{language}-{color}?style=flat-square&logo={language.lower()}&logoColor=white)")
        
        # License badge
        badges.append("![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)")
        
        return ' '.join(badges)
    
    def _generate_installation(self, language: str) -> str:
        """Generate installation instructions based on language."""
        instructions = {
            'python': """```bash
# Clone the repository
git clone https://github.com/username/project.git
cd project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```
""",
            'javascript': """```bash
# Clone the repository
git clone https://github.com/username/project.git
cd project

# Install dependencies
npm install
```
""",
            'typescript': """```bash
# Clone the repository
git clone https://github.com/username/project.git
cd project

# Install dependencies
npm install

# Build
npm run build
```
""",
        }
        return instructions.get(language.lower(), "```bash\n# Clone and install\ngit clone https://github.com/username/project.git\n```\n")
    
    def _generate_usage(self, language: str, project_name: str) -> str:
        """Generate usage examples based on language."""
        examples = {
            'python': f"""```python
from {project_name} import main

# Example usage
result = main.run()
print(result)
```
""",
            'javascript': f"""```javascript
const {project_name} = require('{project_name}');

// Example usage
const result = {project_name}.run();
console.log(result);
```
""",
        }
        return examples.get(language.lower(), "See examples in the `examples/` directory.\n")
    
    def generate_docstring(
        self,
        function_name: str,
        params: List[Tuple[str, str]] = None,
        returns: str = None,
        description: str = None,
        style: str = "google"
    ) -> str:
        """
        Generate a docstring for a function.
        
        Args:
            function_name: Name of the function
            params: List of (param_name, param_type) tuples
            returns: Return type
            description: Function description
            style: Docstring style ('google', 'numpy', 'sphinx')
            
        Returns:
            Docstring content
        """
        if style == "google":
            return self._docstring_google(function_name, params, returns, description)
        elif style == "numpy":
            return self._docstring_numpy(function_name, params, returns, description)
        elif style == "sphinx":
            return self._docstring_sphinx(function_name, params, returns, description)
        return self._docstring_google(function_name, params, returns, description)
    
    def _docstring_google(
        self,
        name: str,
        params: List[Tuple[str, str]] = None,
        returns: str = None,
        description: str = None
    ) -> str:
        """Generate Google-style docstring."""
        lines = ['"""']
        lines.append(description or f"{name} function.")
        lines.append("")
        
        if params:
            lines.append("Args:")
            for param_name, param_type in params:
                lines.append(f"    {param_name} ({param_type}): Description of {param_name}.")
            lines.append("")
        
        if returns:
            lines.append("Returns:")
            lines.append(f"    {returns}: Description of return value.")
            lines.append("")
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def _docstring_numpy(
        self,
        name: str,
        params: List[Tuple[str, str]] = None,
        returns: str = None,
        description: str = None
    ) -> str:
        """Generate NumPy-style docstring."""
        lines = ['"""']
        lines.append(description or f"{name} function.")
        lines.append("")
        
        if params:
            lines.append("Parameters")
            lines.append("----------")
            for param_name, param_type in params:
                lines.append(f"{param_name} : {param_type}")
                lines.append(f"    Description of {param_name}.")
            lines.append("")
        
        if returns:
            lines.append("Returns")
            lines.append("-------")
            lines.append(f"{returns}")
            lines.append("    Description of return value.")
            lines.append("")
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def _docstring_sphinx(
        self,
        name: str,
        params: List[Tuple[str, str]] = None,
        returns: str = None,
        description: str = None
    ) -> str:
        """Generate Sphinx-style docstring."""
        lines = ['"""']
        lines.append(description or f"{name} function.")
        lines.append("")
        
        if params:
            for param_name, param_type in params:
                lines.append(f":param {param_name}: Description of {param_name}.")
                lines.append(f":type {param_name}: {param_type}")
            lines.append("")
        
        if returns:
            lines.append(f":returns: Description of return value.")
            lines.append(f":rtype: {returns}")
            lines.append("")
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def generate_changelog(
        self,
        versions: List[Dict[str, Any]],
        project_name: str
    ) -> str:
        """
        Generate a CHANGELOG.md file.
        
        Args:
            versions: List of version dicts with 'version', 'date', 'changes'
            project_name: Name of the project
            
        Returns:
            Changelog content
        """
        lines = ["# Changelog\n"]
        lines.append(f"All notable changes to {project_name} will be documented in this file.\n")
        lines.append("The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),")
        lines.append("and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n")
        
        for version in versions:
            ver = version.get('version', '0.0.0')
            date = version.get('date', datetime.now().strftime('%Y-%m-%d'))
            changes = version.get('changes', {})
            
            lines.append(f"## [{ver}] - {date}\n")
            
            for change_type in ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security']:
                items = changes.get(change_type.lower(), [])
                if items:
                    lines.append(f"### {change_type}\n")
                    for item in items:
                        lines.append(f"- {item}")
                    lines.append("")
        
        return '\n'.join(lines)
    
    def generate_license(self, license_type: str, author: str, year: int = None) -> str:
        """
        Generate a LICENSE file.
        
        Args:
            license_type: Type of license ('mit', 'apache', 'gpl3', 'bsd')
            author: Author/copyright holder name
            year: Copyright year
            
        Returns:
            License content
        """
        year = year or datetime.now().year
        
        licenses = {
            'mit': f"""MIT License

Copyright (c) {year} {author}

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
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
            'apache': f"""Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright {year} {author}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
""",
        }
        
        return licenses.get(license_type.lower(), licenses['mit'])
    
    def generate_api_docs(
        self,
        functions: List[FunctionDoc],
        title: str = "API Documentation"
    ) -> str:
        """
        Generate API documentation in Markdown.
        
        Args:
            functions: List of FunctionDoc objects
            title: Documentation title
            
        Returns:
            API documentation content
        """
        lines = [f"# {title}\n"]
        
        # Table of contents
        lines.append("## Functions\n")
        for func in functions:
            lines.append(f"- [{func.name}](#{func.name.lower().replace(' ', '-')})")
        lines.append("\n---\n")
        
        # Function documentation
        for func in functions:
            lines.append(f"## {func.name}\n")
            lines.append(f"{func.description}\n")
            
            if func.params:
                lines.append("### Parameters\n")
                lines.append("| Name | Type | Description |")
                lines.append("|------|------|-------------|")
                for name, type_, desc in func.params:
                    lines.append(f"| `{name}` | `{type_}` | {desc} |")
                lines.append("")
            
            if func.returns[0]:
                lines.append("### Returns\n")
                lines.append(f"- **Type:** `{func.returns[0]}`")
                lines.append(f"- **Description:** {func.returns[1]}\n")
            
            if func.example:
                lines.append("### Example\n")
                lines.append(f"```python\n{func.example}\n```\n")
            
            lines.append("---\n")
        
        return '\n'.join(lines)


# Singleton instance
_doc_generator: Optional[DocumentationGenerator] = None


def get_documentation_generator(workspace_path: Optional[str] = None) -> DocumentationGenerator:
    """Get documentation generator instance."""
    global _doc_generator
    if _doc_generator is None:
        _doc_generator = DocumentationGenerator(workspace_path)
    return _doc_generator

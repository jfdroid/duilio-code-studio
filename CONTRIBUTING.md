# Contributing to DuilioCode Studio

First off, thank you for considering contributing to DuilioCode Studio! 🎉

It's people like you that make DuilioCode Studio such a great tool for developers who value privacy and local AI.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, screenshots)
- **Describe the behavior you observed and what you expected**
- **Include your environment details** (OS, Python version, Ollama version)

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any alternative solutions you've considered**

### 🔧 Pull Requests

1. Fork the repo and create your branch from `master`
2. If you've added code that should be tested, add tests
3. Ensure your code follows the project's style guidelines
4. Make sure your code lints without errors
5. Issue your pull request!

## Development Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- Git

### Getting Started

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/duilio-code-studio.git
cd duilio-code-studio

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull a model (if not already)
ollama pull qwen2.5-coder:7b

# Start the development server
./start.sh
```

### Project Structure

```
duilio-code-studio/
├── src/
│   ├── api/           # FastAPI routes
│   ├── core/          # Configuration, exceptions
│   ├── services/      # Business logic
│   └── schemas/       # Pydantic models
├── web/
│   ├── templates/     # HTML templates
│   └── static/        # CSS, JS, images
└── tests/             # Test files
```

## Pull Request Process

1. **Update the README.md** with details of changes if applicable
2. **Update documentation** for any new features
3. **Add tests** for new functionality
4. **Follow the commit message convention** (see below)
5. **Request a review** from maintainers

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting, no code change
refactor: code restructuring
test: adding tests
chore: maintenance tasks
```

Examples:
```
feat: add path autocomplete to Open Folder dialog
fix: resolve file encoding issue on Windows
docs: update installation instructions
```

## Style Guidelines

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where possible
- Write docstrings for public functions
- Keep functions small and focused

```python
def my_function(param: str) -> Dict[str, Any]:
    """
    Brief description.
    
    Args:
        param: Description of param
        
    Returns:
        Description of return value
    """
    pass
```

### JavaScript

- Use modern ES6+ syntax
- Use `const` and `let`, avoid `var`
- Use meaningful variable names
- Add comments for complex logic

### HTML/CSS

- Use semantic HTML elements
- Follow BEM naming convention for CSS classes
- Keep styles organized and commented

## 🏆 Recognition

Contributors will be recognized in:
- The project README
- Release notes
- Our contributors page

## Questions?

Feel free to open an issue with the tag `question` if you have any questions about contributing.

---

Thank you for contributing to DuilioCode Studio! 🚀

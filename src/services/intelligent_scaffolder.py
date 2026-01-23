"""
Intelligent Project Scaffolder Service
======================================
Analyzes user requests and generates complete project structures intelligently.
Uses AI to understand project requirements and create comprehensive project plans.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import re
import json


@dataclass
class ProjectPlan:
    """Plan for a complete project structure."""
    project_type: str  # e.g., "react", "fastapi", "android"
    tech_stack: List[str]  # e.g., ["react", "typescript", "vite"]
    structure: Dict[str, Any]  # Directory structure
    files: List[Dict[str, str]]  # List of files to create: [{"path": "...", "content": "..."}]
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # package.json dependencies
    description: str = ""


class IntelligentProjectScaffolder:
    """
    Intelligent project scaffolder that analyzes user requests
    and generates complete project structures.
    
    Features:
    - Detects project type from user request
    - Identifies technology stack
    - Plans complete directory structure
    - Generates all necessary files
    - Validates structure
    """
    
    def __init__(self):
        """Initialize the intelligent scaffolder."""
        self.project_patterns = self._load_project_patterns()
        self.tech_stack_patterns = self._load_tech_stack_patterns()
    
    def _load_project_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for detecting project types."""
        return {
            "react": ["react", "reactjs", "react.js", "create-react-app", "vite react"],
            "vue": ["vue", "vuejs", "vue.js", "nuxt", "nuxtjs"],
            "angular": ["angular", "angularjs"],
            "nextjs": ["next", "next.js", "nextjs"],
            "fastapi": ["fastapi", "fast api"],
            "flask": ["flask"],
            "django": ["django"],
            "express": ["express", "expressjs", "node.js", "nodejs"],
            "android": ["android", "kotlin android", "android app"],
            "ios": ["ios", "swift", "swiftui"],
            "python-cli": ["python cli", "command line", "cli tool"],
            "typescript-lib": ["typescript library", "ts library", "npm package"],
            "python-lib": ["python library", "python package", "pip package"],
        }
    
    def _load_tech_stack_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for detecting technology stack."""
        return {
            "typescript": ["typescript", "ts", ".ts", ".tsx"],
            "javascript": ["javascript", "js", ".js", ".jsx"],
            "python": ["python", "py", ".py"],
            "kotlin": ["kotlin", "kt", ".kt"],
            "java": ["java", ".java"],
            "vite": ["vite"],
            "webpack": ["webpack"],
            "tailwind": ["tailwind", "tailwindcss"],
            "bootstrap": ["bootstrap"],
            "material-ui": ["material-ui", "mui", "@mui"],
            "redux": ["redux"],
            "zustand": ["zustand"],
            "pytest": ["pytest"],
            "jest": ["jest"],
            "vitest": ["vitest"],
        }
    
    def analyze_request(self, user_request: str) -> ProjectPlan:
        """
        Analyze user request and create a project plan.
        
        Args:
            user_request: User's request for project creation
            
        Returns:
            ProjectPlan with complete structure
        """
        user_request_lower = user_request.lower()
        
        # Detect project type
        project_type = self._detect_project_type(user_request_lower)
        
        # Detect tech stack
        tech_stack = self._detect_tech_stack(user_request_lower)
        
        # Plan structure based on project type
        structure = self._plan_structure(project_type, tech_stack)
        
        # Generate file list
        files = self._generate_file_list(project_type, tech_stack, structure)
        
        # Generate dependencies
        dependencies = self._generate_dependencies(project_type, tech_stack)
        
        # Generate description
        description = self._generate_description(project_type, tech_stack)
        
        return ProjectPlan(
            project_type=project_type,
            tech_stack=tech_stack,
            structure=structure,
            files=files,
            dependencies=dependencies,
            description=description
        )
    
    def _detect_project_type(self, request: str) -> str:
        """Detect project type from user request."""
        for project_type, patterns in self.project_patterns.items():
            for pattern in patterns:
                if pattern in request:
                    return project_type
        
        # Default to web if no specific type detected
        return "web"
    
    def _detect_tech_stack(self, request: str) -> List[str]:
        """Detect technology stack from user request."""
        detected = []
        
        for tech, patterns in self.tech_stack_patterns.items():
            for pattern in patterns:
                if pattern in request:
                    detected.append(tech)
                    break
        
        # Defaults based on project type
        if not detected:
            if "react" in request or "vue" in request:
                detected = ["javascript", "react" if "react" in request else "vue"]
            elif "python" in request:
                detected = ["python"]
        
        return detected if detected else ["javascript"]
    
    def _plan_structure(self, project_type: str, tech_stack: List[str]) -> Dict[str, Any]:
        """Plan directory structure based on project type."""
        structures = {
            "react": {
                "directories": [
                    "src",
                    "src/components",
                    "src/hooks",
                    "src/utils",
                    "src/services",
                    "src/styles",
                    "public"
                ],
                "config_files": ["package.json", "tsconfig.json", ".gitignore"],
                "entry_points": ["src/index.js", "src/App.jsx", "public/index.html"]
            },
            "vue": {
                "directories": [
                    "src",
                    "src/components",
                    "src/composables",
                    "src/utils",
                    "src/services",
                    "public"
                ],
                "config_files": ["package.json", "vite.config.js", ".gitignore"],
                "entry_points": ["src/main.js", "src/App.vue", "index.html"]
            },
            "fastapi": {
                "directories": [
                    "src",
                    "src/api",
                    "src/api/routes",
                    "src/services",
                    "src/models",
                    "src/utils",
                    "tests"
                ],
                "config_files": ["requirements.txt", "pyproject.toml", ".gitignore"],
                "entry_points": ["src/main.py"]
            },
            "express": {
                "directories": [
                    "src",
                    "src/routes",
                    "src/controllers",
                    "src/models",
                    "src/middleware",
                    "src/utils",
                    "public"
                ],
                "config_files": ["package.json", ".gitignore"],
                "entry_points": ["src/index.js", "src/app.js"]
            },
            "android": {
                "directories": [
                    "app/src/main/java",
                    "app/src/main/res",
                    "app/src/main/res/layout",
                    "app/src/main/res/values"
                ],
                "config_files": ["build.gradle", "settings.gradle", ".gitignore"],
                "entry_points": ["app/src/main/AndroidManifest.xml"]
            },
        }
        
        return structures.get(project_type, {
            "directories": ["src", "public"],
            "config_files": [],
            "entry_points": []
        })
    
    def _generate_file_list(
        self, 
        project_type: str, 
        tech_stack: List[str], 
        structure: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate list of files to create."""
        files = []
        
        # Add directory structure files (useful files, not empty)
        for directory in structure.get("directories", []):
            # Create index.js or similar in each directory
            if "components" in directory:
                files.append({
                    "path": f"{directory}/index.js",
                    "content": "// Component exports\n"
                })
            elif "hooks" in directory:
                files.append({
                    "path": f"{directory}/index.js",
                    "content": "// Hook exports\n"
                })
            elif "utils" in directory:
                files.append({
                    "path": f"{directory}/index.js",
                    "content": "// Utility functions\n"
                })
            elif "services" in directory:
                files.append({
                    "path": f"{directory}/index.js",
                    "content": "// Service exports\n"
                })
        
        # Add entry point files
        for entry_point in structure.get("entry_points", []):
            if entry_point.endswith(".html"):
                files.append({
                    "path": entry_point,
                    "content": self._generate_html_template(project_type)
                })
            elif entry_point.endswith(".js") or entry_point.endswith(".jsx"):
                files.append({
                    "path": entry_point,
                    "content": self._generate_js_entry(project_type, entry_point)
                })
            elif entry_point.endswith(".py"):
                files.append({
                    "path": entry_point,
                    "content": self._generate_python_entry(project_type)
                })
        
        # Add config files
        for config_file in structure.get("config_files", []):
            if config_file == "package.json":
                files.append({
                    "path": config_file,
                    "content": self._generate_package_json(project_type, tech_stack)
                })
            elif config_file == "requirements.txt":
                files.append({
                    "path": config_file,
                    "content": self._generate_requirements_txt(project_type)
                })
            elif config_file == ".gitignore":
                files.append({
                    "path": config_file,
                    "content": self._generate_gitignore(project_type)
                })
        
        # Add README
        files.append({
            "path": "README.md",
            "content": self._generate_readme(project_type, tech_stack)
        })
        
        return files
    
    def _generate_dependencies(self, project_type: str, tech_stack: List[str]) -> Dict[str, List[str]]:
        """Generate dependencies for package.json or requirements.txt."""
        dependencies = {
            "react": {
                "dependencies": ["react", "react-dom"],
                "devDependencies": ["@vitejs/plugin-react", "vite"]
            },
            "vue": {
                "dependencies": ["vue"],
                "devDependencies": ["@vitejs/plugin-vue", "vite"]
            },
            "fastapi": {
                "dependencies": ["fastapi", "uvicorn", "pydantic"]
            },
            "express": {
                "dependencies": ["express"],
                "devDependencies": ["nodemon"]
            }
        }
        
        return dependencies.get(project_type, {})
    
    def _generate_description(self, project_type: str, tech_stack: List[str]) -> str:
        """Generate project description."""
        return f"{project_type.title()} project with {', '.join(tech_stack)}"
    
    def _generate_html_template(self, project_type: str) -> str:
        """Generate HTML template."""
        if project_type == "react":
            return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React App</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
</body>
</html>"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>App</title>
</head>
<body>
    <div id="app"></div>
</body>
</html>"""
    
    def _generate_js_entry(self, project_type: str, entry_point: str) -> str:
        """Generate JavaScript entry point."""
        if "App.jsx" in entry_point:
            return """import React from 'react';

function App() {
    return (
        <div className="App">
            <h1>Welcome to React</h1>
        </div>
    );
}

export default App;"""
        elif "index.js" in entry_point:
            return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);"""
        return "// Entry point\n"
    
    def _generate_python_entry(self, project_type: str) -> str:
        """Generate Python entry point."""
        if project_type == "fastapi":
            return """from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)"""
        return "# Entry point\n"
    
    def _generate_package_json(self, project_type: str, tech_stack: List[str]) -> str:
        """Generate package.json."""
        deps = self._generate_dependencies(project_type, tech_stack)
        dependencies = deps.get("dependencies", [])
        dev_dependencies = deps.get("devDependencies", [])
        
        # Convert lists to dict format for package.json
        deps_dict = {dep: "^latest" for dep in dependencies} if isinstance(dependencies, list) else dependencies
        dev_deps_dict = {dep: "^latest" for dep in dev_dependencies} if isinstance(dev_dependencies, list) else dev_dependencies
        
        return f"""{{
  "name": "my-project",
  "version": "1.0.0",
  "description": "{self._generate_description(project_type, tech_stack)}",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {json.dumps(deps_dict, indent=2)},
  "devDependencies": {json.dumps(dev_deps_dict, indent=2)}
}}"""
    
    def _generate_requirements_txt(self, project_type: str) -> str:
        """Generate requirements.txt."""
        deps = self._generate_dependencies(project_type, [])
        dependencies = deps.get("dependencies", [])
        return "\n".join(dependencies) if dependencies else "# Requirements\n"
    
    def _generate_gitignore(self, project_type: str) -> str:
        """Generate .gitignore."""
        if project_type in ["react", "vue", "nextjs"]:
            return """node_modules/
dist/
build/
.env
.env.local
.DS_Store"""
        elif project_type in ["fastapi", "flask", "django"]:
            return """__pycache__/
*.py[cod]
*$py.class
.env
venv/
.venv/"""
        return ".DS_Store\n"
    
    def _generate_readme(self, project_type: str, tech_stack: List[str]) -> str:
        """Generate README.md."""
        return f"""# {project_type.title()} Project

## Description
{self._generate_description(project_type, tech_stack)}

## Tech Stack
{', '.join(tech_stack)}

## Getting Started

### Installation
\`\`\`bash
npm install
\`\`\`

### Development
\`\`\`bash
npm run dev
\`\`\`

## License
MIT
"""
    
    def generate_create_file_actions(self, plan: ProjectPlan) -> str:
        """
        Generate create-file actions string for AI to use.
        
        Returns:
            String with all create-file blocks formatted for AI response
        """
        actions = []
        
        for file_info in plan.files:
            path = file_info["path"]
            content = file_info["content"]
            actions.append(f"```create-file:{path}\n{content}\n```")
        
        return "\n\n".join(actions)


# Singleton instance
_intelligent_scaffolder: IntelligentProjectScaffolder = None


def get_intelligent_scaffolder() -> IntelligentProjectScaffolder:
    """Get or create IntelligentProjectScaffolder instance."""
    global _intelligent_scaffolder
    if _intelligent_scaffolder is None:
        _intelligent_scaffolder = IntelligentProjectScaffolder()
    return _intelligent_scaffolder

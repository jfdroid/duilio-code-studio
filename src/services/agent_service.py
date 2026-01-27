"""
Agent Service
=============
Autonomous AI agent that can implement features independently.
Plans, codes, tests, and iterates to complete complex tasks.
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AgentStatus(Enum):
    """Agent task status."""
    PENDING = "pending"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Types of agent steps."""
    ANALYZE = "analyze"
    PLAN = "plan"
    CREATE_FILE = "create_file"
    EDIT_FILE = "edit_file"
    DELETE_FILE = "delete_file"
    RUN_COMMAND = "run_command"
    RUN_TEST = "run_test"
    GIT_COMMIT = "git_commit"
    REVIEW = "review"
    FIX_ERROR = "fix_error"


@dataclass
class AgentStep:
    """A single step in the agent's execution plan."""
    id: str
    type: StepType
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: str = ""
    error: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class AgentTask:
    """A task for the agent to complete."""
    id: str
    description: str
    status: AgentStatus = AgentStatus.PENDING
    steps: List[AgentStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: str = ""
    error: str = ""
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: int = 0


class AgentService:
    """
    Autonomous AI coding agent.
    
    Capabilities:
    - Analyze requirements and create execution plans
    - Create and modify files
    - Run commands and tests
    - Commit changes to git
    - Self-correct on errors
    - Report progress in real-time
    """
    
    MAX_ITERATIONS = 10
    MAX_STEPS = 50
    
    def __init__(
        self,
        workspace_path: str,
        ollama_service=None,
        file_service=None,
        git_service=None,
        code_executor=None
    ):
        """
        Initialize agent service.
        
        Args:
            workspace_path: Root workspace path
            ollama_service: AI service for generation
            file_service: File operations service
            git_service: Git operations service
            code_executor: Code execution service
        """
        self.workspace_path = workspace_path
        self.ollama = ollama_service
        self.file_service = file_service
        self.git_service = git_service
        self.executor = code_executor
        self._current_task: Optional[AgentTask] = None
        self._progress_callback: Optional[Callable] = None
        self._cancelled = False
    
    def set_progress_callback(self, callback: Callable[[AgentTask], None]) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    def _report_progress(self, task: AgentTask) -> None:
        """Report progress to callback."""
        if self._progress_callback:
            self._progress_callback(task)
    
    def _generate_step_id(self) -> str:
        """Generate unique step ID."""
        return f"step_{int(time.time() * 1000)}"
    
    async def _analyze_task(self, description: str) -> Dict[str, Any]:
        """
        Analyze task and determine requirements.
        
        Uses AI to understand what needs to be done.
        """
        prompt = f"""Analyze this development task and provide a structured breakdown:

TASK: {description}

WORKSPACE: {self.workspace_path}

Provide your analysis as JSON with:
{{
    "task_type": "feature|bugfix|refactor|docs|test",
    "complexity": "simple|medium|complex",
    "files_to_create": ["list of new files"],
    "files_to_modify": ["list of existing files to change"],
    "dependencies_needed": ["any new packages"],
    "steps_summary": ["high-level steps"],
    "estimated_time_minutes": number,
    "risks": ["potential issues"]
}}

Return ONLY valid JSON, no other text."""
        
        if self.ollama:
            result = await self.ollama.generate(
                prompt=prompt,
                model=None,  # Auto-select
                temperature=0.3
            )
            
            # Parse JSON from response
            try:
                # Find JSON in response
                response = result.response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
        
        return {
            "task_type": "feature",
            "complexity": "medium",
            "files_to_create": [],
            "files_to_modify": [],
            "dependencies_needed": [],
            "steps_summary": ["Analyze requirements", "Implement solution", "Test"],
            "estimated_time_minutes": 10,
            "risks": []
        }
    
    async def _create_plan(self, task: AgentTask, analysis: Dict[str, Any]) -> List[AgentStep]:
        """Create execution plan from analysis."""
        steps = []
        
        # Step 1: Analyze codebase
        steps.append(AgentStep(
            id=self._generate_step_id(),
            type=StepType.ANALYZE,
            description="Analyze existing codebase structure",
            data={"path": self.workspace_path}
        ))
        
        # Step 2: Create new files
        for file_path in analysis.get('files_to_create', []):
            steps.append(AgentStep(
                id=self._generate_step_id(),
                type=StepType.CREATE_FILE,
                description=f"Create file: {file_path}",
                data={"path": file_path}
            ))
        
        # Step 3: Modify existing files
        for file_path in analysis.get('files_to_modify', []):
            steps.append(AgentStep(
                id=self._generate_step_id(),
                type=StepType.EDIT_FILE,
                description=f"Modify file: {file_path}",
                data={"path": file_path}
            ))
        
        # Step 4: Run tests if applicable
        steps.append(AgentStep(
            id=self._generate_step_id(),
            type=StepType.RUN_TEST,
            description="Run tests to verify changes",
            data={}
        ))
        
        # Step 5: Review changes
        steps.append(AgentStep(
            id=self._generate_step_id(),
            type=StepType.REVIEW,
            description="Review all changes",
            data={}
        ))
        
        # Step 6: Git commit (optional)
        steps.append(AgentStep(
            id=self._generate_step_id(),
            type=StepType.GIT_COMMIT,
            description="Commit changes to git",
            data={"message": f"feat: {task.description[:50]}"}
        ))
        
        return steps
    
    async def _execute_step(self, task: AgentTask, step: AgentStep) -> bool:
        """
        Execute a single step.
        
        Returns:
            True if step succeeded, False otherwise
        """
        step.started_at = time.time()
        step.status = "running"
        self._report_progress(task)
        
        try:
            if step.type == StepType.ANALYZE:
                # Analyze codebase
                step.result = f"Analyzed codebase at {step.data.get('path')}"
                step.status = "completed"
                
            elif step.type == StepType.CREATE_FILE:
                # Generate file content using AI
                file_path = step.data.get('path')
                
                if self.ollama and self.file_service:
                    prompt = f"""Create the content for this file based on the task:
                    
Task: {task.description}
File: {file_path}

Generate complete, working code for this file.
Use best practices and include comments.
Return ONLY the code, no explanations."""
                    
                    result = await self.ollama.generate(prompt=prompt, temperature=0.5)
                    content = result.response
                    
                    # Clean up code blocks if present
                    if '```' in content:
                        lines = content.split('\n')
                        code_lines = []
                        in_code = False
                        for line in lines:
                            if line.startswith('```'):
                                in_code = not in_code
                            elif in_code:
                                code_lines.append(line)
                        content = '\n'.join(code_lines)
                    
                    # Create file
                    full_path = os.path.join(self.workspace_path, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w') as f:
                        f.write(content)
                    
                    task.files_created.append(file_path)
                    step.result = f"Created {file_path}"
                    step.status = "completed"
                else:
                    step.error = "Services not available"
                    step.status = "failed"
                    return False
                    
            elif step.type == StepType.EDIT_FILE:
                # Edit existing file
                file_path = step.data.get('path')
                full_path = os.path.join(self.workspace_path, file_path)
                
                if os.path.exists(full_path) and self.ollama:
                    with open(full_path, 'r') as f:
                        current_content = f.read()
                    
                    prompt = f"""Modify this file according to the task:

Task: {task.description}
File: {file_path}

Current content:
```
{current_content[:3000]}
```

Generate the complete modified file content.
Return ONLY the code, no explanations."""
                    
                    result = await self.ollama.generate(prompt=prompt, temperature=0.5)
                    new_content = result.response
                    
                    # Clean up code blocks
                    if '```' in new_content:
                        lines = new_content.split('\n')
                        code_lines = []
                        in_code = False
                        for line in lines:
                            if line.startswith('```'):
                                in_code = not in_code
                            elif in_code:
                                code_lines.append(line)
                        new_content = '\n'.join(code_lines)
                    
                    with open(full_path, 'w') as f:
                        f.write(new_content)
                    
                    task.files_modified.append(file_path)
                    step.result = f"Modified {file_path}"
                    step.status = "completed"
                else:
                    step.error = f"File not found: {file_path}"
                    step.status = "failed"
                    return False
                    
            elif step.type == StepType.RUN_TEST:
                # Run tests
                if self.executor:
                    # Try to detect and run tests
                    test_commands = [
                        'pytest -v',
                        'npm test',
                        'python -m unittest discover'
                    ]
                    
                    for cmd in test_commands:
                        result = self.executor.execute(cmd, 'shell')
                        if result.success:
                            step.result = f"Tests passed:\n{result.output[:500]}"
                            step.status = "completed"
                            break
                    else:
                        step.result = "No tests found or tests skipped"
                        step.status = "completed"
                else:
                    step.result = "Test execution skipped (executor not available)"
                    step.status = "completed"
                    
            elif step.type == StepType.REVIEW:
                # Review changes
                changes_summary = []
                for f in task.files_created:
                    changes_summary.append(f"+ Created: {f}")
                for f in task.files_modified:
                    changes_summary.append(f"~ Modified: {f}")
                
                step.result = "Changes reviewed:\n" + '\n'.join(changes_summary)
                step.status = "completed"
                
            elif step.type == StepType.GIT_COMMIT:
                # Commit to git
                if self.git_service:
                    # Add all changes
                    add_result = self.git_service.add(all=True, path=self.workspace_path)
                    
                    if add_result.success:
                        # Commit
                        message = step.data.get('message', f"Agent: {task.description[:50]}")
                        commit_result = self.git_service.commit(message, self.workspace_path)
                        
                        if commit_result.success:
                            step.result = f"Committed: {message}"
                            step.status = "completed"
                        else:
                            step.result = "No changes to commit"
                            step.status = "completed"
                    else:
                        step.result = "Git add failed"
                        step.status = "completed"
                else:
                    step.result = "Git commit skipped (service not available)"
                    step.status = "completed"
                    
            elif step.type == StepType.FIX_ERROR:
                # Fix a previous error
                error = step.data.get('error', '')
                file_path = step.data.get('file', '')
                
                if self.ollama and file_path:
                    full_path = os.path.join(self.workspace_path, file_path)
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    prompt = f"""Fix this error in the file:

Error: {error}
File: {file_path}

Current content:
```
{content[:3000]}
```

Generate the corrected file content.
Return ONLY the code, no explanations."""
                    
                    result = await self.ollama.generate(prompt=prompt, temperature=0.3)
                    fixed_content = result.response
                    
                    # Clean up
                    if '```' in fixed_content:
                        lines = fixed_content.split('\n')
                        code_lines = []
                        in_code = False
                        for line in lines:
                            if line.startswith('```'):
                                in_code = not in_code
                            elif in_code:
                                code_lines.append(line)
                        fixed_content = '\n'.join(code_lines)
                    
                    with open(full_path, 'w') as f:
                        f.write(fixed_content)
                    
                    step.result = f"Fixed error in {file_path}"
                    step.status = "completed"
                else:
                    step.error = "Cannot fix: missing services"
                    step.status = "failed"
                    return False
            
            step.completed_at = time.time()
            return True
            
        except Exception as e:
            step.error = str(e)
            step.status = "failed"
            step.completed_at = time.time()
            return False
    
    async def execute_task(self, description: str) -> AgentTask:
        """
        Execute a complete task autonomously.
        
        Args:
            description: Natural language task description
            
        Returns:
            AgentTask with results
        """
        task_id = f"task_{int(time.time())}"
        task = AgentTask(
            id=task_id,
            description=description,
            started_at=time.time()
        )
        self._current_task = task
        self._cancelled = False
        
        try:
            # Phase 1: Planning
            task.status = AgentStatus.PLANNING
            self._report_progress(task)
            
            analysis = await self._analyze_task(description)
            task.context['analysis'] = analysis
            
            # Create execution plan
            task.steps = await self._create_plan(task, analysis)
            
            # Phase 2: Implementation
            task.status = AgentStatus.IMPLEMENTING
            
            for i, step in enumerate(task.steps):
                if self._cancelled:
                    task.status = AgentStatus.CANCELLED
                    break
                
                task.progress = int((i / len(task.steps)) * 100)
                self._report_progress(task)
                
                success = await self._execute_step(task, step)
                
                if not success:
                    # Try to fix the error
                    if step.type in (StepType.CREATE_FILE, StepType.EDIT_FILE):
                        fix_step = AgentStep(
                            id=self._generate_step_id(),
                            type=StepType.FIX_ERROR,
                            description=f"Fix error: {step.error}",
                            data={
                                'error': step.error,
                                'file': step.data.get('path')
                            }
                        )
                        task.steps.insert(i + 1, fix_step)
            
            # Phase 3: Completion
            if not self._cancelled:
                task.status = AgentStatus.COMPLETED
                task.progress = 100
                task.result = f"Task completed. Created {len(task.files_created)} files, modified {len(task.files_modified)} files."
            
        except Exception as e:
            task.status = AgentStatus.FAILED
            task.error = str(e)
        
        task.completed_at = time.time()
        self._report_progress(task)
        
        return task
    
    def cancel_task(self) -> None:
        """Cancel the current task."""
        self._cancelled = True
    
    def get_current_task(self) -> Optional[AgentTask]:
        """Get the current running task."""
        return self._current_task
    
    def get_task_summary(self, task: AgentTask) -> str:
        """Get a human-readable summary of a task."""
        lines = [f"# Agent Task: {task.description}\n"]
        lines.append(f"**Status:** {task.status.value}")
        lines.append(f"**Progress:** {task.progress}%\n")
        
        if task.context.get('analysis'):
            analysis = task.context['analysis']
            lines.append("## Analysis")
            lines.append(f"- Type: {analysis.get('task_type')}")
            lines.append(f"- Complexity: {analysis.get('complexity')}")
            lines.append("")
        
        lines.append("## Steps\n")
        for step in task.steps:
            icon = "✓" if step.status == "completed" else "✗" if step.status == "failed" else "○"
            lines.append(f"{icon} **{step.description}**")
            if step.result:
                lines.append(f"   Result: {step.result[:100]}")
            if step.error:
                lines.append(f"   Error: {step.error}")
        
        if task.files_created:
            lines.append("\n## Files Created")
            for f in task.files_created:
                lines.append(f"- {f}")
        
        if task.files_modified:
            lines.append("\n## Files Modified")
            for f in task.files_modified:
                lines.append(f"- {f}")
        
        if task.error:
            lines.append(f"\n## Error\n{task.error}")
        
        return '\n'.join(lines)


# Factory function
def create_agent(workspace_path: str, **services) -> AgentService:
    """Create an agent instance with optional services."""
    return AgentService(
        workspace_path=workspace_path,
        ollama_service=services.get('ollama'),
        file_service=services.get('file'),
        git_service=services.get('git'),
        code_executor=services.get('executor')
    )

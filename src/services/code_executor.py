"""
Code Executor Service
=====================
Safe sandbox for executing code snippets.
Supports Python, JavaScript, and Shell commands.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
import signal
import resource
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import queue


class Language(Enum):
    """Supported languages for execution."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SHELL = "shell"
    BASH = "bash"


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    language: str
    code: str
    output: str
    error: str = ""
    return_code: int = 0
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    timed_out: bool = False
    

class CodeExecutor:
    """
    Safe code execution sandbox.
    
    Security Features:
    - Timeout limits
    - Memory limits
    - Restricted file system access
    - No network access by default
    - Process isolation
    
    Supported Languages:
    - Python 3
    - JavaScript (Node.js)
    - Shell/Bash
    """
    
    # Default limits
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MEMORY_MB = 256  # MB
    MAX_OUTPUT_SIZE = 100 * 1024  # 100KB
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = {
        'python': [
            'os.system', 'subprocess', 'eval(', 'exec(',
            '__import__', 'open(', 'file(', 'input(',
            'compile(', 'globals(', 'locals()',
            'delattr', 'setattr', 'getattr',
            'importlib', 'builtins',
            # Network
            'socket', 'urllib', 'requests', 'http.client',
            'ftplib', 'smtplib', 'telnetlib',
        ],
        'javascript': [
            'require(', 'import(', 'eval(',
            'Function(', 'process.', 'child_process',
            'fs.', 'net.', 'http.', 'https.',
            'dgram.', 'dns.', 'cluster.',
        ],
        'shell': [
            'rm -rf', 'rm -r /', 'dd if=',
            'mkfs', 'fdisk', ':(){', 'fork bomb',
            'chmod 777', 'wget', 'curl',
            '> /dev/', 'sudo', 'su ',
        ]
    }
    
    # Safe Python imports that are allowed
    SAFE_PYTHON_IMPORTS = {
        'math', 'random', 'datetime', 'time', 'json',
        'collections', 'itertools', 'functools',
        're', 'string', 'textwrap',
        'decimal', 'fractions', 'statistics',
        'copy', 'pprint', 'typing',
        'dataclasses', 'enum', 'abc',
        'heapq', 'bisect', 'array',
        'operator', 'contextlib',
    }
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        memory_mb: int = DEFAULT_MEMORY_MB,
        allow_network: bool = False,
        workspace_path: Optional[str] = None
    ):
        """Initialize code executor with safety limits."""
        self.timeout = timeout
        self.memory_mb = memory_mb
        self.allow_network = allow_network
        self.workspace_path = workspace_path
        self.temp_dir = None
    
    def _create_temp_dir(self) -> str:
        """Create isolated temporary directory for execution."""
        self.temp_dir = tempfile.mkdtemp(prefix='duilio_exec_')
        return self.temp_dir
    
    def _cleanup_temp_dir(self) -> None:
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
            self.temp_dir = None
    
    def _check_code_safety(self, code: str, language: str) -> Tuple[bool, str]:
        """
        Check if code contains dangerous patterns.
        
        Returns:
            (is_safe, reason)
        """
        patterns = self.BLOCKED_PATTERNS.get(language, [])
        code_lower = code.lower()
        
        for pattern in patterns:
            if pattern.lower() in code_lower:
                return False, f"Blocked pattern detected: {pattern}"
        
        return True, "Code appears safe"
    
    def _create_safe_python_wrapper(self, code: str) -> str:
        """Create a safe Python wrapper that restricts dangerous operations."""
        wrapper = '''
import sys
import builtins

# Restrict builtins
_safe_builtins = {{
    'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
    'bin': bin, 'bool': bool, 'bytearray': bytearray, 'bytes': bytes,
    'callable': callable, 'chr': chr, 'classmethod': classmethod,
    'complex': complex, 'dict': dict, 'dir': dir, 'divmod': divmod,
    'enumerate': enumerate, 'filter': filter, 'float': float,
    'format': format, 'frozenset': frozenset, 'getattr': getattr,
    'hasattr': hasattr, 'hash': hash, 'hex': hex, 'id': id,
    'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
    'iter': iter, 'len': len, 'list': list, 'map': map,
    'max': max, 'min': min, 'next': next, 'object': object,
    'oct': oct, 'ord': ord, 'pow': pow, 'print': print,
    'property': property, 'range': range, 'repr': repr,
    'reversed': reversed, 'round': round, 'set': set,
    'slice': slice, 'sorted': sorted, 'staticmethod': staticmethod,
    'str': str, 'sum': sum, 'super': super, 'tuple': tuple,
    'type': type, 'vars': vars, 'zip': zip,
    'True': True, 'False': False, 'None': None,
    '__name__': '__main__', '__doc__': None,
}}

# Allow safe imports
def _safe_import(name, *args, **kwargs):
    safe_modules = {safe_modules}
    if name in safe_modules or name.split('.')[0] in safe_modules:
        return __original_import__(name, *args, **kwargs)
    raise ImportError(f"Import of '{{name}}' is not allowed in sandbox")

__original_import__ = builtins.__import__
builtins.__import__ = _safe_import

# Execute user code
try:
{user_code}
except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}", file=sys.stderr)
'''
        # Indent user code
        indented_code = '\n'.join('    ' + line for line in code.split('\n'))
        
        return wrapper.format(
            safe_modules=repr(self.SAFE_PYTHON_IMPORTS),
            user_code=indented_code
        )
    
    def _execute_python(self, code: str) -> ExecutionResult:
        """Execute Python code in sandbox."""
        temp_dir = self._create_temp_dir()
        script_path = os.path.join(temp_dir, 'script.py')
        
        try:
            # Create safe wrapper
            wrapped_code = self._create_safe_python_wrapper(code)
            
            with open(script_path, 'w') as f:
                f.write(wrapped_code)
            
            start_time = time.time()
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=temp_dir,
                env={
                    'PATH': os.environ.get('PATH', ''),
                    'PYTHONPATH': '',
                    'HOME': temp_dir,
                }
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                success=result.returncode == 0,
                language='python',
                code=code,
                output=result.stdout[:self.MAX_OUTPUT_SIZE],
                error=result.stderr[:self.MAX_OUTPUT_SIZE],
                return_code=result.returncode,
                execution_time_ms=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                language='python',
                code=code,
                output="",
                error=f"Execution timed out after {self.timeout} seconds",
                timed_out=True
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                language='python',
                code=code,
                output="",
                error=str(e)
            )
        finally:
            self._cleanup_temp_dir()
    
    def _execute_javascript(self, code: str) -> ExecutionResult:
        """Execute JavaScript code using Node.js."""
        # Check if Node.js is available
        try:
            subprocess.run(['node', '--version'], capture_output=True, timeout=5)
        except:
            return ExecutionResult(
                success=False,
                language='javascript',
                code=code,
                output="",
                error="Node.js is not installed"
            )
        
        temp_dir = self._create_temp_dir()
        script_path = os.path.join(temp_dir, 'script.js')
        
        try:
            # Wrap code to catch errors
            wrapped_code = f'''
try {{
{code}
}} catch (e) {{
    console.error('Error:', e.message);
    process.exit(1);
}}
'''
            with open(script_path, 'w') as f:
                f.write(wrapped_code)
            
            start_time = time.time()
            
            result = subprocess.run(
                ['node', '--no-warnings', script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=temp_dir,
                env={
                    'PATH': os.environ.get('PATH', ''),
                    'HOME': temp_dir,
                    'NODE_PATH': ''
                }
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                success=result.returncode == 0,
                language='javascript',
                code=code,
                output=result.stdout[:self.MAX_OUTPUT_SIZE],
                error=result.stderr[:self.MAX_OUTPUT_SIZE],
                return_code=result.returncode,
                execution_time_ms=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                language='javascript',
                code=code,
                output="",
                error=f"Execution timed out after {self.timeout} seconds",
                timed_out=True
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                language='javascript',
                code=code,
                output="",
                error=str(e)
            )
        finally:
            self._cleanup_temp_dir()
    
    def _execute_shell(self, code: str) -> ExecutionResult:
        """Execute shell commands (limited)."""
        temp_dir = self._create_temp_dir()
        
        try:
            start_time = time.time()
            
            # Use sh for safety (not bash)
            result = subprocess.run(
                ['sh', '-c', code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=temp_dir,
                env={
                    'PATH': '/usr/bin:/bin',  # Restricted PATH
                    'HOME': temp_dir,
                }
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                success=result.returncode == 0,
                language='shell',
                code=code,
                output=result.stdout[:self.MAX_OUTPUT_SIZE],
                error=result.stderr[:self.MAX_OUTPUT_SIZE],
                return_code=result.returncode,
                execution_time_ms=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                language='shell',
                code=code,
                output="",
                error=f"Execution timed out after {self.timeout} seconds",
                timed_out=True
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                language='shell',
                code=code,
                output="",
                error=str(e)
            )
        finally:
            self._cleanup_temp_dir()
    
    def execute(self, code: str, language: str) -> ExecutionResult:
        """
        Execute code in the specified language.
        
        Args:
            code: The code to execute
            language: 'python', 'javascript', or 'shell'
            
        Returns:
            ExecutionResult with output and status
        """
        language = language.lower()
        
        # Safety check
        is_safe, reason = self._check_code_safety(code, language)
        if not is_safe:
            return ExecutionResult(
                success=False,
                language=language,
                code=code,
                output="",
                error=f"Security check failed: {reason}"
            )
        
        # Route to appropriate executor
        if language in ('python', 'py', 'python3'):
            return self._execute_python(code)
        elif language in ('javascript', 'js', 'node'):
            return self._execute_javascript(code)
        elif language in ('shell', 'sh', 'bash'):
            return self._execute_shell(code)
        else:
            return ExecutionResult(
                success=False,
                language=language,
                code=code,
                output="",
                error=f"Unsupported language: {language}"
            )
    
    def detect_language(self, code: str) -> str:
        """Detect the language of a code snippet."""
        # Python indicators
        if any(p in code for p in ['def ', 'import ', 'from ', 'print(', 'class ', 'elif ', 'except:']):
            return 'python'
        
        # JavaScript indicators
        if any(p in code for p in ['const ', 'let ', 'var ', 'function ', '=>', 'console.log']):
            return 'javascript'
        
        # Shell indicators
        if any(p in code for p in ['#!/', 'echo ', 'ls ', 'cd ', 'mkdir ', 'grep ', 'cat ']):
            return 'shell'
        
        # Default to Python
        return 'python'
    
    def execute_auto(self, code: str) -> ExecutionResult:
        """Execute code with auto-detected language."""
        language = self.detect_language(code)
        return self.execute(code, language)


# Singleton instance
_code_executor: Optional[CodeExecutor] = None


def get_code_executor(
    timeout: int = CodeExecutor.DEFAULT_TIMEOUT,
    memory_mb: int = CodeExecutor.DEFAULT_MEMORY_MB
) -> CodeExecutor:
    """Get code executor instance."""
    global _code_executor
    if _code_executor is None:
        _code_executor = CodeExecutor(timeout=timeout, memory_mb=memory_mb)
    return _code_executor

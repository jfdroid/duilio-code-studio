"""
SOLID Validator Service
========================
Validates code against SOLID principles and suggests improvements.
"""

import re
import ast
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """Types of SOLID violations."""
    SINGLE_RESPONSIBILITY = "Single Responsibility Principle"
    OPEN_CLOSED = "Open/Closed Principle"
    LISKOV_SUBSTITUTION = "Liskov Substitution Principle"
    INTERFACE_SEGREGATION = "Interface Segregation Principle"
    DEPENDENCY_INVERSION = "Dependency Inversion Principle"


@dataclass
class Violation:
    """A SOLID principle violation."""
    type: ViolationType
    severity: str  # "high", "medium", "low"
    description: str
    location: str  # File path or class/function name
    suggestion: str
    line_number: Optional[int] = None


class SOLIDValidator:
    """
    Validates code against SOLID principles.
    
    Features:
    - Detects violations in Python, JavaScript, TypeScript, Kotlin, Java
    - Provides specific suggestions for fixes
    - Scores code quality based on SOLID adherence
    """
    
    def __init__(self):
        """Initialize the SOLID validator."""
        pass
    
    def validate_file(self, file_path: str, content: str, language: str = None) -> List[Violation]:
        """
        Validate a file against SOLID principles.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language (auto-detected if None)
            
        Returns:
            List of violations found
        """
        if language is None:
            language = self._detect_language(file_path, content)
        
        violations = []
        
        # Detect language-specific violations
        if language in ['python', 'py']:
            violations.extend(self._validate_python(content, file_path))
        elif language in ['javascript', 'js', 'typescript', 'ts', 'jsx', 'tsx']:
            violations.extend(self._validate_javascript(content, file_path))
        elif language in ['kotlin', 'kt', 'java']:
            violations.extend(self._validate_kotlin_java(content, file_path))
        
        return violations
    
    def _detect_language(self, file_path: str, content: str) -> str:
        """Detect programming language from file path and content."""
        ext = file_path.split('.')[-1].lower()
        
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'kt': 'kotlin',
            'java': 'java'
        }
        
        return lang_map.get(ext, 'unknown')
    
    def _validate_python(self, content: str, file_path: str) -> List[Violation]:
        """Validate Python code against SOLID principles."""
        violations = []
        
        try:
            tree = ast.parse(content)
            
            # Check for Single Responsibility violations
            violations.extend(self._check_single_responsibility_python(tree, file_path))
            
            # Check for Open/Closed violations
            violations.extend(self._check_open_closed_python(tree, file_path))
            
            # Check for Dependency Inversion violations
            violations.extend(self._check_dependency_inversion_python(tree, file_path))
            
        except SyntaxError:
            # If parsing fails, use regex-based checks
            violations.extend(self._check_single_responsibility_regex(content, file_path))
        
        return violations
    
    def _validate_javascript(self, content: str, file_path: str) -> List[Violation]:
        """Validate JavaScript/TypeScript code against SOLID principles."""
        violations = []
        
        # Check for Single Responsibility violations
        violations.extend(self._check_single_responsibility_js(content, file_path))
        
        # Check for Interface Segregation violations
        violations.extend(self._check_interface_segregation_js(content, file_path))
        
        return violations
    
    def _validate_kotlin_java(self, content: str, file_path: str) -> List[Violation]:
        """Validate Kotlin/Java code against SOLID principles."""
        violations = []
        
        # Check for Single Responsibility violations
        violations.extend(self._check_single_responsibility_kotlin(content, file_path))
        
        return violations
    
    def _check_single_responsibility_python(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """Check Single Responsibility Principle in Python."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods in class
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                
                # Check if class has too many responsibilities
                if len(methods) > 10:
                    violations.append(Violation(
                        type=ViolationType.SINGLE_RESPONSIBILITY,
                        severity="medium",
                        description=f"Class {node.name} has {len(methods)} methods, suggesting multiple responsibilities",
                        location=f"{file_path}:{node.name}",
                        suggestion=f"Consider splitting {node.name} into smaller, focused classes",
                        line_number=node.lineno
                    ))
                
                # Check for mixed concerns (data access + business logic + presentation)
                method_names = [m.name.lower() for m in methods]
                has_data_access = any('db' in n or 'save' in n or 'load' in n or 'fetch' in n for n in method_names)
                has_business_logic = any('process' in n or 'calculate' in n or 'validate' in n for n in method_names)
                has_presentation = any('render' in n or 'display' in n or 'format' in n for n in method_names)
                
                if sum([has_data_access, has_business_logic, has_presentation]) > 1:
                    violations.append(Violation(
                        type=ViolationType.SINGLE_RESPONSIBILITY,
                        severity="high",
                        description=f"Class {node.name} mixes data access, business logic, and/or presentation concerns",
                        location=f"{file_path}:{node.name}",
                        suggestion="Separate into distinct classes: Repository (data), Service (business logic), View/Controller (presentation)",
                        line_number=node.lineno
                    ))
        
        return violations
    
    def _check_open_closed_python(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """Check Open/Closed Principle in Python."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for if/elif chains that suggest need for polymorphism
                if_chain_length = self._count_if_chain(node)
                if if_chain_length > 3:
                    violations.append(Violation(
                        type=ViolationType.OPEN_CLOSED,
                        severity="medium",
                        description=f"Function {node.name} has long if/elif chain ({if_chain_length} branches)",
                        location=f"{file_path}:{node.name}",
                        suggestion="Consider using polymorphism or strategy pattern instead of if/elif chains",
                        line_number=node.lineno
                    ))
        
        return violations
    
    def _check_dependency_inversion_python(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """Check Dependency Inversion Principle in Python."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for direct instantiation of concrete classes
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            # Direct instantiation of concrete class
                            violations.append(Violation(
                                type=ViolationType.DEPENDENCY_INVERSION,
                                severity="low",
                                description=f"Class {node.name} directly instantiates {child.func.id}",
                                location=f"{file_path}:{node.name}",
                                suggestion="Consider using dependency injection or abstract interfaces",
                                line_number=child.lineno if hasattr(child, 'lineno') else None
                            ))
        
        return violations
    
    def _check_single_responsibility_regex(self, content: str, file_path: str) -> List[Violation]:
        """Check Single Responsibility using regex (fallback)."""
        violations = []
        
        # Count class methods
        class_pattern = r'class\s+(\w+)[^{]*\{[^}]*\}'
        matches = re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            class_content = match.group(0)
            # Count function definitions
            func_count = len(re.findall(r'\b(def|function)\s+\w+', class_content))
            
            if func_count > 10:
                violations.append(Violation(
                    type=ViolationType.SINGLE_RESPONSIBILITY,
                    severity="medium",
                    description=f"Class has {func_count} methods, suggesting multiple responsibilities",
                    location=file_path,
                    suggestion="Consider splitting into smaller, focused classes"
                ))
        
        return violations
    
    def _check_single_responsibility_js(self, content: str, file_path: str) -> List[Violation]:
        """Check Single Responsibility in JavaScript/TypeScript."""
        violations = []
        
        # Count methods in classes
        class_pattern = r'class\s+(\w+)[^{]*\{([^}]*)\}'
        matches = re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)
            
            # Count methods
            method_count = len(re.findall(r'\b\w+\s*\([^)]*\)\s*\{', class_body))
            
            if method_count > 10:
                violations.append(Violation(
                    type=ViolationType.SINGLE_RESPONSIBILITY,
                    severity="medium",
                    description=f"Class {class_name} has {method_count} methods, suggesting multiple responsibilities",
                    location=f"{file_path}:{class_name}",
                    suggestion="Consider splitting into smaller, focused classes"
                ))
        
        return violations
    
    def _check_interface_segregation_js(self, content: str, file_path: str) -> List[Violation]:
        """Check Interface Segregation in JavaScript/TypeScript."""
        violations = []
        
        # Check for large interfaces/types
        interface_pattern = r'(interface|type)\s+(\w+)[^{]*\{([^}]*)\}'
        matches = re.finditer(interface_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            interface_name = match.group(2)
            interface_body = match.group(3)
            
            # Count properties/methods
            prop_count = len(re.findall(r'\w+\s*[:?]', interface_body))
            
            if prop_count > 10:
                violations.append(Violation(
                    type=ViolationType.INTERFACE_SEGREGATION,
                    severity="medium",
                    description=f"Interface/Type {interface_name} has {prop_count} properties, suggesting it's too large",
                    location=f"{file_path}:{interface_name}",
                    suggestion="Consider splitting into smaller, more specific interfaces"
                ))
        
        return violations
    
    def _check_single_responsibility_kotlin(self, content: str, file_path: str) -> List[Violation]:
        """Check Single Responsibility in Kotlin/Java."""
        violations = []
        
        # Count methods in classes
        class_pattern = r'class\s+(\w+)[^{]*\{([^}]*)\}'
        matches = re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)
            
            # Count methods (fun in Kotlin, method in Java)
            method_count = len(re.findall(r'\b(fun|def|public|private|protected)\s+\w+\s*\(', class_body))
            
            if method_count > 10:
                violations.append(Violation(
                    type=ViolationType.SINGLE_RESPONSIBILITY,
                    severity="medium",
                    description=f"Class {class_name} has {method_count} methods, suggesting multiple responsibilities",
                    location=f"{file_path}:{class_name}",
                    suggestion="Consider splitting into smaller, focused classes"
                ))
        
        return violations
    
    def _count_if_chain(self, node: ast.FunctionDef) -> int:
        """Count length of if/elif chain in a function."""
        max_chain = 0
        current_chain = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                current_chain = 1
                # Check for elif
                while hasattr(child, 'orelse') and child.orelse:
                    if isinstance(child.orelse[0], ast.If):
                        current_chain += 1
                        child = child.orelse[0]
                    else:
                        break
                max_chain = max(max_chain, current_chain)
        
        return max_chain
    
    def get_quality_score(self, violations: List[Violation]) -> float:
        """
        Calculate quality score based on violations.
        
        Returns:
            Score from 0.0 to 1.0 (1.0 = perfect, no violations)
        """
        if not violations:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            'high': 0.3,
            'medium': 0.2,
            'low': 0.1
        }
        
        total_penalty = sum(severity_weights.get(v.severity, 0.1) for v in violations)
        
        # Normalize to 0-1 scale (max penalty = 1.0)
        score = max(0.0, 1.0 - min(1.0, total_penalty))
        
        return score
    
    def generate_report(self, violations: List[Violation], file_path: str) -> str:
        """Generate a human-readable report of violations."""
        if not violations:
            return f"✅ No SOLID violations found in {file_path}"
        
        report = [f"📋 SOLID Validation Report for {file_path}\n"]
        report.append(f"Total violations: {len(violations)}\n")
        
        # Group by type
        by_type = {}
        for v in violations:
            if v.type not in by_type:
                by_type[v.type] = []
            by_type[v.type].append(v)
        
        for violation_type, vs in by_type.items():
            report.append(f"\n{violation_type.value} ({len(vs)} violations):")
            for v in vs:
                report.append(f"  [{v.severity.upper()}] {v.description}")
                report.append(f"    Location: {v.location}")
                report.append(f"    Suggestion: {v.suggestion}")
                if v.line_number:
                    report.append(f"    Line: {v.line_number}")
                report.append("")
        
        score = self.get_quality_score(violations)
        report.append(f"\nQuality Score: {score:.2%}")
        
        return "\n".join(report)


# Singleton instance
_solid_validator: SOLIDValidator = None


def get_solid_validator() -> SOLIDValidator:
    """Get or create SOLIDValidator instance."""
    global _solid_validator
    if _solid_validator is None:
        _solid_validator = SOLIDValidator()
    return _solid_validator

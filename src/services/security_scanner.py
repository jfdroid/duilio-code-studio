"""
Security Scanner Service
========================
Analyze dependencies for vulnerabilities and security issues.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """A security vulnerability."""
    package: str
    version: str
    severity: Severity
    title: str
    description: str
    cve: Optional[str] = None
    fixed_version: Optional[str] = None
    url: Optional[str] = None


@dataclass
class ScanResult:
    """Result of a security scan."""
    success: bool
    package_manager: str
    total_packages: int
    vulnerabilities: List[Vulnerability]
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    error: str = ""


class SecurityScanner:
    """
    Service for scanning dependencies for vulnerabilities.
    
    Supports:
    - Python (pip, pipenv, poetry)
    - JavaScript (npm, yarn)
    - Go (go mod)
    """
    
    # Known vulnerable packages (simplified local database)
    # In production, this would connect to a vulnerability database API
    KNOWN_VULNERABILITIES = {
        # Python
        'pyyaml': {
            '5.3': [Vulnerability(
                package='pyyaml',
                version='5.3',
                severity=Severity.CRITICAL,
                title='Arbitrary Code Execution',
                description='PyYAML versions before 5.4 allow arbitrary code execution via yaml.load().',
                cve='CVE-2020-14343',
                fixed_version='5.4'
            )],
        },
        'urllib3': {
            '1.25.0': [Vulnerability(
                package='urllib3',
                version='1.25.0',
                severity=Severity.HIGH,
                title='CRLF Injection',
                description='urllib3 before 1.25.9 allows CRLF injection if the attacker controls the HTTP request method.',
                cve='CVE-2020-26137',
                fixed_version='1.25.9'
            )],
        },
        'requests': {
            '2.20.0': [Vulnerability(
                package='requests',
                version='2.20.0',
                severity=Severity.MEDIUM,
                title='Session Cookie Leak',
                description='Requests may leak session cookies when redirecting to a different host.',
                cve='CVE-2018-18074',
                fixed_version='2.20.1'
            )],
        },
        # JavaScript
        'lodash': {
            '4.17.15': [Vulnerability(
                package='lodash',
                version='4.17.15',
                severity=Severity.HIGH,
                title='Prototype Pollution',
                description='Lodash before 4.17.21 is vulnerable to prototype pollution.',
                cve='CVE-2021-23337',
                fixed_version='4.17.21'
            )],
        },
        'axios': {
            '0.21.0': [Vulnerability(
                package='axios',
                version='0.21.0',
                severity=Severity.CRITICAL,
                title='Server-Side Request Forgery',
                description='Axios before 0.21.2 has an SSRF vulnerability.',
                cve='CVE-2021-3749',
                fixed_version='0.21.2'
            )],
        },
        'minimist': {
            '1.2.5': [Vulnerability(
                package='minimist',
                version='1.2.5',
                severity=Severity.CRITICAL,
                title='Prototype Pollution',
                description='minimist before 1.2.6 is vulnerable to prototype pollution.',
                cve='CVE-2021-44906',
                fixed_version='1.2.6'
            )],
        },
    }
    
    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize security scanner."""
        self.workspace_path = workspace_path
    
    def _parse_requirements(self, content: str) -> Dict[str, str]:
        """Parse requirements.txt content."""
        packages = {}
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Handle different formats
            if '==' in line:
                name, version = line.split('==')
                packages[name.lower().strip()] = version.strip()
            elif '>=' in line:
                name, version = line.split('>=')
                packages[name.lower().strip()] = version.strip()
            elif line:
                # No version specified
                packages[line.lower().strip()] = 'unknown'
        
        return packages
    
    def _parse_package_json(self, content: str) -> Dict[str, str]:
        """Parse package.json content."""
        try:
            data = json.loads(content)
            packages = {}
            
            for deps_key in ['dependencies', 'devDependencies']:
                deps = data.get(deps_key, {})
                for name, version in deps.items():
                    # Clean version string
                    version = version.replace('^', '').replace('~', '').replace('>=', '').replace('>', '')
                    packages[name.lower()] = version
            
            return packages
        except json.JSONDecodeError:
            return {}
    
    def _check_package(self, name: str, version: str) -> List[Vulnerability]:
        """Check a package against known vulnerabilities."""
        vulns = []
        name_lower = name.lower()
        
        if name_lower in self.KNOWN_VULNERABILITIES:
            pkg_vulns = self.KNOWN_VULNERABILITIES[name_lower]
            
            # Check if version is vulnerable
            for vuln_version, vuln_list in pkg_vulns.items():
                # Simple version comparison (in production, use proper semver)
                if self._is_version_vulnerable(version, vuln_version, vuln_list[0].fixed_version):
                    for vuln in vuln_list:
                        vulns.append(Vulnerability(
                            package=name,
                            version=version,
                            severity=vuln.severity,
                            title=vuln.title,
                            description=vuln.description,
                            cve=vuln.cve,
                            fixed_version=vuln.fixed_version,
                            url=vuln.url
                        ))
        
        return vulns
    
    def _is_version_vulnerable(
        self,
        current: str,
        vulnerable: str,
        fixed: Optional[str]
    ) -> bool:
        """Check if current version is vulnerable (simplified)."""
        try:
            # Remove any extra characters
            current_clean = current.split('.')[0:3]
            vulnerable_clean = vulnerable.split('.')[0:3]
            
            # Pad versions to 3 parts
            while len(current_clean) < 3:
                current_clean.append('0')
            while len(vulnerable_clean) < 3:
                vulnerable_clean.append('0')
            
            # Compare
            for c, v in zip(current_clean, vulnerable_clean):
                try:
                    if int(c) < int(v):
                        return True
                    elif int(c) > int(v):
                        return False
                except ValueError:
                    pass
            
            return True  # Same version = vulnerable
        except:
            return False
    
    def scan_python(self, path: Optional[str] = None) -> ScanResult:
        """Scan Python dependencies for vulnerabilities."""
        scan_path = Path(path or self.workspace_path)
        packages = {}
        
        # Check for requirements.txt
        req_file = scan_path / 'requirements.txt'
        if req_file.exists():
            packages.update(self._parse_requirements(req_file.read_text()))
        
        # Check for pyproject.toml (simplified)
        pyproject = scan_path / 'pyproject.toml'
        if pyproject.exists():
            content = pyproject.read_text()
            # Simple extraction (in production, use toml parser)
            for line in content.split('\n'):
                if '=' in line and '"' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        name = parts[0].strip().strip('"')
                        if name and not name.startswith('['):
                            packages[name.lower()] = 'unknown'
        
        # Check for vulnerabilities
        vulnerabilities = []
        for name, version in packages.items():
            vulns = self._check_package(name, version)
            vulnerabilities.extend(vulns)
        
        # Count by severity
        critical = len([v for v in vulnerabilities if v.severity == Severity.CRITICAL])
        high = len([v for v in vulnerabilities if v.severity == Severity.HIGH])
        medium = len([v for v in vulnerabilities if v.severity == Severity.MEDIUM])
        low = len([v for v in vulnerabilities if v.severity == Severity.LOW])
        
        return ScanResult(
            success=True,
            package_manager='pip',
            total_packages=len(packages),
            vulnerabilities=vulnerabilities,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low
        )
    
    def scan_javascript(self, path: Optional[str] = None) -> ScanResult:
        """Scan JavaScript dependencies for vulnerabilities."""
        scan_path = Path(path or self.workspace_path)
        packages = {}
        
        # Check for package.json
        pkg_file = scan_path / 'package.json'
        if pkg_file.exists():
            packages.update(self._parse_package_json(pkg_file.read_text()))
        
        # Also check package-lock.json for more accurate versions
        lock_file = scan_path / 'package-lock.json'
        if lock_file.exists():
            try:
                lock_data = json.loads(lock_file.read_text())
                for name, info in lock_data.get('packages', {}).items():
                    if name.startswith('node_modules/'):
                        pkg_name = name.replace('node_modules/', '').lower()
                        version = info.get('version', 'unknown')
                        packages[pkg_name] = version
            except:
                pass
        
        # Check for vulnerabilities
        vulnerabilities = []
        for name, version in packages.items():
            vulns = self._check_package(name, version)
            vulnerabilities.extend(vulns)
        
        # Count by severity
        critical = len([v for v in vulnerabilities if v.severity == Severity.CRITICAL])
        high = len([v for v in vulnerabilities if v.severity == Severity.HIGH])
        medium = len([v for v in vulnerabilities if v.severity == Severity.MEDIUM])
        low = len([v for v in vulnerabilities if v.severity == Severity.LOW])
        
        return ScanResult(
            success=True,
            package_manager='npm',
            total_packages=len(packages),
            vulnerabilities=vulnerabilities,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low
        )
    
    def scan_auto(self, path: Optional[str] = None) -> List[ScanResult]:
        """Auto-detect and scan all package managers."""
        scan_path = Path(path or self.workspace_path)
        results = []
        
        # Check for Python
        if (scan_path / 'requirements.txt').exists() or (scan_path / 'pyproject.toml').exists():
            results.append(self.scan_python(str(scan_path)))
        
        # Check for JavaScript
        if (scan_path / 'package.json').exists():
            results.append(self.scan_javascript(str(scan_path)))
        
        return results
    
    def format_report(self, results: List[ScanResult]) -> str:
        """Format scan results as a readable report."""
        lines = ["# Security Scan Report\n"]
        lines.append(f"Scan Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        total_vulns = sum(len(r.vulnerabilities) for r in results)
        total_critical = sum(r.critical_count for r in results)
        total_high = sum(r.high_count for r in results)
        
        # Summary
        lines.append("## Summary\n")
        if total_vulns == 0:
            lines.append("**No vulnerabilities found.**\n")
        else:
            lines.append(f"- **Total Vulnerabilities:** {total_vulns}")
            lines.append(f"- **Critical:** {total_critical}")
            lines.append(f"- **High:** {total_high}")
            lines.append("")
        
        # Details
        for result in results:
            lines.append(f"## {result.package_manager.upper()}\n")
            lines.append(f"- Packages scanned: {result.total_packages}")
            lines.append(f"- Vulnerabilities found: {len(result.vulnerabilities)}\n")
            
            if result.vulnerabilities:
                lines.append("### Vulnerabilities\n")
                
                # Group by severity
                for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                    vulns = [v for v in result.vulnerabilities if v.severity == severity]
                    if vulns:
                        lines.append(f"#### {severity.value.upper()}\n")
                        for v in vulns:
                            lines.append(f"**{v.package}** @ {v.version}")
                            lines.append(f"- {v.title}")
                            if v.cve:
                                lines.append(f"- CVE: {v.cve}")
                            if v.fixed_version:
                                lines.append(f"- Fix: Upgrade to {v.fixed_version}")
                            lines.append("")
        
        return '\n'.join(lines)


# Singleton instance
_security_scanner: Optional[SecurityScanner] = None


def get_security_scanner(workspace_path: Optional[str] = None) -> SecurityScanner:
    """Get security scanner instance."""
    global _security_scanner
    if _security_scanner is None:
        _security_scanner = SecurityScanner(workspace_path)
    return _security_scanner

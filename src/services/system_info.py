"""
System Information Service
==========================
Collects local machine information for Agent mode context.
"""

import platform
import os
import subprocess
import sys
from typing import Dict, Any, Optional
from pathlib import Path


def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns:
        Dictionary with system information including:
        - OS, platform, architecture
        - CPU information
        - Memory information
        - User and home directory
        - Python version
        - Hostname
    """
    info = {
        "os": {
            "system": platform.system(),
            "platform": platform.platform(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "user": {
            "name": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
            "home": os.path.expanduser("~"),
        },
        "hostname": platform.node(),
    }
    
    # Get memory information (platform-specific)
    try:
        if platform.system() == "Darwin":  # macOS
            # Get total memory
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                mem_bytes = int(result.stdout.strip())
                info["memory"] = {
                    "total_gb": round(mem_bytes / (1024**3), 2),
                    "total_bytes": mem_bytes
                }
            
            # Get CPU info
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                info["cpu"] = {
                    "brand": result.stdout.strip()
                }
                
        elif platform.system() == "Linux":
            # Get memory from /proc/meminfo
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_kb = int(line.split()[1])
                            info["memory"] = {
                                "total_gb": round(mem_kb / (1024**2), 2),
                                "total_bytes": mem_kb * 1024
                            }
                            break
            except:
                pass
                
        elif platform.system() == "Windows":
            # Windows memory info
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                memStatus = MEMORYSTATUSEX()
                memStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memStatus))
                info["memory"] = {
                    "total_gb": round(memStatus.ullTotalPhys / (1024**3), 2),
                    "total_bytes": memStatus.ullTotalPhys
                }
            except:
                pass
    except Exception:
        pass  # Ignore errors in system info collection
    
    return info


def format_system_info_for_prompt(system_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Format system information as a readable string for AI prompts.
    
    Args:
        system_info: Optional system info dict. If None, will collect it.
    
    Returns:
        Formatted string with system information.
    """
    if system_info is None:
        system_info = get_system_info()
    
    lines = ["=== SYSTEM INFORMATION ==="]
    
    # OS Info
    os_info = system_info.get("os", {})
    lines.append(f"Operating System: {os_info.get('system', 'Unknown')} {os_info.get('release', '')}")
    lines.append(f"Platform: {os_info.get('platform', 'Unknown')}")
    lines.append(f"Architecture: {os_info.get('machine', 'Unknown')}")
    
    # CPU
    if "cpu" in system_info and "brand" in system_info["cpu"]:
        lines.append(f"CPU: {system_info['cpu']['brand']}")
    elif "processor" in os_info:
        lines.append(f"Processor: {os_info['processor']}")
    
    # Memory
    if "memory" in system_info:
        mem = system_info["memory"]
        if "total_gb" in mem:
            lines.append(f"Total Memory: {mem['total_gb']} GB")
    
    # User
    user_info = system_info.get("user", {})
    lines.append(f"User: {user_info.get('name', 'Unknown')}")
    lines.append(f"Home Directory: {user_info.get('home', 'Unknown')}")
    
    # Hostname
    if "hostname" in system_info:
        lines.append(f"Hostname: {system_info['hostname']}")
    
    # Python
    python_info = system_info.get("python", {})
    lines.append(f"Python Version: {python_info.get('version', 'Unknown')}")
    
    lines.append("=== END SYSTEM INFORMATION ===")
    
    return "\n".join(lines)


def get_system_info_service():
    """Get singleton system info service."""
    return SystemInfoService()


class SystemInfoService:
    """Service for system information collection."""
    
    def __init__(self):
        self._cached_info: Optional[Dict[str, Any]] = None
    
    def get_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get system information (cached)."""
        if self._cached_info is None or force_refresh:
            self._cached_info = get_system_info()
        return self._cached_info
    
    def get_formatted_prompt(self, force_refresh: bool = False) -> str:
        """Get formatted system info for prompts."""
        info = self.get_info(force_refresh)
        return format_system_info_for_prompt(info)

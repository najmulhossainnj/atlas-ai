"""Resource restrictions for sandboxed execution."""

from __future__ import annotations

import resource
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResourceLimits:
    """Resource limits for code execution."""
    max_cpu_time_seconds: float = 10.0
    max_wall_time_seconds: float = 30.0
    max_memory_bytes: int = 256 * 1024 * 1024  # 256 MB
    max_open_files: int = 100
    max_processes: int = 10
    max_output_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_stack_bytes: int = 8 * 1024 * 1024  # 8 MB

    def apply(self) -> None:
        """Apply resource limits to the current process."""
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (int(self.max_cpu_time_seconds), int(self.max_cpu_time_seconds)))
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_bytes, self.max_memory_bytes))
            resource.setrlimit(resource.RLIMIT_NOFILE, (self.max_open_files, self.max_open_files))
            resource.setrlimit(resource.RLIMIT_NPROC, (self.max_processes, self.max_processes))
            resource.setrlimit(resource.RLIMIT_FSIZE, (self.max_output_bytes, self.max_output_bytes))
            resource.setrlimit(resource.RLIMIT_STACK, (self.max_stack_bytes, self.max_stack_bytes))
        except (ValueError, resource.error) as e:
            pass


class SecurityPolicy:
    """Security policy for code execution."""

    ALLOWED_MODULES = {
        "math", "random", "datetime", "json", "re", "collections",
        "itertools", "functools", "operator", "string", "textwrap",
        "decimal", "fractions", "complex", "typing",
    }

    BLOCKED_MODULES = {
        "os", "sys", "subprocess", "socket", "requests", "urllib",
        "http", "ftplib", "telnetlib", "pickle", "shelve",
        "builtins", "importlib", "imp", "exec", "eval", "compile",
    }

    def __init__(self):
        self.allowed_modules = set(self.ALLOWED_MODULES)
        self.blocked_modules = set(self.BLOCKED_MODULES)
        self.allow_network = False
        self.allow_filesystem = False
        self.allow_subprocess = False

    def is_module_allowed(self, module_name: str) -> bool:
        """Check if a module is allowed."""
        if module_name in self.blocked_modules:
            return False
        if module_name in self.allowed_modules:
            return True
        for allowed in self.allowed_modules:
            if module_name.startswith(f"{allowed}."):
                return True
        return False

    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate code for security issues."""
        issues = []
        
        import_patterns = [
            "import os", "from os ", "import sys", "from sys ",
            "import subprocess", "from subprocess ",
            "import socket", "from socket ",
            "import requests", "from requests ",
            "import urllib", "from urllib ",
            "open(", "exec(", "eval(", "compile(",
            "__import__", "getattr(", "setattr(",
        ]
        
        for pattern in import_patterns:
            if pattern in code:
                issues.append(f"Potentially dangerous pattern: {pattern}")
        
        return len(issues) == 0, issues
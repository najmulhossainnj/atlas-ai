"""Coding module for repository understanding and code analysis."""

from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Optional
import ast


@dataclass
class CodeAnalysis:
    """Results of code analysis."""
    file_path: str
    functions: list[dict[str, Any]] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    complexity: int = 0
    lines_of_code: int = 0


@dataclass
class DependencyGraph:
    """Dependency graph for a codebase."""
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)


class CodingModule:
    """Module for coding-related tasks."""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self._index: dict[str, CodeAnalysis] = {}

    async def analyze_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a single file."""
        full_path = os.path.join(self.workspace_path, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(full_path, "r") as f:
            content = f.read()

        analysis = CodeAnalysis(file_path=file_path)
        analysis.lines_of_code = len(content.splitlines())

        if file_path.endswith(".py"):
            try:
                tree = ast.parse(content)
                analysis.functions = self._extract_functions(tree)
                analysis.classes = self._extract_classes(tree)
                analysis.imports = self._extract_imports(tree)
                analysis.complexity = self._calculate_complexity(tree)
            except SyntaxError:
                pass

        self._index[file_path] = analysis
        return analysis

    def _extract_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract function definitions."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node),
                })
        return functions

    def _extract_classes(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract class definitions."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    "docstring": ast.get_docstring(node),
                })
        return classes

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extract import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    async def build_dependency_graph(self) -> DependencyGraph:
        """Build a dependency graph for the codebase."""
        graph = DependencyGraph()

        for file_path in self._index:
            analysis = self._index[file_path]
            graph.nodes[file_path] = {
                "functions": len(analysis.functions),
                "classes": len(analysis.classes),
                "complexity": analysis.complexity,
            }

            for imp in analysis.imports:
                if imp in self._index:
                    graph.edges.append((file_path, imp))

        return graph

    async def search_code(self, query: str) -> list[dict[str, Any]]:
        """Search for code patterns."""
        results = []
        
        for file_path, analysis in self._index.items():
            for func in analysis.functions:
                if query.lower() in func["name"].lower():
                    results.append({
                        "type": "function",
                        "file": file_path,
                        "name": func["name"],
                        "line": func["line"],
                    })

            for cls in analysis.classes:
                if query.lower() in cls["name"].lower():
                    results.append({
                        "type": "class",
                        "file": file_path,
                        "name": cls["name"],
                        "line": cls["line"],
                    })

        return results

    async def get_file_summary(self, file_path: str) -> str:
        """Get a summary of a file."""
        analysis = self._index.get(file_path)
        if not analysis:
            analysis = await self.analyze_file(file_path)

        summary_parts = [
            f"File: {file_path}",
            f"Lines of code: {analysis.lines_of_code}",
            f"Functions: {len(analysis.functions)}",
            f"Classes: {len(analysis.classes)}",
            f"Complexity: {analysis.complexity}",
        ]

        if analysis.classes:
            summary_parts.append("\nClasses:")
            for cls in analysis.classes[:5]:
                summary_parts.append(f"  - {cls['name']} (line {cls['line']})")

        if analysis.functions:
            summary_parts.append("\nFunctions:")
            for func in analysis.functions[:10]:
                summary_parts.append(f"  - {func['name']}() (line {func['line']})")

        return "\n".join(summary_parts)

    def get_stats(self) -> dict[str, Any]:
        """Get coding module statistics."""
        total_files = len(self._index)
        total_functions = sum(len(a.functions) for a in self._index.values())
        total_classes = sum(len(a.classes) for a in self._index.values())
        avg_complexity = (
            sum(a.complexity for a in self._index.values()) / total_files
            if total_files > 0 else 0
        )

        return {
            "files_analyzed": total_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "average_complexity": round(avg_complexity, 2),
        }

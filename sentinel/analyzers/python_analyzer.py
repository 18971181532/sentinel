"""Python AST-based code analyzer."""
import ast
import re
from sentinel.models import FileStats


def analyze_python(content: str, path: str) -> FileStats:
    """Analyze a Python file using AST."""
    stats = FileStats(path=path, language="python")
    content = content.rstrip("\n")
    lines = content.split("\n")
    stats.lines = len(lines)

    # Count blank, comment, code lines
    in_docstring = False
    docstring_quote = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            stats.blank_lines += 1
            continue
        if stripped.startswith("#"):
            stats.comment_lines += 1
            continue
        # Check for docstrings
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote = stripped[:3]
                if stripped.count(quote) >= 2 and len(stripped) > 3:
                    # Single-line docstring
                    stats.comment_lines += 1
                else:
                    in_docstring = True
                    docstring_quote = quote
                    stats.comment_lines += 1
                continue
        else:
            stats.comment_lines += 1
            if docstring_quote in stripped:
                in_docstring = False
            continue
        stats.code_lines += 1

    # AST analysis
    try:
        tree = ast.parse(content)
        _analyze_ast(tree, stats)
    except SyntaxError:
        pass

    return stats


def _analyze_ast(tree: ast.AST, stats: FileStats):
    """Extract function/class counts and complexity from AST."""
    func_count = 0
    class_count = 0
    complexities = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_count += 1
        elif isinstance(node, ast.ClassDef):
            class_count += 1

    # Compute cyclomatic complexity for each function
    from sentinel.rules.complexity import compute_cyclomatic_complexity
    comp = compute_cyclomatic_complexity(tree)
    for name, info in comp.items():
        complexities.append(info["complexity"])

    stats.functions = func_count
    stats.classes = class_count
    if complexities:
        stats.max_complexity = max(complexities)
        stats.avg_complexity = sum(complexities) / len(complexities)


def get_function_locations(content: str) -> list:
    """Get list of (name, start_line, end_line) for all functions."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    locations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            locations.append((node.name, node.lineno, end))
    return locations

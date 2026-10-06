"""Complexity analysis rules."""
import re
import ast
from sentinel.models import Severity, Category, FileStats
from sentinel.rules.base import Rule, RuleRegistry


def compute_cyclomatic_complexity(tree) -> dict:
    """Compute cyclomatic complexity for each function in an AST."""
    results = {}

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_func = None
            self.complexity = 0

        def visit_FunctionDef(self, node):
            prev = self.current_func
            prev_c = self.complexity
            self.current_func = node.name
            self.complexity = 1  # base complexity
            self.generic_visit(node)
            results[node.name] = {
                "complexity": self.complexity,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
            }
            self.current_func = prev
            self.complexity = prev_c

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

        def visit_If(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_For(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_AsyncFor(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_While(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_ExceptHandler(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_With(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_BoolOp(self, node):
            # Each 'and'/'or' adds a branch
            self.complexity += len(node.values) - 1
            self.generic_visit(node)

        def visit_IfExp(self, node):
            self.complexity += 1
            self.generic_visit(node)

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return results


@RuleRegistry.register
class CyclomaticComplexityRule(Rule):
    rule_id = "CPX001"
    rule_name = "High Cyclomatic Complexity"
    category = Category.COMPLEXITY
    severity = Severity.MEDIUM
    description = "Detects functions with high cyclomatic complexity (> 10)."
    languages = ["python"]

    THRESHOLD = 10

    def check(self, content, file_path, stats):
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        complexities = compute_cyclomatic_complexity(tree)
        for func_name, info in complexities.items():
            if info["complexity"] > self.THRESHOLD:
                sev = Severity.HIGH if info["complexity"] > 20 else Severity.MEDIUM
                issues.append(self.make_issue(
                    f"Function '{func_name}' has cyclomatic complexity of {info['complexity']} (threshold: {self.THRESHOLD})",
                    file_path, line=info["lineno"],
                    snippet=f"def {func_name}(...):  # complexity={info['complexity']}",
                    suggestion="Break the function into smaller, more focused functions.",
                    severity=sev, confidence=0.95,
                ))
        return issues


@RuleRegistry.register
class FunctionLengthRule(Rule):
    rule_id = "CPX002"
    rule_name = "Long Function"
    category = Category.COMPLEXITY
    severity = Severity.LOW
    description = "Detects functions that are too long (> 50 lines)."
    languages = ["python"]

    THRESHOLD = 50

    def check(self, content, file_path, stats):
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                length = end - node.lineno + 1
                if length > self.THRESHOLD:
                    sev = Severity.MEDIUM if length > 100 else Severity.LOW
                    issues.append(self.make_issue(
                        f"Function '{node.name}' is {length} lines long (threshold: {self.THRESHOLD})",
                        file_path, line=node.lineno,
                        snippet=f"def {node.name}(...):  # {length} lines",
                        suggestion="Extract helper functions to reduce length.",
                        severity=sev, confidence=0.9,
                    ))
        return issues


@RuleRegistry.register
class NestingDepthRule(Rule):
    rule_id = "CPX003"
    rule_name = "Deep Nesting"
    category = Category.COMPLEXITY
    severity = Severity.MEDIUM
    description = "Detects deeply nested code blocks (> 4 levels)."
    languages = ["python"]

    THRESHOLD = 4

    def check(self, content, file_path, stats):
        issues = []
        max_depth = 0
        max_line = 0
        current_depth = 0

        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Count indentation level (4 spaces per level)
            indent = len(line) - len(line.lstrip())
            depth = indent // 4
            if depth > max_depth:
                max_depth = depth
                max_line = i

        if max_depth > self.THRESHOLD:
            lines = content.split("\n")
            issues.append(self.make_issue(
                f"Code nested {max_depth} levels deep (threshold: {self.THRESHOLD})",
                file_path, line=max_line,
                snippet=lines[max_line-1].strip()[:120] if max_line <= len(lines) else "",
                suggestion="Use early returns, guard clauses, or extract methods to reduce nesting.",
                confidence=0.8,
            ))
        return issues


@RuleRegistry.register
class TooManyArgumentsRule(Rule):
    rule_id = "CPX004"
    rule_name = "Too Many Arguments"
    category = Category.COMPLEXITY
    severity = Severity.LOW
    description = "Detects functions with too many parameters (> 5)."
    languages = ["python"]

    THRESHOLD = 5

    def check(self, content, file_path, stats):
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                count = len(args.args) + len(args.posonlyargs if hasattr(args, 'posonlyargs') else [])
                if count > self.THRESHOLD:
                    issues.append(self.make_issue(
                        f"Function '{node.name}' has {count} parameters (threshold: {self.THRESHOLD})",
                        file_path, line=node.lineno,
                        snippet=f"def {node.name}(...{count} args...):",
                        suggestion="Group related parameters into a data class or dictionary.",
                        confidence=0.85,
                    ))
        return issues


@RuleRegistry.register
class FileTooLargeRule(Rule):
    rule_id = "CPX005"
    rule_name = "File Too Large"
    category = Category.COMPLEXITY
    severity = Severity.LOW
    description = "Detects files that exceed 500 lines."

    THRESHOLD = 500

    def check(self, content, file_path, stats):
        issues = []
        line_count = len(content.split("\n"))
        if line_count > self.THRESHOLD:
            sev = Severity.MEDIUM if line_count > 1000 else Severity.LOW
            issues.append(self.make_issue(
                f"File has {line_count} lines (threshold: {self.THRESHOLD})",
                file_path, line=1,
                snippet=f"# {line_count} lines total",
                suggestion="Consider splitting this file into smaller modules.",
                severity=sev, confidence=0.9,
            ))
        return issues

"""Code style rules."""
import re
from sentinel.models import Severity, Category, FileStats
from sentinel.rules.base import Rule, RuleRegistry


@RuleRegistry.register
class LineLengthRule(Rule):
    rule_id = "STY001"
    rule_name = "Line Too Long"
    category = Category.STYLE
    severity = Severity.INFO
    description = "Detects lines exceeding 120 characters."

    THRESHOLD = 120

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            if len(line) > self.THRESHOLD:
                issues.append(self.make_issue(
                    f"Line is {len(line)} characters (threshold: {self.THRESHOLD})",
                    file_path, line=i, snippet=line[:120] + "...",
                    suggestion="Break long lines for readability.",
                    confidence=1.0,
                ))
        return issues


@RuleRegistry.register
class TrailingWhitespaceRule(Rule):
    rule_id = "STY002"
    rule_name = "Trailing Whitespace"
    category = Category.STYLE
    severity = Severity.INFO
    description = "Detects trailing whitespace at end of lines."

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            if line != line.rstrip() and line.strip():
                issues.append(self.make_issue(
                    "Trailing whitespace",
                    file_path, line=i, snippet=line.rstrip()[:120],
                    suggestion="Remove trailing whitespace.",
                    confidence=1.0,
                ))
        return issues


@RuleRegistry.register
class MixedIndentationRule(Rule):
    rule_id = "STY003"
    rule_name = "Mixed Indentation"
    category = Category.STYLE
    severity = Severity.LOW
    description = "Detects mixed tabs and spaces for indentation."

    def check(self, content, file_path, stats):
        issues = []
        has_tabs = False
        has_spaces = False
        tab_lines = []
        for i, line in enumerate(content.split("\n"), 1):
            if line.startswith("\t"):
                has_tabs = True
                tab_lines.append(i)
            elif line.startswith("    "):
                has_spaces = True
        if has_tabs and has_spaces:
            issues.append(self.make_issue(
                "Mixed tabs and spaces for indentation",
                file_path, line=tab_lines[0] if tab_lines else 1,
                snippet="Mixed indentation detected",
                suggestion="Use spaces consistently (PEP 8 recommends 4 spaces).",
                confidence=0.9,
            ))
        return issues


@RuleRegistry.register
class MissingDocstringRule(Rule):
    rule_id = "STY004"
    rule_name = "Missing Docstring"
    category = Category.STYLE
    severity = Severity.INFO
    description = "Detects public functions/classes without docstrings."
    languages = ["python"]

    def check(self, content, file_path, stats):
        import ast
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                if name.startswith("_") and not name.startswith("__"):
                    continue  # skip private
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append(self.make_issue(
                        f"{'Class' if isinstance(node, ast.ClassDef) else 'Function'} '{name}' has no docstring",
                        file_path, line=node.lineno,
                        snippet=f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {name}(...):",
                        suggestion="Add a docstring describing purpose, parameters, and return value.",
                        confidence=0.7,
                    ))
        return issues


@RuleRegistry.register
class VariableNamingRule(Rule):
    rule_id = "STY005"
    rule_name = "Non-snake_case Variable"
    category = Category.STYLE
    severity = Severity.INFO
    description = "Detects variables/functions using camelCase instead of snake_case."
    languages = ["python"]

    def check(self, content, file_path, stats):
        import ast
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        camel = re.compile(r'^[a-z]+[A-Z][a-zA-Z0-9]*$')
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if camel.match(node.name) and not node.name.startswith("test"):
                    snake_name = re.sub(r'([A-Z])', r'_\1', node.name).lower()
                    issues.append(self.make_issue(
                        f"Function name '{node.name}' should be snake_case",
                        file_path, line=node.lineno,
                        snippet=f"def {node.name}(...):",
                        suggestion=f"Rename to '{snake_name}'",
                        confidence=0.6,
                    ))
        return issues

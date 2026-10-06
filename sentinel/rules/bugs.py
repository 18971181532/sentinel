"""Common bug pattern detection rules."""
import re
import ast
from sentinel.models import Severity, Category, FileStats
from sentinel.rules.base import Rule, RuleRegistry


@RuleRegistry.register
class BareExceptRule(Rule):
    rule_id = "BUG001"
    rule_name = "Bare Except"
    category = Category.BUG
    severity = Severity.MEDIUM
    description = "Detects bare except clauses that swallow all exceptions."
    languages = ["python"]

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if re.match(r'except\s*:', stripped):
                issues.append(self.make_issue(
                    "Bare except clause catches all exceptions including KeyboardInterrupt",
                    file_path, line=i, snippet=stripped[:120],
                    suggestion="Specify exception types: except (ValueError, KeyError) as e:",
                    confidence=0.95,
                ))
        return issues


@RuleRegistry.register
class MutableDefaultArgRule(Rule):
    rule_id = "BUG002"
    rule_name = "Mutable Default Argument"
    category = Category.BUG
    severity = Severity.HIGH
    description = "Detects mutable default arguments in function definitions."
    languages = ["python"]

    def check(self, content, file_path, stats):
        issues = []
        pattern = re.compile(r'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\)|dict\(\)|list\(\))')
        for i, line in enumerate(content.split("\n"), 1):
            if pattern.search(line):
                issues.append(self.make_issue(
                    "Mutable default argument — shared across all calls",
                    file_path, line=i, snippet=line.strip()[:120],
                    suggestion="Use None as default and initialize inside: if x is None: x = []",
                    confidence=0.9,
                ))
        return issues


@RuleRegistry.register
class ComparisonWithNoneRule(Rule):
    rule_id = "BUG003"
    rule_name = "Comparison with None"
    category = Category.BUG
    severity = Severity.LOW
    description = "Detects use of == or != instead of is/is not for None comparisons."
    languages = ["python"]

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(r'==\s*None|!=\s*None', line):
                issues.append(self.make_issue(
                    "Use 'is None' or 'is not None' instead of ==/!=",
                    file_path, line=i, snippet=line.strip()[:120],
                    suggestion="Use identity comparison: if x is None:",
                    confidence=0.85,
                ))
        return issues


@RuleRegistry.register
class UnusedImportRule(Rule):
    rule_id = "BUG004"
    rule_name = "Unused Import"
    category = Category.MAINTAINABILITY
    severity = Severity.INFO
    description = "Detects potentially unused imports (heuristic)."
    languages = ["python"]

    def check(self, content, file_path, stats):
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        imported = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        imported[name] = node.lineno

        # Check usage (simple heuristic: name appears as attribute or standalone)
        lines = content.split("\n")
        for name, lineno in imported.items():
            used = False
            for j, line in enumerate(lines):
                if j + 1 == lineno:
                    continue
                # Check if name is used (as word boundary, not in import)
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    if not line.strip().startswith("import") and not line.strip().startswith("from"):
                        used = True
                        break
            if not used:
                issues.append(self.make_issue(
                    f"Potentially unused import: {name}",
                    file_path, line=lineno, snippet=lines[lineno-1].strip()[:120],
                    suggestion="Remove unused imports to keep code clean.",
                    confidence=0.6,
                ))
        return issues


@RuleRegistry.register
class PrintStatementRule(Rule):
    rule_id = "BUG005"
    rule_name = "Print in Production"
    category = Category.MAINTAINABILITY
    severity = Severity.INFO
    description = "Detects print() statements that should use logging."
    languages = ["python"]

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if re.match(r'print\s*\(', stripped) and not stripped.startswith("#"):
                issues.append(self.make_issue(
                    "print() statement — consider using logging for production code",
                    file_path, line=i, snippet=stripped[:120],
                    suggestion="Use logging.info/debug/warning instead of print().",
                    confidence=0.5,
                ))
        return issues


@RuleRegistry.register
class TodoCommentRule(Rule):
    rule_id = "BUG006"
    rule_name = "TODO/FIXME Comments"
    category = Category.MAINTAINABILITY
    severity = Severity.INFO
    description = "Detects TODO, FIXME, HACK, and XXX comments."

    def check(self, content, file_path, stats):
        issues = []
        pattern = re.compile(r'(?i)(TODO|FIXME|HACK|XXX|BUG)\s*[:\s]')
        for i, line in enumerate(content.split("\n"), 1):
            if pattern.search(line):
                issues.append(self.make_issue(
                    f"Unresolved marker in comment: {line.strip()[:80]}",
                    file_path, line=i, snippet=line.strip()[:120],
                    suggestion="Resolve or create an issue ticket for this marker.",
                    confidence=1.0,
                ))
        return issues


@RuleRegistry.register
class BroadExceptionCatchRule(Rule):
    rule_id = "BUG007"
    rule_name = "Broad Exception Catch"
    category = Category.BUG
    severity = Severity.LOW
    description = "Detects catching Exception (too broad)."
    languages = ["python"]

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            if re.match(r'except\s+Exception\s*:', line.strip()):
                issues.append(self.make_issue(
                    "Catching Exception is too broad — may hide bugs",
                    file_path, line=i, snippet=line.strip()[:120],
                    suggestion="Catch specific exception types instead of Exception.",
                    confidence=0.7,
                ))
        return issues

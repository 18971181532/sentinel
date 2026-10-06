"""Main scanner orchestrator."""
import os
import time
from typing import Optional
from sentinel.models import ScanResult, FileStats, Severity, Category
from sentinel.rules import RuleRegistry
from sentinel.analyzers import analyze_python, analyze_generic, detect_language
from sentinel.rules.duplicates import find_duplicate_blocks


# Default file extensions to scan
SCAN_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".h", ".cpp", ".cc",
    ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".sh", ".bash", ".sql", ".html", ".htm", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".cfg", ".r", ".lua",
    ".pl", ".dart", ".md",
}

# Directories to skip
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "build", "dist", ".idea", ".vscode", ".tox", ".mypy_cache",
    ".pytest_cache", "coverage", "htmlcov", ".next", ".nuxt",
    "target", "bin", "obj", "packages", ".dart_tool",
}

# Max file size to scan (1 MB)
MAX_FILE_SIZE = 1024 * 1024


class Scanner:
    """Main code scanner that orchestrates analysis and rule checking."""

    def __init__(self, target_path: str,
                 extensions: Optional[set] = None,
                 skip_dirs: Optional[set] = None,
                 max_size: int = MAX_FILE_SIZE,
                 exclude_patterns: Optional[list] = None):
        self.target_path = os.path.abspath(target_path)
        self.extensions = extensions or SCAN_EXTENSIONS
        self.skip_dirs = skip_dirs or SKIP_DIRS
        self.max_size = max_size
        self.exclude_patterns = exclude_patterns or []
        self._rules = RuleRegistry.get_all()

    def scan(self) -> ScanResult:
        """Run full scan and return results."""
        if not os.path.exists(self.target_path):
            raise FileNotFoundError(f"Path not found: {self.target_path}")
        start = time.time()
        result = ScanResult(target_path=self.target_path)
        files_content = {}

        # Collect and analyze files
        for file_path in self._iter_files():
            try:
                content = self._read_file(file_path)
            except (OSError, UnicodeDecodeError):
                continue

            rel_path = os.path.relpath(file_path, self.target_path).replace("\\", "/")
            files_content[rel_path] = content

            # Analyze file
            language = detect_language(file_path)
            if language == "python":
                stats = analyze_python(content, rel_path)
            else:
                stats = analyze_generic(content, rel_path, language)

            # Run rules
            file_issues = []
            for rule in self._rules:
                if not rule.applies_to(language):
                    continue
                try:
                    issues = rule.check(content, rel_path, stats)
                    file_issues.extend(issues)
                except Exception:
                    continue  # Don't let one rule crash the scan

            stats.issues = file_issues
            result.file_stats[rel_path] = stats
            result.all_issues.extend(file_issues)
            result.files_scanned += 1

            if file_issues:
                result.files_with_issues += 1

            # Track languages
            result.languages[language] = result.languages.get(language, 0) + 1

        # Duplicate code detection (cross-file)
        if len(files_content) >= 2:
            result.duplicates = find_duplicate_blocks(files_content, min_lines=5)

        # Aggregate
        result.total_issues = len(result.all_issues)
        result.issues_by_severity = self._count_by_severity(result.all_issues)
        result.issues_by_category = self._count_by_category(result.all_issues)
        result.issues_by_rule = self._count_by_rule(result.all_issues)

        result.scan_time = time.time() - start
        return result

    def _iter_files(self):
        """Iterate over scannable files."""
        if os.path.isfile(self.target_path):
            if self._should_scan(self.target_path):
                yield self.target_path
            return

        for root, dirs, filenames in os.walk(self.target_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs
                       and not d.startswith(".")]
            for filename in filenames:
                full_path = os.path.join(root, filename)
                if self._should_scan(full_path):
                    yield full_path

    def _should_scan(self, file_path: str) -> bool:
        """Check if a file should be scanned."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.extensions:
            return False
        try:
            if os.path.getsize(file_path) > self.max_size:
                return False
        except OSError:
            return False
        # Check exclude patterns
        norm_path = file_path.replace("\\", "/")
        for pattern in self.exclude_patterns:
            if pattern in norm_path:
                return False
        return True

    def _read_file(self, file_path: str) -> str:
        """Read file content with encoding fallback."""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, OSError):
                continue
        raise UnicodeDecodeError("utf-8", b"", 0, 1, f"Cannot decode {file_path}")

    @staticmethod
    def _count_by_severity(issues: list) -> dict:
        counts = {s.value: 0 for s in Severity}
        for issue in issues:
            counts[issue.severity.value] += 1
        return counts

    @staticmethod
    def _count_by_category(issues: list) -> dict:
        counts = {c.value: 0 for c in Category}
        for issue in issues:
            counts[issue.category.value] += 1
        return counts

    @staticmethod
    def _count_by_rule(issues: list) -> dict:
        counts = {}
        for issue in issues:
            key = f"{issue.rule_id} {issue.rule_name}"
            counts[key] = counts.get(key, 0) + 1
        return counts


def scan_path(path: str, **kwargs) -> ScanResult:
    """Convenience function to scan a path."""
    scanner = Scanner(path, **kwargs)
    return scanner.scan()

"""Generic text-based file analyzer for non-Python files."""
import re
from sentinel.models import FileStats


# Language detection by extension
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".java": "java",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell", ".bash": "shell",
    ".sql": "sql",
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "sass", ".less": "less",
    ".json": "json",
    ".yaml": "yaml", ".yml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
    ".toml": "toml",
    ".ini": "ini", ".cfg": "ini",
    ".r": "r", ".R": "r",
    ".lua": "lua",
    ".pl": "perl",
    ".dart": "dart",
}

# Comment patterns per language
SINGLE_LINE_COMMENTS = {
    "python": "#", "shell": "#", "ruby": "#", "perl": "#", "r": "#",
    "javascript": "//", "typescript": "//", "java": "//", "c": "//",
    "cpp": "//", "csharp": "//", "go": "//", "rust": "//", "php": "//",
    "swift": "//", "kotlin": "//", "scala": "//", "sql": "--",
    "lua": "--",
}


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    return EXTENSION_MAP.get(ext, "unknown")


def analyze_generic(content: str, path: str, language: str = "") -> FileStats:
    """Analyze a file using generic text heuristics."""
    if not language:
        language = detect_language(path)

    stats = FileStats(path=path, language=language)
    content = content.rstrip("\n")
    lines = content.split("\n")
    stats.lines = len(lines)

    comment_prefix = SINGLE_LINE_COMMENTS.get(language, "")
    in_block_comment = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            stats.blank_lines += 1
            continue

        # Block comment detection for C-like languages
        if language in ("c", "cpp", "java", "javascript", "typescript",
                        "csharp", "go", "rust", "php", "swift", "kotlin", "scala"):
            if in_block_comment:
                stats.comment_lines += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("/*"):
                stats.comment_lines += 1
                if "*/" not in stripped[2:]:
                    in_block_comment = True
                continue

        if comment_prefix and stripped.startswith(comment_prefix):
            stats.comment_lines += 1
        else:
            stats.code_lines += 1

    # Count functions (heuristic for various languages)
    stats.functions = _count_functions(content, language)
    stats.classes = _count_classes(content, language)

    return stats


def _count_functions(content: str, language: str) -> int:
    """Heuristic function counting."""
    patterns = {
        "javascript": r'\bfunction\s+\w+|=>\s*[{(]',
        "typescript": r'\bfunction\s+\w+|=>\s*[{(]',
        "java": r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*\{',
        "c": r'[\w\*]+\s+\w+\s*\([^)]*\)\s*\{',
        "cpp": r'[\w\*:]+::\w+\s*\([^)]*\)|[\w\*]+\s+\w+\s*\([^)]*\)\s*\{',
        "csharp": r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\([^)]*\)',
        "go": r'func\s+\w+',
        "rust": r'fn\s+\w+',
        "ruby": r'def\s+\w+',
        "php": r'function\s+\w+',
        "swift": r'func\s+\w+',
        "kotlin": r'fun\s+\w+',
        "scala": r'def\s+\w+',
        "shell": r'^\s*\w+\s*\(\s*\)\s*\{',
        "lua": r'function\s+\w+',
        "perl": r'sub\s+\w+',
        "dart": r'(?:void|int|String|bool|double|dynamic|Future|Stream)\s+\w+\s*\(',
    }
    pattern = patterns.get(language)
    if not pattern:
        return 0
    return len(re.findall(pattern, content, re.MULTILINE))


def _count_classes(content: str, language: str) -> int:
    """Heuristic class counting."""
    patterns = {
        "javascript": r'\bclass\s+\w+',
        "typescript": r'\bclass\s+\w+',
        "java": r'\b(?:class|interface|enum)\s+\w+',
        "cpp": r'\b(?:class|struct)\s+\w+',
        "csharp": r'\b(?:class|interface|struct|enum)\s+\w+',
        "php": r'\b(?:class|interface|trait)\s+\w+',
        "swift": r'\b(?:class|struct|protocol|enum)\s+\w+',
        "kotlin": r'\b(?:class|interface|object|enum)\s+\w+',
        "scala": r'\b(?:class|object|trait)\s+\w+',
        "ruby": r'\b(?:class|module)\s+\w+',
        "dart": r'\b(?:class|mixin|enum)\s+\w+',
    }
    pattern = patterns.get(language)
    if not pattern:
        return 0
    return len(re.findall(pattern, content))

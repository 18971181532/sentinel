"""Core data models for Sentinel."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def weight(self) -> int:
        return {
            Severity.CRITICAL: 100,
            Severity.HIGH: 50,
            Severity.MEDIUM: 20,
            Severity.LOW: 5,
            Severity.INFO: 1,
        }[self]

    @property
    def order(self) -> int:
        return {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }[self]


class Category(Enum):
    """Issue categories."""
    SECURITY = "security"
    BUG = "bug"
    COMPLEXITY = "complexity"
    STYLE = "style"
    DUPLICATE = "duplicate"
    MAINTAINABILITY = "maintainability"


@dataclass
class Issue:
    """A single code issue found by a rule."""
    rule_id: str
    rule_name: str
    category: Category
    severity: Severity
    message: str
    file_path: str
    line: int = 0
    column: int = 0
    snippet: str = ""
    suggestion: str = ""
    confidence: float = 1.0  # 0.0 - 1.0

    @property
    def score(self) -> float:
        return self.severity.weight * self.confidence


@dataclass
class FileStats:
    """Statistics for a single scanned file."""
    path: str
    language: str
    lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    code_lines: int = 0
    functions: int = 0
    classes: int = 0
    max_complexity: int = 0
    avg_complexity: float = 0.0
    issues: list = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def comment_ratio(self) -> float:
        if self.code_lines == 0:
            return 0.0
        return self.comment_lines / self.code_lines


@dataclass
class ScanResult:
    """Complete scan result."""
    target_path: str
    files_scanned: int = 0
    files_with_issues: int = 0
    total_issues: int = 0
    issues_by_severity: dict = field(default_factory=dict)
    issues_by_category: dict = field(default_factory=dict)
    issues_by_rule: dict = field(default_factory=dict)
    file_stats: dict = field(default_factory=dict)
    all_issues: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    tech_debt: Optional[dict] = None
    scan_time: float = 0.0
    languages: dict = field(default_factory=dict)

    def get_issues_for_file(self, path: str) -> list:
        return [i for i in self.all_issues if i.file_path == path]

    def get_top_files(self, n: int = 10) -> list:
        scored = []
        for path, stats in self.file_stats.items():
            score = sum(i.score for i in stats.issues)
            scored.append((path, score, len(stats.issues)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:n]

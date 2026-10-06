"""Rule base class and registry."""
from abc import ABC, abstractmethod
from typing import Optional
from sentinel.models import Issue, Severity, Category, FileStats


class Rule(ABC):
    """Base class for all analysis rules."""
    rule_id: str = ""
    rule_name: str = ""
    category: Category = Category.MAINTAINABILITY
    severity: Severity = Severity.MEDIUM
    description: str = ""
    languages: list = []  # empty = all languages

    def applies_to(self, language: str) -> bool:
        if not self.languages:
            return True
        return language.lower() in [l.lower() for l in self.languages]

    @abstractmethod
    def check(self, content: str, file_path: str, stats: FileStats) -> list:
        """Analyze file content and return list of Issue objects."""
        ...

    def make_issue(self, message: str, file_path: str, line: int = 0,
                   column: int = 0, snippet: str = "", suggestion: str = "",
                   severity: Optional[Severity] = None,
                   confidence: float = 1.0) -> Issue:
        return Issue(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            severity=severity or self.severity,
            message=message,
            file_path=file_path,
            line=line,
            column=column,
            snippet=snippet,
            suggestion=suggestion,
            confidence=confidence,
        )


class RuleRegistry:
    """Registry for all available rules."""
    _rules: list = []

    @classmethod
    def register(cls, rule_cls):
        cls._rules.append(rule_cls())
        return rule_cls

    @classmethod
    def get_all(cls) -> list:
        return list(cls._rules)

    @classmethod
    def get_by_category(cls, category: Category) -> list:
        return [r for r in cls._rules if r.category == category]

    @classmethod
    def get_by_id(cls, rule_id: str):
        for r in cls._rules:
            if r.rule_id == rule_id:
                return r
        return None

    @classmethod
    def count(cls) -> int:
        return len(cls._rules)

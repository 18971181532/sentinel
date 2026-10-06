"""Rule package — imports all rule modules to trigger registration."""
from sentinel.rules.base import Rule, RuleRegistry
from sentinel.rules import security, bugs, complexity, style, duplicates

__all__ = ["Rule", "RuleRegistry"]

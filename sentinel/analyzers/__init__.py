"""Analyzer package."""
from sentinel.analyzers.python_analyzer import analyze_python
from sentinel.analyzers.generic_analyzer import analyze_generic, detect_language

__all__ = ["analyze_python", "analyze_generic", "detect_language"]

"""Duplicate code detection."""
import re
import hashlib
from collections import defaultdict
from sentinel.models import Severity, Category, FileStats, Issue
from sentinel.rules.base import Rule, RuleRegistry


def normalize_line(line: str) -> str:
    """Normalize a line for duplicate detection."""
    line = line.strip()
    # Remove comments
    line = re.sub(r'#.*$', '', line)
    line = re.sub(r'//.*$', '', line)
    # Normalize whitespace
    line = re.sub(r'\s+', ' ', line)
    # Normalize strings (replace with placeholder)
    line = re.sub(r'"[^"]*"', '"STR"', line)
    line = re.sub(r"'[^']*'", "'STR'", line)
    # Normalize numbers
    line = re.sub(r'\b\d+\b', 'NUM', line)
    return line.strip()


def find_duplicate_blocks(files_content: dict, min_lines: int = 5) -> list:
    """
    Find duplicate code blocks across files.

    Args:
        files_content: dict of {file_path: content}
        min_lines: minimum number of consecutive lines to consider a duplicate

    Returns:
        list of dicts with keys: hash, lines, occurrences [(file_path, start_line), ...]
    """
    # Collect normalized line sequences per file
    file_lines = {}
    for path, content in files_content.items():
        lines = [normalize_line(l) for l in content.split("\n")]
        # Filter out empty/noise lines
        file_lines[path] = lines

    # Find all sequences of min_lines and hash them
    seq_hashes = defaultdict(list)  # hash -> [(file_path, start_line, actual_lines)]

    for path, lines in file_lines.items():
        n = len(lines)
        for i in range(n - min_lines + 1):
            block = lines[i:i + min_lines]
            # Skip blocks that are mostly empty or just braces
            non_empty = [l for l in block if l and l not in ('{', '}', 'else:', 'pass')]
            if len(non_empty) < min_lines // 2:
                continue
            block_str = "\n".join(block)
            h = hashlib.md5(block_str.encode()).hexdigest()
            seq_hashes[h].append((path, i + 1, block))

    # Filter to hashes with multiple occurrences
    duplicates = []
    for h, occurrences in seq_hashes.items():
        if len(occurrences) >= 2:
            # Check if these are from different files or different locations
            paths = set(o[0] for o in occurrences)
            if len(paths) >= 2 or len(occurrences) >= 2:
                duplicates.append({
                    "hash": h,
                    "lines": occurrences[0][2],
                    "line_count": len(occurrences[0][2]),
                    "occurrences": [(o[0], o[1]) for o in occurrences],
                })

    # Sort by number of occurrences (most duplicated first)
    duplicates.sort(key=lambda d: len(d["occurrences"]), reverse=True)
    return duplicates


@RuleRegistry.register
class DuplicateCodeRule(Rule):
    rule_id = "DUP001"
    rule_name = "Duplicate Code"
    category = Category.DUPLICATE
    severity = Severity.LOW
    description = "Detects duplicated code blocks across the codebase."

    def check(self, content, file_path, stats):
        # This rule works at the scanner level, not per-file
        return []

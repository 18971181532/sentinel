"""Test helpers for Sentinel."""
import os
import tempfile
import shutil


def create_temp_project(files: dict) -> str:
    """
    Create a temporary directory with sample code files.

    Args:
        files: dict of {relative_path: content}

    Returns:
        Path to temporary directory
    """
    tmpdir = tempfile.mkdtemp(prefix="sentinel_test_")
    for rel_path, content in files.items():
        full_path = os.path.join(tmpdir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    return tmpdir


def cleanup_temp_project(path: str):
    """Remove a temporary project directory."""
    shutil.rmtree(path, ignore_errors=True)


# Sample code snippets for testing
SAMPLE_PYTHON_WITH_ISSUES = '''
import os
import sys
import json

password = "secret123"
api_key = "sk-1234567890abcdef"

def connect_db():
    conn = "mysql://user:pass@localhost/db"
    return conn

def query(user_input):
    result = db.execute("SELECT * FROM users WHERE id = " + user_input)
    return result

def run_cmd(cmd):
    os.system("ls -la " + cmd)

def load_data(data):
    return pickle.loads(data)

def very_complex_function(a, b, c, d, e, f):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            return 1
                        else:
                            return 2
                    else:
                        return 3
                else:
                    return 4
            else:
                return 5
        else:
            return 6
    else:
        return 0

# TODO: fix this later
# FIXME: this is broken
def unused_import_example():
    print("hello")
    return None
'''

SAMPLE_PYTHON_CLEAN = '''
"""A clean Python module."""
import os
from typing import List, Optional


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def process_items(items: List[str]) -> List[str]:
    """Process a list of items."""
    result = []
    for item in items:
        if item:
            result.append(item.strip())
    return result


class Calculator:
    """Simple calculator class."""

    def __init__(self, initial: float = 0.0):
        self.value = initial

    def add(self, amount: float) -> float:
        """Add amount to current value."""
        self.value += amount
        return self.value

    def reset(self) -> None:
        """Reset calculator to zero."""
        self.value = 0.0
'''

SAMPLE_JAVASCRIPT = '''
const password = "admin123";
const apiKey = "ghp_abcdefghijklmnopqrstuvwxyz123456";

function fetchData(url) {
    return fetch(url + "?q=" + userInput);
}

function execute(command) {
    eval(command);
}

const longLine = "This is a very long line that exceeds the maximum allowed line length for code style checking in most projects and should be wrapped to improve readability";
'''

"""Tests for code analyzers."""
import unittest
from sentinel.analyzers.python_analyzer import analyze_python, get_function_locations
from sentinel.analyzers.generic_analyzer import analyze_generic, detect_language


class TestPythonAnalyzer(unittest.TestCase):
    def test_basic_stats(self):
        code = '''"""Module docstring."""
import os

def add(a, b):
    """Add two numbers."""
    return a + b

class Calc:
    """Calculator class."""
    def compute(self, x):
        return x * 2
'''
        stats = analyze_python(code, "test.py")
        self.assertEqual(stats.language, "python")
        self.assertGreater(stats.lines, 0)
        self.assertEqual(stats.functions, 2)
        self.assertEqual(stats.classes, 1)
        self.assertGreater(stats.comment_lines, 0)

    def test_code_lines_count(self):
        code = "x = 1\ny = 2\nz = 3\n"
        stats = analyze_python(code, "test.py")
        self.assertEqual(stats.code_lines, 3)

    def test_blank_lines(self):
        code = "x = 1\n\ny = 2\n\n\nz = 3\n"
        stats = analyze_python(code, "test.py")
        self.assertEqual(stats.blank_lines, 3)

    def test_syntax_error_handled(self):
        code = "def broken(\n"
        stats = analyze_python(code, "test.py")
        self.assertEqual(stats.functions, 0)  # AST parse fails, but no crash

    def test_get_function_locations(self):
        code = "def f():\n    pass\n\ndef g():\n    pass\n"
        locs = get_function_locations(code)
        self.assertEqual(len(locs), 2)
        self.assertEqual(locs[0][0], "f")
        self.assertEqual(locs[1][0], "g")


class TestGenericAnalyzer(unittest.TestCase):
    def test_detect_language_python(self):
        self.assertEqual(detect_language("test.py"), "python")

    def test_detect_language_javascript(self):
        self.assertEqual(detect_language("app.js"), "javascript")
        self.assertEqual(detect_language("app.tsx"), "typescript")

    def test_detect_language_unknown(self):
        self.assertEqual(detect_language("file.xyz"), "unknown")

    def test_analyze_javascript(self):
        code = '''// Comment
function add(a, b) {
    return a + b;
}

class Calculator {
    compute(x) { return x * 2; }
}
'''
        stats = analyze_generic(code, "test.js")
        self.assertEqual(stats.language, "javascript")
        self.assertGreater(stats.functions, 0)
        self.assertGreater(stats.comment_lines, 0)

    def test_analyze_java(self):
        code = '''// Comment
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
'''
        stats = analyze_generic(code, "Hello.java")
        self.assertEqual(stats.language, "java")
        self.assertGreater(stats.functions, 0)

    def test_analyze_html(self):
        code = "<html><body><h1>Hello</h1></body></html>\n"
        stats = analyze_generic(code, "index.html")
        self.assertEqual(stats.language, "html")

    def test_comment_detection(self):
        code = "# comment line\ncode_line = 1\n"
        stats = analyze_generic(code, "test.py", "python")
        self.assertEqual(stats.comment_lines, 1)
        self.assertEqual(stats.code_lines, 1)


if __name__ == "__main__":
    unittest.main()

"""Tests for complexity rules."""
import unittest
from sentinel.models import FileStats
from sentinel.rules.complexity import (
    CyclomaticComplexityRule, FunctionLengthRule, NestingDepthRule,
    TooManyArgumentsRule, FileTooLargeRule, compute_cyclomatic_complexity,
)
import ast


class TestCyclomaticComplexity(unittest.TestCase):
    def test_simple_function(self):
        code = "def f():\n    return 1\n"
        tree = ast.parse(code)
        comp = compute_cyclomatic_complexity(tree)
        self.assertEqual(comp["f"]["complexity"], 1)

    def test_function_with_if(self):
        code = "def f(x):\n    if x > 0:\n        return 1\n    return 0\n"
        tree = ast.parse(code)
        comp = compute_cyclomatic_complexity(tree)
        self.assertEqual(comp["f"]["complexity"], 2)

    def test_high_complexity_triggered(self):
        code = """def f(x):
    if x > 0:
        if x > 1:
            if x > 2:
                if x > 3:
                    if x > 4:
                        if x > 5:
                            if x > 6:
                                if x > 7:
                                    if x > 8:
                                        if x > 9:
                                            if x > 10:
                                                return 1
    return 0
"""
        rule = CyclomaticComplexityRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)


class TestFunctionLength(unittest.TestCase):
    def test_long_function(self):
        lines = ["def f():"] + [f"    x{i} = {i}" for i in range(60)]
        code = "\n".join(lines) + "\n"
        rule = FunctionLengthRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_short_function_ok(self):
        code = "def f():\n    return 1\n"
        rule = FunctionLengthRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestNestingDepth(unittest.TestCase):
    def test_deep_nesting(self):
        code = """def f():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        pass
"""
        rule = NestingDepthRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)


class TestTooManyArguments(unittest.TestCase):
    def test_many_args(self):
        code = "def f(a, b, c, d, e, f):\n    pass\n"
        rule = TooManyArgumentsRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_few_args_ok(self):
        code = "def f(a, b):\n    pass\n"
        rule = TooManyArgumentsRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestFileTooLarge(unittest.TestCase):
    def test_large_file(self):
        code = "\n".join([f"x{i} = {i}" for i in range(600)])
        rule = FileTooLargeRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_small_file_ok(self):
        code = "x = 1\n"
        rule = FileTooLargeRule()
        issues = rule.check(code, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()

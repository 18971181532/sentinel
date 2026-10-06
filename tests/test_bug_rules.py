"""Tests for bug pattern rules."""
import unittest
from sentinel.models import FileStats
from sentinel.rules.bugs import (
    BareExceptRule, MutableDefaultArgRule, ComparisonWithNoneRule,
    UnusedImportRule, PrintStatementRule, TodoCommentRule, BroadExceptionCatchRule,
)


class TestBareExcept(unittest.TestCase):
    def setUp(self):
        self.rule = BareExceptRule()

    def test_bare_except(self):
        content = "try:\n    x = 1\nexcept:\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_specific_except_ok(self):
        content = "try:\n    x = 1\nexcept ValueError:\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestMutableDefaultArg(unittest.TestCase):
    def setUp(self):
        self.rule = MutableDefaultArgRule()

    def test_list_default(self):
        content = "def f(x=[]):\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_dict_default(self):
        content = "def f(x={}):\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_immutable_default_ok(self):
        content = "def f(x=0):\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestComparisonWithNone(unittest.TestCase):
    def setUp(self):
        self.rule = ComparisonWithNoneRule()

    def test_eq_none(self):
        content = "if x == None:\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_is_none_ok(self):
        content = "if x is None:\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestTodoComment(unittest.TestCase):
    def setUp(self):
        self.rule = TodoCommentRule()

    def test_todo(self):
        content = "# TODO: fix this later\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_fixme(self):
        content = "# FIXME: broken\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_normal_comment_ok(self):
        content = "# This is a normal comment\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestBroadExceptionCatch(unittest.TestCase):
    def setUp(self):
        self.rule = BroadExceptionCatchRule()

    def test_catch_exception(self):
        content = "try:\n    x = 1\nexcept Exception:\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)

    def test_specific_ok(self):
        content = "try:\n    x = 1\nexcept ValueError:\n    pass\n"
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestPrintStatement(unittest.TestCase):
    def setUp(self):
        self.rule = PrintStatementRule()

    def test_print(self):
        content = 'print("hello")\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 1)


if __name__ == "__main__":
    unittest.main()

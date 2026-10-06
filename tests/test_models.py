"""Tests for data models."""
import unittest
from sentinel.models import Issue, Severity, Category, FileStats, ScanResult


class TestSeverity(unittest.TestCase):
    def test_severity_weights(self):
        self.assertEqual(Severity.CRITICAL.weight, 100)
        self.assertEqual(Severity.HIGH.weight, 50)
        self.assertEqual(Severity.MEDIUM.weight, 20)
        self.assertEqual(Severity.LOW.weight, 5)
        self.assertEqual(Severity.INFO.weight, 1)

    def test_severity_order(self):
        self.assertEqual(Severity.CRITICAL.order, 0)
        self.assertEqual(Severity.HIGH.order, 1)
        self.assertEqual(Severity.MEDIUM.order, 2)
        self.assertEqual(Severity.LOW.order, 3)
        self.assertEqual(Severity.INFO.order, 4)


class TestIssue(unittest.TestCase):
    def test_issue_creation(self):
        issue = Issue(
            rule_id="SEC001", rule_name="Test Rule",
            category=Category.SECURITY, severity=Severity.HIGH,
            message="Test message", file_path="test.py", line=10,
        )
        self.assertEqual(issue.rule_id, "SEC001")
        self.assertEqual(issue.severity, Severity.HIGH)
        self.assertEqual(issue.score, 50)  # HIGH weight * confidence 1.0

    def test_issue_score_with_confidence(self):
        issue = Issue(
            rule_id="T1", rule_name="T", category=Category.BUG,
            severity=Severity.CRITICAL, message="m", file_path="f",
            confidence=0.5,
        )
        self.assertEqual(issue.score, 50)  # 100 * 0.5


class TestFileStats(unittest.TestCase):
    def test_file_stats(self):
        stats = FileStats(path="test.py", language="python")
        stats.lines = 100
        stats.code_lines = 80
        stats.comment_lines = 15
        stats.blank_lines = 5
        self.assertEqual(stats.comment_ratio, 15 / 80)

    def test_file_stats_zero_code(self):
        stats = FileStats(path="empty.py", language="python")
        self.assertEqual(stats.comment_ratio, 0.0)


class TestScanResult(unittest.TestCase):
    def test_get_top_files(self):
        result = ScanResult(target_path="/test")
        # Create mock file stats
        from sentinel.models import FileStats
        stats1 = FileStats(path="a.py", language="python")
        stats1.issues = [Issue(rule_id="T1", rule_name="T", category=Category.BUG,
                                severity=Severity.HIGH, message="m", file_path="a.py")]
        stats2 = FileStats(path="b.py", language="python")
        stats2.issues = [Issue(rule_id="T1", rule_name="T", category=Category.BUG,
                                severity=Severity.CRITICAL, message="m", file_path="b.py")]
        result.file_stats = {"a.py": stats1, "b.py": stats2}

        top = result.get_top_files(2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0][0], "b.py")  # critical has higher score


if __name__ == "__main__":
    unittest.main()

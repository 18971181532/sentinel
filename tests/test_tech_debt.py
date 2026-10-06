"""Tests for tech debt estimation."""
import unittest
from sentinel.models import ScanResult, FileStats, Issue, Severity, Category
from sentinel.tech_debt import compute_tech_debt, generate_summary


def make_result(issues_by_sev=None, files=None, total_issues=0):
    result = ScanResult(target_path="/test")
    result.total_issues = total_issues
    result.issues_by_severity = issues_by_sev or {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    result.issues_by_category = {c.value: 0 for c in Category}
    result.file_stats = files or {}
    result.all_issues = []
    return result


class TestTechDebt(unittest.TestCase):
    def test_clean_codebase(self):
        result = make_result()
        debt = compute_tech_debt(result)
        self.assertEqual(debt["total_debt_minutes"], 0)
        self.assertEqual(debt["quality_score"], 100)
        self.assertEqual(debt["grade"], "A")
        self.assertEqual(debt["risk_level"], "low")

    def test_critical_issues(self):
        result = make_result(
            issues_by_sev={"critical": 5, "high": 0, "medium": 0, "low": 0, "info": 0},
            total_issues=5,
        )
        debt = compute_tech_debt(result)
        self.assertGreater(debt["total_debt_minutes"], 0)
        self.assertEqual(debt["risk_level"], "critical")

    def test_grade_boundaries(self):
        # A grade
        result = make_result(total_issues=0)
        debt = compute_tech_debt(result)
        self.assertEqual(debt["grade"], "A")

    def test_debt_by_severity(self):
        result = make_result(
            issues_by_sev={"critical": 1, "high": 2, "medium": 0, "low": 0, "info": 0},
            total_issues=3,
        )
        debt = compute_tech_debt(result)
        self.assertEqual(debt["debt_by_severity"]["critical"], 120)
        self.assertEqual(debt["debt_by_severity"]["high"], 120)  # 2 * 60

    def test_formatted_time(self):
        result = make_result(
            issues_by_sev={"critical": 4, "high": 0, "medium": 0, "low": 0, "info": 0},
            total_issues=4,
        )
        debt = compute_tech_debt(result)
        # 4 * 120 = 480 minutes = 8 hours = 1 day
        self.assertIn("d", debt["formatted"])

    def test_issues_per_kloc(self):
        stats = FileStats(path="test.py", language="python")
        stats.code_lines = 1000
        result = make_result(files={"test.py": stats}, total_issues=10)
        debt = compute_tech_debt(result)
        self.assertEqual(debt["issues_per_kloc"], 10.0)

    def test_breakdown(self):
        result = make_result(total_issues=5)
        result.issues_by_category = {"security": 2, "bug": 3, "complexity": 0, "style": 0, "duplicate": 0, "maintainability": 0}
        debt = compute_tech_debt(result)
        self.assertEqual(debt["breakdown"]["security_issues"], 2)
        self.assertEqual(debt["breakdown"]["bug_issues"], 3)


class TestGenerateSummary(unittest.TestCase):
    def test_summary_contains_key_info(self):
        result = make_result(total_issues=5)
        result.files_scanned = 10
        result.files_with_issues = 3
        summary = generate_summary(result)
        self.assertIn("SENTINEL", summary)
        self.assertIn("10", summary)
        self.assertIn("5", summary)

    def test_summary_clean_codebase(self):
        result = make_result()
        summary = generate_summary(result)
        self.assertIn("Grade A", summary)


if __name__ == "__main__":
    unittest.main()

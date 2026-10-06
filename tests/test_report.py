"""Tests for report generation."""
import os
import json
import tempfile
import unittest
from sentinel.models import ScanResult, FileStats, Issue, Severity, Category
from sentinel.report import export_to_json, export_to_markdown, export_to_html


def make_sample_result():
    result = ScanResult(target_path="/test/project")
    result.files_scanned = 3
    result.files_with_issues = 2
    result.total_issues = 5
    result.scan_time = 0.5
    result.issues_by_severity = {"critical": 1, "high": 2, "medium": 1, "low": 1, "info": 0}
    result.issues_by_category = {"security": 2, "bug": 1, "complexity": 1, "style": 1, "duplicate": 0, "maintainability": 0}
    result.issues_by_rule = {"SEC001 Hardcoded Secrets": 2, "BUG001 Bare Except": 1, "CPX001 High Complexity": 1, "STY001 Line Too Long": 1}
    result.languages = {"python": 2, "javascript": 1}

    stats1 = FileStats(path="main.py", language="python", lines=100, code_lines=80,
                       comment_lines=15, functions=3, classes=1, max_complexity=8)
    stats2 = FileStats(path="utils.py", language="python", lines=50, code_lines=40,
                       comment_lines=5, functions=2, max_complexity=3)
    result.file_stats = {"main.py": stats1, "utils.py": stats2}

    result.all_issues = [
        Issue(rule_id="SEC001", rule_name="Hardcoded Secrets", category=Category.SECURITY,
              severity=Severity.CRITICAL, message="Hardcoded password", file_path="main.py", line=10,
              snippet='password = "secret"', suggestion="Use env vars"),
        Issue(rule_id="SEC002", rule_name="SQL Injection", category=Category.SECURITY,
              severity=Severity.HIGH, message="SQL concatenation", file_path="main.py", line=20,
              snippet='db.execute("SELECT " + x)', suggestion="Use parameterized queries"),
        Issue(rule_id="BUG001", rule_name="Bare Except", category=Category.BUG,
              severity=Severity.HIGH, message="Bare except", file_path="utils.py", line=5,
              snippet="except:", suggestion="Catch specific exceptions"),
    ]
    return result


class TestExportJSON(unittest.TestCase):
    def test_export_json(self):
        result = make_sample_result()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            export_to_json(result, path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["summary"]["files_scanned"], 3)
            self.assertEqual(data["summary"]["total_issues"], 5)
            self.assertIn("main.py", data["files"])
            self.assertEqual(len(data["issues"]), 3)
        finally:
            os.unlink(path)


class TestExportMarkdown(unittest.TestCase):
    def test_export_markdown(self):
        result = make_sample_result()
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            path = f.name
        try:
            export_to_markdown(result, path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Sentinel", content)
            self.assertIn("Issues by Severity", content)
            self.assertIn("main.py", content)
            self.assertIn("Hardcoded password", content)
        finally:
            os.unlink(path)


class TestExportHTML(unittest.TestCase):
    def test_export_html(self):
        result = make_sample_result()
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            path = f.name
        try:
            export_to_html(result, path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("Sentinel", content)
            self.assertIn("Quality Score", content)
            self.assertIn("main.py", content)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

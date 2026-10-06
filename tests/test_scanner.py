"""Tests for the main scanner."""
import os
import unittest
from sentinel.scanner import Scanner, scan_path
from tests.helpers import create_temp_project, cleanup_temp_project, SAMPLE_PYTHON_WITH_ISSUES, SAMPLE_PYTHON_CLEAN


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.tmpdir = create_temp_project({
            "main.py": SAMPLE_PYTHON_WITH_ISSUES,
            "clean.py": SAMPLE_PYTHON_CLEAN,
            "README.md": "# Test Project\n\nThis is a test.\n",
        })

    def tearDown(self):
        cleanup_temp_project(self.tmpdir)

    def test_scan_directory(self):
        result = scan_path(self.tmpdir)
        self.assertGreater(result.files_scanned, 0)
        self.assertGreater(result.total_issues, 0)

    def test_scan_file(self):
        filepath = os.path.join(self.tmpdir, "main.py")
        result = scan_path(filepath)
        self.assertEqual(result.files_scanned, 1)
        self.assertGreater(result.total_issues, 0)

    def test_issues_by_severity(self):
        result = scan_path(self.tmpdir)
        self.assertIn("critical", result.issues_by_severity)
        self.assertIn("high", result.issues_by_severity)

    def test_issues_by_category(self):
        result = scan_path(self.tmpdir)
        self.assertIn("security", result.issues_by_category)

    def test_file_stats(self):
        result = scan_path(self.tmpdir)
        self.assertIn("main.py", result.file_stats)
        stats = result.file_stats["main.py"]
        self.assertEqual(stats.language, "python")
        self.assertGreater(stats.lines, 0)

    def test_top_files(self):
        result = scan_path(self.tmpdir)
        top = result.get_top_files(5)
        self.assertGreater(len(top), 0)
        # main.py should have more issues than clean.py
        paths = [t[0] for t in top]
        self.assertIn("main.py", paths)

    def test_scan_time_recorded(self):
        result = scan_path(self.tmpdir)
        self.assertGreaterEqual(result.scan_time, 0)

    def test_languages_detected(self):
        result = scan_path(self.tmpdir)
        self.assertIn("python", result.languages)
        self.assertIn("markdown", result.languages)


class TestScannerFilters(unittest.TestCase):
    def test_exclude_patterns(self):
        tmpdir = create_temp_project({
            "src/main.py": "password = 'secret123'\n",
            "tests/test_main.py": "password = 'test123'\n",
        })
        try:
            result = scan_path(tmpdir, exclude_patterns=["tests/"])
            paths = list(result.file_stats.keys())
            self.assertIn("src/main.py", paths)
            self.assertNotIn("tests/test_main.py", paths)
        finally:
            cleanup_temp_project(tmpdir)

    def test_skip_dirs(self):
        tmpdir = create_temp_project({
            "main.py": "x = 1\n",
            "__pycache__/cached.py": "password = 'secret'\n",
            "node_modules/pkg/index.js": "var x = 1;\n",
        })
        try:
            result = scan_path(tmpdir)
            paths = list(result.file_stats.keys())
            self.assertIn("main.py", paths)
            self.assertNotIn("__pycache__/cached.py", paths)
            self.assertNotIn("node_modules/pkg/index.js", paths)
        finally:
            cleanup_temp_project(tmpdir)


class TestScannerEdgeCases(unittest.TestCase):
    def test_empty_directory(self):
        import tempfile
        tmpdir = tempfile.mkdtemp()
        try:
            result = scan_path(tmpdir)
            self.assertEqual(result.files_scanned, 0)
            self.assertEqual(result.total_issues, 0)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_nonexistent_path(self):
        with self.assertRaises(Exception):
            scan_path("/nonexistent/path/12345")


if __name__ == "__main__":
    unittest.main()

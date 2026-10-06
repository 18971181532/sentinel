"""Tests for CLI."""
import os
import sys
import json
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch
from sentinel.cli import build_parser, main, cmd_scan, cmd_rules
from tests.helpers import create_temp_project, cleanup_temp_project, SAMPLE_PYTHON_WITH_ISSUES


class TestCLIParser(unittest.TestCase):
    def test_parser_creation(self):
        parser = build_parser()
        self.assertIsNotNone(parser)

    def test_scan_command(self):
        parser = build_parser()
        args = parser.parse_args(["scan", "/tmp/test"])
        self.assertEqual(args.command, "scan")
        self.assertEqual(args.path, "/tmp/test")

    def test_scan_with_json_flag(self):
        parser = build_parser()
        args = parser.parse_args(["scan", "--json", "/tmp/test"])
        self.assertTrue(args.json)

    def test_rules_command(self):
        parser = build_parser()
        args = parser.parse_args(["rules"])
        self.assertEqual(args.command, "rules")

    def test_serve_command(self):
        parser = build_parser()
        args = parser.parse_args(["serve", "--port", "9000", "/tmp/test"])
        self.assertEqual(args.command, "serve")
        self.assertEqual(args.port, 9000)


class TestCLIScan(unittest.TestCase):
    def setUp(self):
        self.tmpdir = create_temp_project({
            "main.py": SAMPLE_PYTHON_WITH_ISSUES,
        })

    def tearDown(self):
        cleanup_temp_project(self.tmpdir)

    def test_scan_text_output(self):
        parser = build_parser()
        args = parser.parse_args(["scan", self.tmpdir])
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exit_code = cmd_scan(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertIn("SENTINEL", output)
        self.assertIn("Issues", output)

    def test_scan_json_output(self):
        parser = build_parser()
        args = parser.parse_args(["scan", "--json", self.tmpdir])
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exit_code = cmd_scan(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        data = json.loads(output)
        self.assertIn("summary", data)
        self.assertIn("issues", data)

    def test_scan_nonexistent_path(self):
        parser = build_parser()
        args = parser.parse_args(["scan", "/nonexistent/path/12345"])
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            exit_code = cmd_scan(args)
        finally:
            sys.stderr = old_stderr
        self.assertEqual(exit_code, 1)

    def test_scan_export_to_file(self):
        outfile = os.path.join(self.tmpdir, "report.json")
        parser = build_parser()
        args = parser.parse_args(["scan", "-o", outfile, self.tmpdir])
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cmd_scan(args)
        finally:
            sys.stdout = old_stdout
        self.assertTrue(os.path.exists(outfile))
        with open(outfile, "r") as f:
            data = json.load(f)
        self.assertIn("summary", data)


class TestCLIRules(unittest.TestCase):
    def test_list_rules(self):
        parser = build_parser()
        args = parser.parse_args(["rules"])
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exit_code = cmd_rules(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(exit_code, 0)
        self.assertIn("Available rules", output)
        self.assertIn("SEC001", output)

    def test_filter_by_category(self):
        parser = build_parser()
        args = parser.parse_args(["rules", "--category", "security"])
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cmd_rules(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertIn("SEC001", output)


class TestCLIMain(unittest.TestCase):
    def test_main_no_args(self):
        old_argv = sys.argv
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            sys.argv = ["sentinel"]
            exit_code = main()
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

"""HTTP server for Sentinel web dashboard."""
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from sentinel.scanner import Scanner
from sentinel.tech_debt import compute_tech_debt


class SentinelHandler(BaseHTTPRequestHandler):
    """HTTP request handler with API endpoints and static file serving."""

    result_cache = None
    target_path = None

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath, content_type):
        try:
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API routes
        if path == "/api/stats":
            self._handle_stats()
        elif path == "/api/issues":
            self._handle_issues(params)
        elif path == "/api/files":
            self._handle_files()
        elif path == "/api/severity":
            self._handle_severity()
        elif path == "/api/category":
            self._handle_category()
        elif path == "/api/rules":
            self._handle_rules()
        elif path == "/api/top-files":
            self._handle_top_files()
        elif path == "/api/duplicates":
            self._handle_duplicates()
        elif path == "/api/tech-debt":
            self._handle_tech_debt()
        elif path == "/api/languages":
            self._handle_languages()
        elif path == "/api/refresh":
            self._handle_refresh()
        elif path == "/api/file-detail":
            self._handle_file_detail(params)
        # Static files
        elif path == "/" or path == "/index.html":
            self._serve_static("index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self._serve_static("style.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._serve_static("app.js", "application/javascript; charset=utf-8")
        else:
            self.send_error(404)

    def _get_result(self):
        """Get cached scan result or perform scan."""
        if self.result_cache is None:
            scanner = Scanner(self.target_path)
            self.result_cache = scanner.scan()
        return self.result_cache

    def _handle_stats(self):
        result = self._get_result()
        debt = compute_tech_debt(result)
        self._send_json({
            "target": result.target_path,
            "files_scanned": result.files_scanned,
            "files_with_issues": result.files_with_issues,
            "total_issues": result.total_issues,
            "scan_time": round(result.scan_time, 3),
            "quality_score": debt["quality_score"],
            "grade": debt["grade"],
            "risk_level": debt["risk_level"],
            "tech_debt": debt["formatted"],
            "tech_debt_minutes": debt["total_debt_minutes"],
            "issues_per_kloc": debt["issues_per_kloc"],
            "total_code_lines": debt["total_code_lines"],
        })

    def _handle_issues(self, params):
        result = self._get_result()
        issues = result.all_issues
        # Filter by severity
        sev = params.get("severity", [None])[0]
        if sev:
            issues = [i for i in issues if i.severity.value == sev]
        # Filter by file
        file_filter = params.get("file", [None])[0]
        if file_filter:
            issues = [i for i in issues if file_filter in i.file_path]
        # Limit
        limit = int(params.get("limit", [200])[0])
        issues = issues[:limit]

        self._send_json([
            {
                "rule_id": i.rule_id, "rule_name": i.rule_name,
                "category": i.category.value, "severity": i.severity.value,
                "message": i.message, "file": i.file_path,
                "line": i.line, "snippet": i.snippet,
                "suggestion": i.suggestion, "confidence": i.confidence,
            }
            for i in issues
        ])

    def _handle_files(self):
        result = self._get_result()
        files = []
        for path, stats in result.file_stats.items():
            files.append({
                "path": path, "language": stats.language,
                "lines": stats.lines, "code_lines": stats.code_lines,
                "comment_lines": stats.comment_lines, "functions": stats.functions,
                "classes": stats.classes, "max_complexity": stats.max_complexity,
                "avg_complexity": round(stats.avg_complexity, 2),
                "issue_count": stats.issue_count,
            })
        self._send_json(sorted(files, key=lambda f: f["issue_count"], reverse=True))

    def _handle_severity(self):
        result = self._get_result()
        self._send_json(result.issues_by_severity)

    def _handle_category(self):
        result = self._get_result()
        self._send_json(result.issues_by_category)

    def _handle_rules(self):
        result = self._get_result()
        self._send_json(result.issues_by_rule)

    def _handle_top_files(self):
        result = self._get_result()
        top = result.get_top_files(20)
        self._send_json([
            {"path": p, "risk_score": round(s, 1), "issue_count": c}
            for p, s, c in top
        ])

    def _handle_duplicates(self):
        result = self._get_result()
        self._send_json(result.duplicates[:20])

    def _handle_tech_debt(self):
        result = self._get_result()
        self._send_json(compute_tech_debt(result))

    def _handle_languages(self):
        result = self._get_result()
        self._send_json(result.languages)

    def _handle_refresh(self):
        self.result_cache = None
        result = self._get_result()
        self._send_json({"status": "ok", "total_issues": result.total_issues})

    def _handle_file_detail(self, params):
        result = self._get_result()
        path = params.get("path", [""])[0]
        stats = result.file_stats.get(path)
        if not stats:
            self._send_json({"error": "file not found"}, 404)
            return
        issues = [i for i in result.all_issues if i.file_path == path]
        self._send_json({
            "path": path,
            "stats": {
                "language": stats.language, "lines": stats.lines,
                "code_lines": stats.code_lines, "comment_lines": stats.comment_lines,
                "functions": stats.functions, "classes": stats.classes,
                "max_complexity": stats.max_complexity,
                "avg_complexity": round(stats.avg_complexity, 2),
            },
            "issues": [
                {"rule_id": i.rule_id, "severity": i.severity.value,
                 "line": i.line, "message": i.message, "snippet": i.snippet}
                for i in issues
            ],
        })

    def _serve_static(self, filename, content_type):
        web_dir = os.path.join(os.path.dirname(__file__), "web")
        filepath = os.path.join(web_dir, filename)
        self._send_file(filepath, content_type)


class ThreadingHTTPServer(HTTPServer):
    """Multi-threaded HTTP server."""
    daemon_threads = True
    allow_reuse_address = True


def start_server(target_path: str, host: str = "127.0.0.1", port: int = 8765):
    """Start the Sentinel web dashboard server."""
    SentinelHandler.target_path = os.path.abspath(target_path)
    SentinelHandler.result_cache = None
    server = ThreadingHTTPServer((host, port), SentinelHandler)
    server.serve_forever()

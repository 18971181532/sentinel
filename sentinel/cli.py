"""Command-line interface for Sentinel."""
import argparse
import json
import os
import sys

from sentinel import __version__
from sentinel.scanner import Scanner, scan_path
from sentinel.tech_debt import compute_tech_debt, generate_summary
from sentinel.report import export_to_json, export_to_markdown, export_to_html
from sentinel.rules import RuleRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Sentinel — zero-dependency code security & quality scanner",
    )
    parser.add_argument("--version", action="version", version=f"sentinel {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan
    scan_p = subparsers.add_parser("scan", help="Scan a directory or file")
    scan_p.add_argument("path", nargs="?", default=".", help="Path to scan (default: current dir)")
    scan_p.add_argument("--json", action="store_true", help="Output results as JSON")
    scan_p.add_argument("--output", "-o", help="Write report to file (format by extension)")
    scan_p.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text")
    scan_p.add_argument("--min-severity", choices=["critical", "high", "medium", "low", "info"],
                        default="info", help="Minimum severity to report")
    scan_p.add_argument("--exclude", action="append", default=[], help="Exclude paths containing this string")
    scan_p.add_argument("--no-fail", action="store_true", help="Always exit 0, even with issues")

    # rules
    rules_p = subparsers.add_parser("rules", help="List available rules")
    rules_p.add_argument("--category", help="Filter by category")

    # serve
    serve_p = subparsers.add_parser("serve", help="Start web dashboard")
    serve_p.add_argument("path", nargs="?", default=".", help="Path to scan and display")
    serve_p.add_argument("--port", "-p", type=int, default=8765, help="Port to listen on")
    serve_p.add_argument("--host", default="127.0.0.1", help="Host to bind")

    return parser


def cmd_scan(args):
    """Execute scan command."""
    target = os.path.abspath(args.path)
    if not os.path.exists(target):
        print(f"Error: path not found: {target}", file=sys.stderr)
        return 1

    scanner = Scanner(target, exclude_patterns=args.exclude)
    result = scanner.scan()

    # Filter by minimum severity
    if args.min_severity != "info":
        from sentinel.models import Severity
        min_order = Severity(args.min_severity).order
        result.all_issues = [i for i in result.all_issues if i.severity.order <= min_order]
        result.total_issues = len(result.all_issues)

    # Output
    if args.output:
        ext = os.path.splitext(args.output)[1].lower()
        if ext == ".json":
            export_to_json(result, args.output)
        elif ext in (".md", ".markdown"):
            export_to_markdown(result, args.output)
        elif ext == ".html":
            export_to_html(result, args.output)
        else:
            export_to_markdown(result, args.output)
        print(f"Report written to {args.output}")
    elif args.json or args.format == "json":
        data = {
            "summary": {
                "files_scanned": result.files_scanned,
                "total_issues": result.total_issues,
                "quality_score": compute_tech_debt(result)["quality_score"],
            },
            "issues": [
                {"rule": i.rule_id, "severity": i.severity.value,
                 "file": i.file_path, "line": i.line, "message": i.message}
                for i in result.all_issues
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(generate_summary(result))

    # Exit code
    if not args.no_fail and result.total_issues > 0:
        critical = result.issues_by_severity.get("critical", 0)
        high = result.issues_by_severity.get("high", 0)
        if critical > 0 or high > 0:
            return 1
    return 0


def cmd_rules(args):
    """List available rules."""
    rules = RuleRegistry.get_all()
    if args.category:
        rules = [r for r in rules if r.category.value == args.category]

    print(f"Available rules: {len(rules)}")
    print()
    current_cat = None
    for rule in sorted(rules, key=lambda r: (r.category.value, r.rule_id)):
        if rule.category.value != current_cat:
            current_cat = rule.category.value
            print(f"  [{current_cat.upper()}]")
        print(f"    {rule.rule_id}  {rule.rule_name}")
        print(f"           {rule.description}")
        print(f"           severity: {rule.severity.value}, languages: {rule.languages or 'all'}")
        print()
    return 0


def cmd_serve(args):
    """Start web dashboard."""
    from sentinel.server import start_server
    target = os.path.abspath(args.path)
    print(f"Sentinel dashboard: http://{args.host}:{args.port}")
    print(f"Scanning: {target}")
    print("Press Ctrl+C to stop.")
    try:
        start_server(target, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    return 0


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    handlers = {
        "scan": cmd_scan,
        "rules": cmd_rules,
        "serve": cmd_serve,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

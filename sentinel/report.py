"""Report generation in multiple formats."""
import json
import os
from typing import Optional
from sentinel.models import ScanResult
from sentinel.tech_debt import compute_tech_debt


def export_to_json(result: ScanResult, output_path: str) -> str:
    """Export scan results to JSON."""
    data = {
        "target": result.target_path,
        "summary": {
            "files_scanned": result.files_scanned,
            "files_with_issues": result.files_with_issues,
            "total_issues": result.total_issues,
            "scan_time_seconds": round(result.scan_time, 3),
        },
        "issues_by_severity": result.issues_by_severity,
        "issues_by_category": result.issues_by_category,
        "issues_by_rule": result.issues_by_rule,
        "tech_debt": compute_tech_debt(result),
        "languages": result.languages,
        "files": {},
        "issues": [],
        "duplicates": result.duplicates,
    }

    for path, stats in result.file_stats.items():
        data["files"][path] = {
            "language": stats.language,
            "lines": stats.lines,
            "code_lines": stats.code_lines,
            "comment_lines": stats.comment_lines,
            "blank_lines": stats.blank_lines,
            "functions": stats.functions,
            "classes": stats.classes,
            "max_complexity": stats.max_complexity,
            "avg_complexity": round(stats.avg_complexity, 2),
            "issue_count": stats.issue_count,
        }

    for issue in result.all_issues:
        data["issues"].append({
            "rule_id": issue.rule_id,
            "rule_name": issue.rule_name,
            "category": issue.category.value,
            "severity": issue.severity.value,
            "message": issue.message,
            "file": issue.file_path,
            "line": issue.line,
            "column": issue.column,
            "snippet": issue.snippet,
            "suggestion": issue.suggestion,
            "confidence": issue.confidence,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path


def export_to_markdown(result: ScanResult, output_path: str) -> str:
    """Export scan results to Markdown report."""
    debt = compute_tech_debt(result)
    lines = []

    lines.append("# Sentinel — Code Security & Quality Report")
    lines.append("")
    lines.append(f"**Target:** `{result.target_path}`  ")
    lines.append(f"**Files scanned:** {result.files_scanned}  ")
    lines.append(f"**Total issues:** {result.total_issues}  ")
    lines.append(f"**Quality score:** {debt['quality_score']}/100 (Grade **{debt['grade']}**)  ")
    lines.append(f"**Risk level:** {debt['risk_level'].upper()}  ")
    lines.append(f"**Technical debt:** {debt['formatted']}  ")
    lines.append("")

    # Severity table
    lines.append("## Issues by Severity")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = result.issues_by_severity.get(sev, 0)
        lines.append(f"| {sev.upper()} | {count} |")
    lines.append("")

    # Category table
    lines.append("## Issues by Category")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, count in sorted(result.issues_by_category.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            lines.append(f"| {cat} | {count} |")
    lines.append("")

    # Top files
    top_files = result.get_top_files(10)
    if top_files:
        lines.append("## Top Problem Files")
        lines.append("")
        lines.append("| File | Issues | Risk Score |")
        lines.append("|------|--------|------------|")
        for path, score, count in top_files:
            lines.append(f"| `{path}` | {count} | {score:.0f} |")
        lines.append("")

    # All issues grouped by file
    lines.append("## All Issues")
    lines.append("")
    current_file = None
    for issue in sorted(result.all_issues, key=lambda i: (i.file_path, i.line)):
        if issue.file_path != current_file:
            current_file = issue.file_path
            lines.append(f"### `{current_file}`")
            lines.append("")
        sev_badge = f"**{issue.severity.value.upper()}**"
        lines.append(f"- **{issue.rule_id}** {sev_badge} — {issue.message}")
        if issue.line:
            lines.append(f"  - Location: line {issue.line}")
        if issue.snippet:
            lines.append(f"  - Code: `{issue.snippet[:100]}`")
        if issue.suggestion:
            lines.append(f"  - Suggestion: {issue.suggestion}")
        lines.append("")

    # Duplicates
    if result.duplicates:
        lines.append("## Duplicate Code")
        lines.append("")
        for i, dup in enumerate(result.duplicates[:10], 1):
            lines.append(f"### Duplicate #{i} ({dup['line_count']} lines, {len(dup['occurrences'])} occurrences)")
            lines.append("")
            for path, line in dup["occurrences"]:
                lines.append(f"- `{path}`:{line}")
            lines.append("")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


def export_to_html(result: ScanResult, output_path: str) -> str:
    """Export scan results to a standalone HTML report."""
    debt = compute_tech_debt(result)

    # Build issue rows
    issue_rows = ""
    for issue in sorted(result.all_issues, key=lambda i: (i.severity.order, i.file_path, i.line)):
        sev_class = f"sev-{issue.severity.value}"
        issue_rows += f"""<tr class="{sev_class}">
            <td><span class="badge {sev_class}">{issue.severity.value.upper()}</span></td>
            <td><code>{issue.rule_id}</code></td>
            <td>{issue.category.value}</td>
            <td><code>{issue.file_path}</code>:{issue.line}</td>
            <td>{issue.message}</td>
        </tr>\n"""

    # Severity data for chart
    sev_data = json.dumps([
        {"label": s.upper(), "value": result.issues_by_severity.get(s, 0)}
        for s in ["critical", "high", "medium", "low", "info"]
    ])

    # Category data
    cat_data = json.dumps([
        {"label": k, "value": v}
        for k, v in sorted(result.issues_by_category.items(), key=lambda x: x[1], reverse=True)
        if v > 0
    ])

    # Top files
    top_files = result.get_top_files(10)
    file_rows = ""
    for path, score, count in top_files:
        file_rows += f"<tr><td><code>{path}</code></td><td>{count}</td><td>{score:.0f}</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sentinel Report — {os.path.basename(result.target_path)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 2rem; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ color: #58a6ff; margin-bottom: 0.5rem; }}
h2 {{ color: #79c0ff; margin: 2rem 0 1rem; border-bottom: 1px solid #21262d; padding-bottom: 0.5rem; }}
.summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.2rem; }}
.card .label {{ font-size: 0.8rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }}
.card .value {{ font-size: 1.8rem; font-weight: 700; margin-top: 0.3rem; }}
.value.critical {{ color: #f85149; }} .value.high {{ color: #d29922; }}
.value.medium {{ color: #e3b341; }} .value.low {{ color: #3fb950; }}
.value.good {{ color: #3fb950; }}
table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
th, td {{ padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid #21262d; }}
th {{ background: #161b22; color: #8b949e; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }}
tr:hover {{ background: #161b22; }}
.badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
.badge.sev-critical {{ background: #f85149; color: #fff; }}
.badge.sev-high {{ background: #d29922; color: #000; }}
.badge.sev-medium {{ background: #e3b341; color: #000; }}
.badge.sev-low {{ background: #3fb950; color: #000; }}
.badge.sev-info {{ background: #58a6ff; color: #000; }}
code {{ background: #161b22; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }}
.charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 1.5rem 0; }}
@media (max-width: 768px) {{ .charts {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
<h1>Sentinel — Code Security &amp; Quality Report</h1>
<p style="color:#8b949e;">Target: <code>{result.target_path}</code> | Scan time: {result.scan_time:.2f}s</p>

<div class="summary-grid">
<div class="card"><div class="label">Quality Score</div><div class="value {'good' if debt['quality_score']>=80 else 'high' if debt['quality_score']>=60 else 'critical'}">{debt['quality_score']}</div></div>
<div class="card"><div class="label">Grade</div><div class="value">{debt['grade']}</div></div>
<div class="card"><div class="label">Risk Level</div><div class="value {'critical' if debt['risk_level']=='critical' else 'high' if debt['risk_level']=='high' else 'medium' if debt['risk_level']=='medium' else 'low'}">{debt['risk_level'].upper()}</div></div>
<div class="card"><div class="label">Total Issues</div><div class="value">{result.total_issues}</div></div>
<div class="card"><div class="label">Files Scanned</div><div class="value">{result.files_scanned}</div></div>
<div class="card"><div class="label">Tech Debt</div><div class="value" style="font-size:1.2rem;">{debt['formatted']}</div></div>
</div>

<h2>Issues by Severity</h2>
<table>
<tr><th>Severity</th><th>Count</th></tr>
{"".join(f"<tr><td><span class='badge sev-{s}'>{s.upper()}</span></td><td>{result.issues_by_severity.get(s, 0)}</td></tr>" for s in ['critical','high','medium','low','info'])}
</table>

<h2>Top Problem Files</h2>
<table>
<tr><th>File</th><th>Issues</th><th>Risk Score</th></tr>
{file_rows}
</table>

<h2>All Issues ({result.total_issues})</h2>
<table>
<tr><th>Severity</th><th>Rule</th><th>Category</th><th>Location</th><th>Message</th></tr>
{issue_rows}
</table>

</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path

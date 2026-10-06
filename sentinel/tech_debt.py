"""Technical debt estimation and quality scoring."""
from sentinel.models import ScanResult, Severity, Category


def compute_tech_debt(result: ScanResult) -> dict:
    """
    Estimate technical debt based on scan results.

    Returns a dict with:
    - total_debt_minutes: estimated minutes to fix all issues
    - debt_by_severity: minutes per severity level
    - quality_score: 0-100 overall quality score
    - grade: A-F letter grade
    - risk_level: low/medium/high/critical
    - breakdown: detailed breakdown
    """
    # Estimate fix time per severity (minutes)
    fix_minutes = {
        Severity.CRITICAL: 120,
        Severity.HIGH: 60,
        Severity.MEDIUM: 20,
        Severity.LOW: 5,
        Severity.INFO: 1,
    }

    debt_by_severity = {}
    total_minutes = 0
    for sev, count in result.issues_by_severity.items():
        sev_enum = Severity(sev)
        minutes = count * fix_minutes[sev_enum]
        debt_by_severity[sev] = minutes
        total_minutes += minutes

    # Add complexity debt
    complexity_minutes = 0
    for stats in result.file_stats.values():
        if stats.max_complexity > 10:
            complexity_minutes += (stats.max_complexity - 10) * 10
    debt_by_severity["complexity"] = complexity_minutes
    total_minutes += complexity_minutes

    # Add duplicate debt
    dup_minutes = len(result.duplicates) * 30
    debt_by_severity["duplicates"] = dup_minutes
    total_minutes += dup_minutes

    # Quality score (0-100, higher is better)
    total_code_lines = sum(s.code_lines for s in result.file_stats.values())
    if total_code_lines == 0:
        quality_score = 100
    else:
        # Issues per 1000 lines
        issues_per_kloc = (result.total_issues / total_code_lines) * 1000
        # Base score, penalized by issue density and severity
        severity_penalty = sum(
            result.issues_by_severity.get(s.value, 0) * s.weight
            for s in Severity
        )
        penalty = min(issues_per_kloc * 2 + severity_penalty * 0.01, 90)
        quality_score = max(0, 100 - penalty)

    # Letter grade
    if quality_score >= 90:
        grade = "A"
    elif quality_score >= 80:
        grade = "B"
    elif quality_score >= 70:
        grade = "C"
    elif quality_score >= 60:
        grade = "D"
    else:
        grade = "F"

    # Risk level
    critical_count = result.issues_by_severity.get("critical", 0)
    high_count = result.issues_by_severity.get("high", 0)
    if critical_count > 0 or quality_score < 40:
        risk_level = "critical"
    elif high_count > 3 or quality_score < 60:
        risk_level = "high"
    elif quality_score < 80:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Format time
    hours = total_minutes // 60
    minutes = total_minutes % 60
    days = hours // 8
    hours_remaining = hours % 8

    return {
        "total_debt_minutes": total_minutes,
        "total_debt_hours": round(total_minutes / 60, 1),
        "total_debt_days": round(total_minutes / 480, 1),
        "formatted": f"{days}d {hours_remaining}h {minutes}m" if days > 0 else f"{hours}h {minutes}m",
        "debt_by_severity": debt_by_severity,
        "quality_score": round(quality_score, 1),
        "grade": grade,
        "risk_level": risk_level,
        "issues_per_kloc": round((result.total_issues / total_code_lines) * 1000, 2) if total_code_lines > 0 else 0,
        "total_code_lines": total_code_lines,
        "breakdown": {
            "security_issues": result.issues_by_category.get("security", 0),
            "bug_issues": result.issues_by_category.get("bug", 0),
            "complexity_issues": result.issues_by_category.get("complexity", 0),
            "style_issues": result.issues_by_category.get("style", 0),
            "duplicate_blocks": len(result.duplicates),
            "files_with_issues": result.files_with_issues,
            "files_scanned": result.files_scanned,
        },
    }


def generate_summary(result: ScanResult) -> str:
    """Generate a human-readable summary of scan results."""
    debt = compute_tech_debt(result)
    lines = []
    lines.append("=" * 60)
    lines.append("  SENTINEL — Code Security & Quality Report")
    lines.append("=" * 60)
    lines.append(f"  Target:    {result.target_path}")
    lines.append(f"  Files:     {result.files_scanned} scanned, {result.files_with_issues} with issues")
    lines.append(f"  Issues:    {result.total_issues} total")
    lines.append(f"  Quality:   {debt['quality_score']}/100 (Grade {debt['grade']})")
    lines.append(f"  Risk:      {debt['risk_level'].upper()}")
    lines.append(f"  Tech Debt: {debt['formatted']}")
    lines.append(f"  Scan time: {result.scan_time:.2f}s")
    lines.append("")

    # Severity breakdown
    lines.append("  Issues by Severity:")
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = result.issues_by_severity.get(sev, 0)
        if count > 0:
            bar = "█" * min(count, 40)
            lines.append(f"    {sev.upper():10s} {count:5d}  {bar}")
    lines.append("")

    # Category breakdown
    lines.append("  Issues by Category:")
    for cat, count in sorted(result.issues_by_category.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            lines.append(f"    {cat:18s} {count:5d}")
    lines.append("")

    # Top files
    top_files = result.get_top_files(5)
    if top_files:
        lines.append("  Top Problem Files:")
        for path, score, count in top_files:
            lines.append(f"    {path}")
            lines.append(f"      {count} issues, risk score {score:.0f}")
    lines.append("")

    # Most common rules
    top_rules = sorted(result.issues_by_rule.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_rules:
        lines.append("  Most Common Issues:")
        for rule, count in top_rules:
            lines.append(f"    {rule}: {count}")

    lines.append("=" * 60)
    return "\n".join(lines)

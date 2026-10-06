# Sentinel Examples

## Basic Usage

### Scan a project and view text report
```bash
sentinel scan /path/to/project
```

### Export to different formats
```bash
# HTML report (open in browser)
sentinel scan -o report.html /path/to/project

# Markdown report
sentinel scan -o report.md /path/to/project

# JSON for CI/CD integration
sentinel scan -o report.json /path/to/project
```

### Start interactive dashboard
```bash
sentinel serve /path/to/project --port 8765
# Open http://127.0.0.1:8765
```

### Filter by severity
```bash
# Only show critical and high issues
sentinel scan --min-severity high /path/to/project
```

### Exclude directories
```bash
sentinel scan --exclude tests/ --exclude vendor/ /path/to/project
```

## CI Integration

```yaml
# .github/workflows/sentinel.yml
name: Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install sentinel-scan
      - run: sentinel scan . --min-severity high
```

## Programmatic Usage

```python
from sentinel.scanner import scan_path
from sentinel.tech_debt import compute_tech_debt, generate_summary
from sentinel.report import export_to_json

# Scan
result = scan_path("/path/to/project")

# Access results
print(f"Files: {result.files_scanned}")
print(f"Issues: {result.total_issues}")
print(f"Quality: {compute_tech_debt(result)['quality_score']}")

# Print summary
print(generate_summary(result))

# Export
export_to_json(result, "report.json")
```

## Adding Custom Rules

```python
from sentinel.models import Severity, Category
from sentinel.rules.base import Rule, RuleRegistry

@RuleRegistry.register
class MyRule(Rule):
    rule_id = "CUS001"
    rule_name = "My Custom Check"
    category = Category.SECURITY
    severity = Severity.HIGH
    description = "Detects my custom pattern."

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            if "my_pattern" in line:
                issues.append(self.make_issue(
                    "Found my pattern", file_path, line=i,
                    suggestion="Replace with safe alternative.",
                ))
        return issues
```

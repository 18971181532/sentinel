# Sentinel — Code Security & Quality Scanner

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-orange.svg)](#)

**Sentinel** is a zero-dependency, pure-Python static code analysis tool that scans your codebase for security vulnerabilities, bugs, code smells, complexity issues, and duplicate code — then visualizes everything in an interactive dashboard.

## Features

### 🔒 Security Scanning
- Hardcoded secrets (passwords, API keys, AWS keys, GitHub tokens, JWTs)
- SQL injection detection (string concatenation, f-strings in queries)
- Command injection (`shell=True`, `eval()`, `exec()`)
- Insecure deserialization (`pickle.loads`, unsafe `yaml.load`)
- Weak cryptography (MD5, SHA1, DES, RC4, non-crypto random)
- Hardcoded endpoints and IP addresses

### 🐛 Bug Pattern Detection
- Bare `except:` clauses
- Mutable default arguments (`def f(x=[])`)
- `== None` instead of `is None`
- Broad `except Exception` catches
- TODO/FIXME/HACK comment markers
- Print statements in production code
- Potentially unused imports

### 📊 Complexity Analysis
- Cyclomatic complexity per function (AST-based)
- Function length detection
- Deep nesting detection
- Too many parameters
- File size warnings

### 📝 Code Style
- Line length violations
- Trailing whitespace
- Mixed tabs/spaces indentation
- Missing docstrings
- Non-snake_case function names

### 🔄 Duplicate Code Detection
- Cross-file duplicate block detection
- Normalized line hashing (strings/numbers abstracted)
- Configurable minimum block size

### 💰 Technical Debt Estimation
- Time-to-fix estimation by severity
- Quality score (0-100) with letter grade (A-F)
- Risk level classification (low/medium/high/critical)
- Issues per KLOC density metric
- Detailed breakdown by category

### 🎨 Interactive Web Dashboard
- **Overview** — quality score, grade, risk, stats cards, severity donut, category bar chart, top problem files
- **Issues** — filterable/searchable issue table with severity badges
- **Files** — bubble packing visualization of file risk + detailed table
- **Security** — security-focused view with rule breakdown and fix suggestions
- **Complexity** — complexity distribution, lines-vs-functions scatter, per-file table
- **Duplicates** — duplicate code blocks with source locations
- **Tech Debt** — hero metrics, debt by severity, quality breakdown, issue density chart

### 📤 Multi-Format Export
- JSON (machine-readable)
- Markdown (readable report)
- HTML (standalone styled report)

## Installation

```bash
pip install -e .
```

Or run directly without installation:

```bash
python -m sentinel scan /path/to/code
```

## Quick Start

### Scan a directory
```bash
sentinel scan /path/to/your/project
```

### Scan with JSON output
```bash
sentinel scan --json /path/to/project
```

### Export report
```bash
sentinel scan -o report.html /path/to/project
sentinel scan -o report.md /path/to/project
sentinel scan -o report.json /path/to/project
```

### Start web dashboard
```bash
sentinel serve /path/to/project --port 8765
# Open http://127.0.0.1:8765
```

### List all rules
```bash
sentinel rules
sentinel rules --category security
```

## CLI Reference

```
sentinel scan [PATH] [OPTIONS]
  --json              Output as JSON
  -o, --output FILE   Write report to file
  --format FORMAT     Output format (text/json/markdown/html)
  --min-severity LEVEL  Minimum severity (critical/high/medium/low/info)
  --exclude PATTERN   Exclude paths containing PATTERN
  --no-fail           Always exit 0

sentinel rules [--category CATEGORY]

sentinel serve [PATH] [--port PORT] [--host HOST]
```

## Rule Catalog

| ID | Rule | Category | Default Severity |
|----|------|----------|-----------------|
| SEC001 | Hardcoded Secrets | Security | Critical |
| SEC002 | SQL Injection | Security | High |
| SEC003 | Command Injection | Security | High |
| SEC004 | Insecure Deserialization | Security | High |
| SEC005 | Weak Cryptography | Security | Medium |
| SEC006 | Hardcoded Endpoints | Security | Low |
| BUG001 | Bare Except | Bug | Medium |
| BUG002 | Mutable Default Arg | Bug | High |
| BUG003 | Comparison with None | Bug | Low |
| BUG004 | Unused Import | Maintainability | Info |
| BUG005 | Print in Production | Maintainability | Info |
| BUG006 | TODO/FIXME Comments | Maintainability | Info |
| BUG007 | Broad Exception Catch | Bug | Low |
| CPX001 | High Cyclomatic Complexity | Complexity | Medium |
| CPX002 | Long Function | Complexity | Low |
| CPX003 | Deep Nesting | Complexity | Medium |
| CPX004 | Too Many Arguments | Complexity | Low |
| CPX005 | File Too Large | Complexity | Low |
| STY001 | Line Too Long | Style | Info |
| STY002 | Trailing Whitespace | Style | Info |
| STY003 | Mixed Indentation | Style | Low |
| STY004 | Missing Docstring | Style | Info |
| STY005 | Non-snake_case | Style | Info |
| DUP001 | Duplicate Code | Duplicate | Low |

## Architecture

```
sentinel/
├── __init__.py          # Package metadata
├── __main__.py          # python -m sentinel entry
├── models.py            # Data models (Issue, FileStats, ScanResult, Severity, Category)
├── scanner.py           # Main orchestrator (file walking, rule dispatch, aggregation)
├── cli.py               # Command-line interface
├── server.py            # HTTP server + REST API
├── tech_debt.py         # Technical debt estimation & quality scoring
├── report.py            # JSON/Markdown/HTML report generation
├── rules/
│   ├── base.py          # Rule base class & registry
│   ├── security.py      # Security rules (6 rules)
│   ├── bugs.py          # Bug pattern rules (7 rules)
│   ├── complexity.py    # Complexity rules (5 rules)
│   ├── style.py         # Style rules (5 rules)
│   └── duplicates.py    # Duplicate code detection
├── analyzers/
│   ├── python_analyzer.py   # Python AST analysis
│   └── generic_analyzer.py  # Multi-language text analysis (30+ languages)
└── web/
    ├── index.html       # Dashboard HTML
    ├── style.css        # Dark theme styles
    └── app.js           # Canvas 2D visualizations (zero dependencies)
```

## Design Principles

- **Zero dependencies** — pure Python standard library only. No pip installs required.
- **Extensible rule engine** — add new rules by subclassing `Rule` and decorating with `@RuleRegistry.register`.
- **Multi-language** — Python gets AST-level analysis; 30+ other languages get heuristic-based analysis.
- **Fast** — concurrent file processing, incremental caching in the web server.
- **Privacy-first** — all analysis runs locally; no data ever leaves your machine.

## Extending Sentinel

### Adding a new rule

```python
from sentinel.models import Severity, Category, FileStats
from sentinel.rules.base import Rule, RuleRegistry

@RuleRegistry.register
class MyCustomRule(Rule):
    rule_id = "CUS001"
    rule_name = "My Custom Check"
    category = Category.SECURITY
    severity = Severity.HIGH
    description = "Detects custom security issues."
    languages = ["python"]  # empty = all languages

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            if "dangerous_pattern" in line:
                issues.append(self.make_issue(
                    "Dangerous pattern detected",
                    file_path, line=i,
                    snippet=line.strip(),
                    suggestion="Use safe_pattern instead.",
                ))
        return issues
```

## CI Integration

Sentinel exits with code 1 when critical or high severity issues are found, making it suitable for CI pipelines:

```yaml
- name: Run Sentinel
  run: |
    pip install -e .
    sentinel scan .
```

Use `--no-fail` to run in advisory mode without blocking the build.

## License

MIT License — see [LICENSE](LICENSE) for details.

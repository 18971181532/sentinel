"""Security-focused rules."""
import re
from sentinel.models import Severity, Category, FileStats
from sentinel.rules.base import Rule, RuleRegistry


# ── Hardcoded Secrets ──────────────────────────────────────────────

SECRET_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']',
     "Hardcoded password detected", Severity.CRITICAL),
    (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*["\'][A-Za-z0-9_\-]{8,}["\']',
     "Hardcoded API key or token detected", Severity.CRITICAL),
    (r'(?i)(private[_-]?key|secret)\s*[:=]\s*["\']-----BEGIN',
     "Hardcoded private key detected", Severity.CRITICAL),
    (r'AKIA[0-9A-Z]{16}', "AWS access key ID detected", Severity.CRITICAL),
    (r'gh[pousr]_[A-Za-z0-9]{36}', "GitHub token detected", Severity.CRITICAL),
    (r'sk_[A-Za-z0-9]{20,}', "API secret key detected", Severity.CRITICAL),
    (r'(?i)(db[_-]?url|database[_-]?url|connection[_-]?string)\s*[:=]\s*["\'][^"\']*:[^"\']*@',
     "Database connection string with credentials detected", Severity.HIGH),
    (r'(?i)(jwt|json[_-]web[_-]?token)\s*[:=]\s*["\']eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+["\']',
     "Hardcoded JWT token detected", Severity.HIGH),
]


@RuleRegistry.register
class HardcodedSecretsRule(Rule):
    rule_id = "SEC001"
    rule_name = "Hardcoded Secrets"
    category = Category.SECURITY
    severity = Severity.CRITICAL
    description = "Detects hardcoded passwords, API keys, tokens, and private keys."

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            for pattern, msg, sev in SECRET_PATTERNS:
                if re.search(pattern, line):
                    issues.append(self.make_issue(
                        msg, file_path, line=i, snippet=line.strip()[:120],
                        suggestion="Move secrets to environment variables or a secure vault.",
                        severity=sev, confidence=0.9,
                    ))
                    break
        return issues


# ── SQL Injection ───────────────────────────────────────────────────

SQL_INJECTION_PATTERNS = [
    (r'(?i)(execute|cursor\.execute|db\.query)\s*\(\s*["\'][^"\']*["\']\s*\+',
     "SQL query built with string concatenation — possible SQL injection"),
    (r'(?i)(execute|cursor\.execute)\s*\(\s*f["\']',
     "SQL query built with f-string — possible SQL injection"),
    (r'(?i)(execute|cursor\.execute)\s*\(\s*["\'][^"\']*%\s*\(.*\)',
     "SQL query built with % formatting — possible SQL injection"),
    (r'(?i)SELECT.*FROM.*\+\s*\w+', "Dynamic SQL with concatenation — possible SQL injection"),
]


@RuleRegistry.register
class SQLInjectionRule(Rule):
    rule_id = "SEC002"
    rule_name = "SQL Injection"
    category = Category.SECURITY
    severity = Severity.HIGH
    description = "Detects potential SQL injection via string concatenation in queries."

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            for pattern, msg in SQL_INJECTION_PATTERNS:
                if re.search(pattern, line):
                    issues.append(self.make_issue(
                        msg, file_path, line=i, snippet=line.strip()[:120],
                        suggestion="Use parameterized queries (e.g., execute('SELECT * WHERE id = ?', (id,))).",
                        confidence=0.7,
                    ))
                    break
        return issues


# ── Command Injection ───────────────────────────────────────────────

CMD_INJECTION_PATTERNS = [
    (r'(?i)(os\.system|subprocess\.(call|run|Popen))\s*\(\s*["\']?[^"\']*["\']?\s*\+',
     "Shell command built with concatenation — possible command injection"),
    (r'(?i)(os\.system|subprocess\.(call|run))\s*\(\s*f["\']',
     "Shell command built with f-string — possible command injection"),
    (r'(?i)shell\s*=\s*True', "shell=True enables command injection risks"),
    (r'(?i)eval\s*\(', "Use of eval() — potential code injection"),
    (r'(?i)exec\s*\(', "Use of exec() — potential code injection"),
]


@RuleRegistry.register
class CommandInjectionRule(Rule):
    rule_id = "SEC003"
    rule_name = "Command Injection"
    category = Category.SECURITY
    severity = Severity.HIGH
    description = "Detects potential command injection via shell=True, eval, exec, and string-built commands."

    def check(self, content, file_path, stats):
        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            for pattern, msg in CMD_INJECTION_PATTERNS:
                if re.search(pattern, line):
                    sev = Severity.CRITICAL if "eval" in pattern or "exec" in pattern else Severity.HIGH
                    issues.append(self.make_issue(
                        msg, file_path, line=i, snippet=line.strip()[:120],
                        suggestion="Use subprocess with argument lists and shell=False. Avoid eval/exec on untrusted input.",
                        severity=sev, confidence=0.8,
                    ))
                    break
        return issues


# ── Insecure Deserialization ────────────────────────────────────────

@RuleRegistry.register
class InsecureDeserializationRule(Rule):
    rule_id = "SEC004"
    rule_name = "Insecure Deserialization"
    category = Category.SECURITY
    severity = Severity.HIGH
    description = "Detects unsafe deserialization of untrusted data."

    def check(self, content, file_path, stats):
        issues = []
        patterns = [
            (r'(?i)pickle\.loads?\s*\(', "pickle.load(s) on untrusted data — arbitrary code execution risk"),
            (r'(?i)yaml\.load\s*\([^)]*\)(?!.*Loader)', "yaml.load without SafeLoader — arbitrary code execution risk"),
            (r'(?i)marshal\.loads?\s*\(', "marshal.load(s) — unsafe for untrusted data"),
            (r'(?i)shelve\.open\s*\(', "shelve.open — unsafe for untrusted data"),
        ]
        for i, line in enumerate(content.split("\n"), 1):
            for pattern, msg in patterns:
                if re.search(pattern, line):
                    issues.append(self.make_issue(
                        msg, file_path, line=i, snippet=line.strip()[:120],
                        suggestion="Use json for untrusted data, or yaml.safe_load. Never deserialize untrusted pickled data.",
                        confidence=0.85,
                    ))
                    break
        return issues


# ── Weak Cryptography ───────────────────────────────────────────────

@RuleRegistry.register
class WeakCryptoRule(Rule):
    rule_id = "SEC005"
    rule_name = "Weak Cryptography"
    category = Category.SECURITY
    severity = Severity.MEDIUM
    description = "Detects use of weak or broken cryptographic algorithms."

    def check(self, content, file_path, stats):
        issues = []
        patterns = [
            (r'(?i)(hashlib\.)?md5\s*\(', "MD5 is cryptographically broken"),
            (r'(?i)(hashlib\.)?sha1\s*\(', "SHA1 is considered weak for security purposes"),
            (r'(?i)DES\b', "DES is insecure and broken"),
            (r'(?i)RC4\b', "RC4 is insecure and broken"),
            (r'(?i)random\.random\s*\(\)', "random.random() is not cryptographically secure — use secrets module"),
            (r'(?i)random\.randint\s*\(', "random.randint() is not cryptographically secure — use secrets module"),
        ]
        for i, line in enumerate(content.split("\n"), 1):
            for pattern, msg in patterns:
                if re.search(pattern, line):
                    sev = Severity.HIGH if "md5" in pattern.lower() or "des" in pattern.lower() else Severity.MEDIUM
                    issues.append(self.make_issue(
                        msg, file_path, line=i, snippet=line.strip()[:120],
                        suggestion="Use SHA-256 or stronger for hashing, AES for encryption, and secrets module for random values.",
                        severity=sev, confidence=0.75,
                    ))
                    break
        return issues


# ── Hardcoded URLs / IPs ────────────────────────────────────────────

@RuleRegistry.register
class HardcodedEndpointRule(Rule):
    rule_id = "SEC006"
    rule_name = "Hardcoded Endpoints"
    category = Category.SECURITY
    severity = Severity.LOW
    description = "Detects hardcoded URLs and IP addresses that should be configurable."

    def check(self, content, file_path, stats):
        issues = []
        url_pattern = re.compile(r'["\']https?://(?:\d{1,3}\.){3}\d{1,3}[:/]?[^"\']*["\']')
        ip_pattern = re.compile(r'["\'](?:\d{1,3}\.){3}\d{1,3}["\']')
        for i, line in enumerate(content.split("\n"), 1):
            if url_pattern.search(line) or ip_pattern.search(line):
                issues.append(self.make_issue(
                    "Hardcoded IP address or URL — should be configurable",
                    file_path, line=i, snippet=line.strip()[:120],
                    suggestion="Move endpoints to configuration or environment variables.",
                    confidence=0.6,
                ))
        return issues

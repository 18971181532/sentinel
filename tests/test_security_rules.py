"""Tests for security rules."""
import unittest
from sentinel.models import FileStats, Severity
from sentinel.rules.security import (
    HardcodedSecretsRule, SQLInjectionRule, CommandInjectionRule,
    InsecureDeserializationRule, WeakCryptoRule, HardcodedEndpointRule,
)
from tests.helpers import SAMPLE_PYTHON_WITH_ISSUES


class TestHardcodedSecrets(unittest.TestCase):
    def setUp(self):
        self.rule = HardcodedSecretsRule()

    def test_detects_password(self):
        content = 'password = "mysecret123"\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertTrue(any("password" in i.message.lower() for i in issues))

    def test_detects_api_key(self):
        content = 'api_key = "sk-1234567890abcdefghij"\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertTrue(any("api key" in i.message.lower() or "token" in i.message.lower() for i in issues))

    def test_detects_aws_key(self):
        content = 'key = "AKIAIOSFODNN7EXAMPLE"\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertTrue(any("aws" in i.message.lower() for i in issues))

    def test_no_false_positive(self):
        content = 'username = "admin"\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)

    def test_sample_file(self):
        issues = self.rule.check(SAMPLE_PYTHON_WITH_ISSUES, "sample.py",
                                  FileStats(path="sample.py", language="python"))
        self.assertGreater(len(issues), 0)


class TestSQLInjection(unittest.TestCase):
    def setUp(self):
        self.rule = SQLInjectionRule()

    def test_concatenation(self):
        content = 'db.execute("SELECT * FROM t WHERE id = " + user_id)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_f_string(self):
        content = 'cursor.execute(f"SELECT * FROM t WHERE id = {user_id}")\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_parameterized_query_safe(self):
        content = 'db.execute("SELECT * FROM t WHERE id = ?", (user_id,))\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestCommandInjection(unittest.TestCase):
    def setUp(self):
        self.rule = CommandInjectionRule()

    def test_os_system_concat(self):
        content = 'os.system("ls " + path)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_eval(self):
        content = 'result = eval(user_input)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertTrue(any("eval" in i.message.lower() for i in issues))

    def test_exec(self):
        content = 'exec(code)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertTrue(any("exec" in i.message.lower() for i in issues))

    def test_shell_true(self):
        content = 'subprocess.run(cmd, shell=True)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)


class TestInsecureDeserialization(unittest.TestCase):
    def setUp(self):
        self.rule = InsecureDeserializationRule()

    def test_pickle_loads(self):
        content = 'data = pickle.loads(raw_data)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_yaml_load_without_safe(self):
        content = 'data = yaml.load(raw)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_yaml_safe_load_ok(self):
        content = 'data = yaml.safe_load(raw)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestWeakCrypto(unittest.TestCase):
    def setUp(self):
        self.rule = WeakCryptoRule()

    def test_md5(self):
        content = 'h = hashlib.md5(data)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_sha1(self):
        content = 'h = hashlib.sha1(data)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_random_not_secure(self):
        content = 'x = random.random()\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)

    def test_sha256_ok(self):
        content = 'h = hashlib.sha256(data)\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertEqual(len(issues), 0)


class TestHardcodedEndpoint(unittest.TestCase):
    def setUp(self):
        self.rule = HardcodedEndpointRule()

    def test_hardcoded_ip(self):
        content = 'url = "http://192.168.1.1/api"\n'
        issues = self.rule.check(content, "test.py", FileStats(path="test.py", language="python"))
        self.assertGreater(len(issues), 0)


if __name__ == "__main__":
    unittest.main()

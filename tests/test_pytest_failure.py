"""Decorated test failures pass through the actual read-only source boundary."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from shake_bake.failure_service import run_failure_location
from shake_bake.troubleshoot import locate_failure


BANNER = " FAILURES ".center(79, "=")


def heading(name):
    return f" {name} ".center(79, "_")


def failure(path="counts.py", statement="return int(value)"):
    return (BANNER + "\n" + heading("test_count") + "\n\n"
            "    def total(value):\n>       " + statement + "\n"
            "E       ValueError: invalid literal for int() with base 10: 'many'\n\n"
            + path + ":2: ValueError\n")


class PytestSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="sb-pytest-source-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = "def total(value):\n    return int(value)\n"
        (self.root / "counts.py").write_bytes(self.source.encode())

    def test_decorated_error_captures_exact_current_source_and_original_input(self):
        raw = "\ufeff" + failure().replace("\n", "\r\n")
        result = locate_failure(self.root, raw, "python -m pytest -q")
        self.assertEqual(result["format"], "pytest")
        self.assertEqual(result["frames"][0]["source_comparison"], "match")
        self.assertEqual(result["terminal_exception"]["type"], "ValueError")
        self.assertEqual(result["innermost_project_frame"], "F1")
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["error_sha256"], hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(result["evidence"][0]["text"], self.source)
        self.assertEqual(result["evidence"][0]["file_sha256"], hashlib.sha256(self.source.encode()).hexdigest())

    def test_final_test_outside_project_does_not_borrow_earlier_source(self):
        raw = failure() + heading("test_other") + "\n\n>       assert 2 == 3\nE       assert 2 == 3\n\n/outside/test_other.py:7: AssertionError\n"
        result = locate_failure(self.root, raw)
        self.assertTrue(result["source_located"])
        self.assertIsNone(result["innermost_project_frame"])
        self.assertEqual(result["terminal_exception"]["type"], "AssertionError")
        self.assertEqual([frame["status"] for frame in result["frames"]], ["located", "outside_project"])
        self.assertEqual(result["chain_relations"], [])

    def test_captured_python_traceback_is_not_treated_as_the_failure(self):
        (self.root / "spoof.py").write_text("raise PermissionError('captured output')\n")
        captured = (" Captured stdout call ".center(79, "-") + "\n"
                    'Traceback (most recent call last):\n  File "spoof.py", line 1\n'
                    "    raise PermissionError('captured output')\nPermissionError: captured output\n")
        result = locate_failure(self.root, failure() + captured)
        self.assertEqual(result["format"], "pytest")
        self.assertEqual(result["terminal_exception"]["type"], "ValueError")
        self.assertEqual([frame["reported_path"] for frame in result["frames"]], ["counts.py"])
        self.assertEqual([item["path"] for item in result["evidence"]], ["counts.py"])

    def test_unfinished_final_test_remains_incomplete(self):
        raw = failure() + heading("test_interrupted") + "\n\n"
        result = locate_failure(self.root, raw)
        self.assertIsNone(result["innermost_project_frame"])
        self.assertIsNone(result["terminal_exception"])
        self.assertIn("pytest_incomplete_case", result["cutoffs"])

    def test_owned_service_preserves_the_decorated_report_without_running_command(self):
        raw = failure(statement="return missing")
        result = run_failure_location(self.root, raw, "DO NOT EXECUTE THIS COMMAND", scratch=self.root)
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["command"], "DO NOT EXECUTE THIS COMMAND")
        self.assertEqual(result["frames"][0]["source_comparison"], "mismatch")
        self.assertEqual(result["evidence"][0]["text"], self.source)
        self.assertEqual((self.root / "counts.py").read_text(), self.source)


if __name__ == "__main__":
    unittest.main()

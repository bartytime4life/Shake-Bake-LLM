"""Synthetic credential shapes in failed-run handoffs; exact evidence stays intact."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.gui import Controller
from shake_bake.screening import MAX_FINDINGS, screen_failure, warning_lines
from shake_bake.troubleshoot import locate_failure


# Assemble inert shapes at runtime; no literal credential is retained in source.
AWS = "AK" + "IA" + "Q7" * 8
GITHUB = "gh" + "p_" + "a" * 36
SLACK = "xo" + "xb-" + "1234567890-abcdefghij"


class FailureScreeningTests(unittest.TestCase):
    def test_legacy_three_argument_screening_remains_bounded_and_compatible(self):
        findings = screen_failure("Error: " + AWS, "launch " + GITHUB, [])
        self.assertEqual([(item["where"], item["line"]) for item in findings], [("error output", 1), ("command", None)])
        with patch("shake_bake.screening._scan", side_effect=lambda text: iter(
                [("synthetic", 1, "masked")] * 100)):
            self.assertEqual(len(screen_failure("log", "command", [])), MAX_FINDINGS)

    def test_log_command_source_and_project_fields_are_masked_without_rewriting(self):
        report = {
            "format": "python", "command": "launch " + SLACK,
            "error_output": "first\r\nsecond\rValueError: " + GITHUB + "\r",
            "project": {"id": GITHUB, "label": SLACK, "path": "/chosen/" + AWS},
            "evidence": [{"evidence_id": "E1", "path": "app.py", "start_line": 8,
                          "text": "first\r\nsecond\r# " + AWS + "\r"}],
        }
        original = deepcopy(report)
        findings = screen_failure(report)
        self.assertEqual(report, original)
        self.assertEqual([item["where"] for item in findings], [
            "project id", "project name", "project folder", "recorded command", "original error output", "E1"])
        self.assertEqual([item["line"] for item in findings], [None, None, None, 1, 3, 10])
        self.assertEqual(findings[-1]["path"], "app.py")
        rendered = str(findings) + "\n".join(warning_lines(findings))
        for value in (AWS, GITHUB, SLACK):
            self.assertNotIn(value, rendered)
        self.assertIn("Possible credentials", rendered)

    def test_source_positions_use_python_or_ecmascript_line_rules(self):
        text = "first\u2028second\u2029third\funchanged\vunchanged\r\n# " + AWS
        for format_name, line in (("python", 8), ("node", 10), ("typescript", 10)):
            with self.subTest(format_name=format_name):
                report = {"format": format_name, "evidence": [
                    {"evidence_id": "E2", "path": "source", "start_line": 7, "text": text}]}
                self.assertEqual(screen_failure(report)[0]["line"], line)
                self.assertEqual(report["evidence"][0]["text"], text)

    def test_cap_stops_consuming_matches_instead_of_building_an_unbounded_list(self):
        def matches(text):
            for number in range(MAX_FINDINGS):
                yield "synthetic", number + 1, "masked"
            raise AssertionError("the bounded scan must stop consuming after its cap")

        with patch("shake_bake.screening._scan", matches):
            findings = screen_failure({"error_output": "synthetic log"})
        self.assertEqual(len(findings), MAX_FINDINGS)

    def test_many_matches_and_placeholders_remain_warn_only(self):
        self.assertEqual(len(screen_failure({"error_output": "\n".join([AWS] * 1000)})), MAX_FINDINGS)
        self.assertEqual(screen_failure({"command": 'password = "changeme"',
                                         "error_output": "ValueError: ordinary failure", "evidence": []}), [])

    def test_locator_screens_all_captured_content_and_keeps_original_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = "def run():\r\n    raise ValueError('bad')\r\n# " + AWS + "\r\n"
            (root / "app.py").write_bytes(source.encode("utf-8"))
            output = ('Traceback (most recent call last):\r\n  File "app.py", line 2, in run\r\n'
                      "    raise ValueError('bad')\r\nValueError: " + GITHUB + "\r\n")
            command = "launch " + SLACK
            result = locate_failure(root, output, command)
            self.assertEqual(result["error_output"], output)
            self.assertEqual(result["command"], command)
            self.assertEqual(result["evidence"][0]["text"], source)
            self.assertEqual((root / "app.py").read_bytes(), source.encode("utf-8"))
            self.assertEqual([item["where"] for item in result["screening"]], [
                "recorded command", "original error output", "E1"])
            self.assertEqual(result["screening"][-1]["line"], 3)

    def test_controller_rescreens_server_bound_project_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / AWS
            root.mkdir()
            controller = Controller({GITHUB: root})
            try:
                controller.project_labels[GITHUB] = SLACK
                result = controller.call("troubleshoot", {"project_id": GITHUB,
                    "error_output": "ValueError: ordinary failure\r\n", "command": ""})
                self.assertEqual(result["project"], {"id": GITHUB, "label": SLACK, "path": str(root)})
                self.assertEqual([item["where"] for item in result["screening"]], [
                    "project id", "project name", "project folder"])
                self.assertEqual(result["error_output"], "ValueError: ordinary failure\r\n")
                self.assertNotIn(AWS, str(result["screening"]))
                self.assertNotIn(GITHUB, str(result["screening"]))
                self.assertNotIn(SLACK, str(result["screening"]))
            finally:
                controller.close()


if __name__ == "__main__":
    unittest.main()

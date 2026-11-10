"""Only an owner-selected run folder changes relative source lookup."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from shake_bake.contracts import Refusal
from shake_bake.failure_service import run_failure_location
from shake_bake.troubleshoot import locate_failure


def traceback(path="./counts.py"):
    return ('Traceback (most recent call last):\r\n'
            f'  File "{path}", line 2, in total\r\n'
            '    return int(value)\r\n'
            "ValueError: invalid literal for int() with base 10: 'many'\r\n")


class FailureWorkingDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="sb-run-directory-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.nested = self.root / "packages" / "count service"
        self.nested.mkdir(parents=True)
        self.root_source = "def total(value):\n    return value + 1\n"
        self.nested_source = "def total(value):\n    return int(value)\n"
        (self.root / "counts.py").write_text(self.root_source)
        (self.nested / "counts.py").write_text(self.nested_source)

    def test_explicit_subfolder_selects_nested_file_and_keeps_exact_inputs(self):
        raw = traceback()
        command = 'cd packages/other && python counts.py  # recorded only\r\n'
        supplied = "./packages/count service/"
        report = locate_failure(self.root, raw, command, working_directory=supplied)
        self.assertEqual(report["working_directory"], supplied)
        self.assertEqual(report["working_directory_path"], "packages/count service")
        self.assertEqual(report["error_output"], raw)
        self.assertEqual(report["error_sha256"], hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(report["command"], command)
        self.assertEqual(report["frames"][0]["reported_path"], "./counts.py")
        self.assertEqual(report["frames"][0]["path"], "packages/count service/counts.py")
        self.assertEqual(report["frames"][0]["source_comparison"], "match")
        self.assertEqual(report["evidence"][0]["text"], self.nested_source)

    def test_default_does_not_infer_directory_from_command_or_look_for_match(self):
        report = locate_failure(self.root, traceback(), "cd 'packages/count service' && python counts.py")
        self.assertEqual(report["working_directory"], "")
        self.assertEqual(report["working_directory_path"], ".")
        self.assertEqual(report["frames"][0]["path"], "counts.py")
        self.assertEqual(report["frames"][0]["source_comparison"], "mismatch")
        self.assertEqual(report["evidence"][0]["text"], self.root_source)

    def test_absolute_owner_directory_is_accepted_and_preserved(self):
        supplied = str(self.nested) + "/"
        report = locate_failure(self.root, traceback(), working_directory=supplied)
        self.assertEqual(report["working_directory"], supplied)
        self.assertEqual(report["working_directory_path"], "packages/count service")
        self.assertEqual(report["evidence"][0]["text"], self.nested_source)

    def test_explicit_root_spellings_remain_root(self):
        for supplied in ("", ".", "././", str(self.root), str(self.root) + "/"):
            with self.subTest(supplied=supplied):
                report = locate_failure(self.root, traceback(), working_directory=supplied)
                self.assertEqual(report["working_directory"], supplied)
                self.assertEqual(report["working_directory_path"], ".")
                self.assertEqual(report["evidence"][0]["path"], "counts.py")

    def test_absolute_reported_paths_keep_their_original_boundary(self):
        absolute = str(self.root / "counts.py")
        report = locate_failure(self.root, traceback(absolute), working_directory="packages/count service")
        self.assertEqual(report["frames"][0]["reported_path"], absolute)
        self.assertEqual(report["evidence"][0]["path"], "counts.py")
        self.assertEqual(report["evidence"][0]["text"], self.root_source)
        outside = locate_failure(self.root, traceback(str(self.root.parent / "counts.py")),
                                 working_directory="packages/count service")
        self.assertEqual(outside["frames"][0]["status"], "outside_project")
        self.assertEqual(outside["evidence"], [])

    def test_missing_relative_path_does_not_fall_back_to_root(self):
        (self.nested / "counts.py").unlink()
        report = locate_failure(self.root, traceback(), working_directory="packages/count service")
        self.assertEqual(report["frames"][0]["status"], "source_unavailable_or_not_allowed")
        self.assertEqual(report["evidence"], [])

    def test_node_typescript_and_pytest_relative_paths_share_the_explicit_base(self):
        (self.nested / "counts.js").write_text("throw new Error('failed');\n")
        (self.nested / "counts.ts").write_text("const total: number = 'many';\n")
        cases = [
            ("Error: failed\n    at total (counts.js:1:7)\n", "node", "counts.js"),
            ("counts.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'.\n", "typescript", "counts.ts"),
            (" FAILURES ".center(79, "=") + "\n" + " test_total ".center(79, "_")
             + "\n\n>       return int(value)\nE       ValueError: bad value\n\ncounts.py:2: ValueError\n", "pytest", "counts.py"),
        ]
        for raw, format_name, name in cases:
            with self.subTest(format=format_name):
                report = locate_failure(self.root, raw, working_directory="packages/count service")
                self.assertEqual(report["format"], format_name)
                self.assertEqual(report["frames"][0]["reported_path"], name)
                self.assertEqual(report["evidence"][0]["path"], "packages/count service/" + name)

    def assert_refused(self, supplied, expected):
        with self.assertRaises(Refusal) as caught:
            locate_failure(self.root, traceback(), working_directory=supplied)
        self.assertEqual(caught.exception.code, expected)

    def test_invalid_directory_input_is_refused(self):
        for supplied in (None, 3, [], {}, "a\x00b", "\ud800", "é" * 2049):
            with self.subTest(supplied=repr(supplied)):
                self.assert_refused(supplied, "invalid_failure_working_directory")

    def test_traversal_sensitive_excluded_and_control_paths_are_refused(self):
        for supplied in ("..", "packages/../packages", str(self.nested) + "/..", ".ssh", ".env.local",
                         "packages/.git", "node_modules", "packages/dist", "packages/venv",
                         "packages\\count service", "packages\ncount service", "file:packages"):
            with self.subTest(supplied=supplied):
                self.assert_refused(supplied, "working_directory_not_allowed")

    def test_outside_and_missing_directories_are_refused(self):
        self.assert_refused(str(self.root.parent), "working_directory_outside_project")
        self.assert_refused("missing", "working_directory_unavailable")
        self.assert_refused("counts.py", "working_directory_unavailable")

    def test_symlink_directory_components_are_refused_even_when_target_is_inside(self):
        (self.root / "linked").symlink_to(self.nested, target_is_directory=True)
        (self.nested / "linked").symlink_to(self.root, target_is_directory=True)
        for supplied in ("linked", "linked/child", "packages/count service/linked", str(self.root / "linked")):
            with self.subTest(supplied=supplied):
                self.assert_refused(supplied, "working_directory_not_allowed")

    def test_reported_traversal_is_still_refused_from_nested_directory(self):
        report = locate_failure(self.root, traceback("../../counts.py"), working_directory="packages/count service")
        self.assertEqual(report["frames"][0]["reported_path"], "../../counts.py")
        self.assertEqual(report["frames"][0]["status"], "path_not_allowed")
        self.assertEqual(report["evidence"], [])

    def test_owned_child_roundtrip_retains_exact_folder_error_and_command(self):
        raw = "\ufeff" + traceback()
        supplied = "./packages/count service/"
        command = "DO NOT EXECUTE; touch OWNED_COMMAND_RAN\r\n"
        report = run_failure_location(self.root, raw, command, working_directory=supplied, scratch=self.root)
        self.assertEqual(report["working_directory"], supplied)
        self.assertEqual(report["working_directory_path"], "packages/count service")
        self.assertEqual(report["error_output"], raw)
        self.assertEqual(report["command"], command)
        self.assertEqual(report["evidence"][0]["text"], self.nested_source)
        self.assertFalse((self.root / "OWNED_COMMAND_RAN").exists())

    def test_owned_child_rejects_unapproved_folder(self):
        with self.assertRaises(Refusal) as caught:
            run_failure_location(self.root, traceback(), "", working_directory="../", scratch=self.root)
        self.assertEqual(caught.exception.code, "working_directory_not_allowed")

    def test_earlier_owned_child_payload_without_folder_remains_supported(self):
        request = {"root": str(self.root), "error_output": traceback(), "command": "recorded only"}
        child = subprocess.run([sys.executable, "-B", "-m", "shake_bake.failure_runner", str(os.getpid())],
                               input=json.dumps(request).encode(), capture_output=True, timeout=5)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        report = json.loads(child.stdout)
        self.assertEqual(report["working_directory"], "")
        self.assertEqual(report["working_directory_path"], ".")
        self.assertEqual(report["evidence"][0]["text"], self.root_source)

    def test_cli_uses_the_selected_directory_without_executing_recorded_command(self):
        raw = "\ufeff" + traceback()
        error_file = self.root / "error.log"
        error_file.write_bytes(raw.encode("utf-8"))
        supplied = "./packages/count service/"
        command = "touch CLI_COMMAND_RAN"
        process = subprocess.run([sys.executable, "-B", "-m", "shake_bake", "diagnose", "--root", str(self.root),
                                  "--error-file", str(error_file), "--working-directory", supplied, "--command", command],
                                 capture_output=True, text=True, timeout=5)
        self.assertEqual(process.returncode, 0, process.stderr)
        report = json.loads(process.stdout)
        self.assertEqual(report["working_directory"], supplied)
        self.assertEqual(report["working_directory_path"], "packages/count service")
        self.assertEqual(report["error_output"], raw)
        self.assertEqual(report["command"], command)
        self.assertEqual(report["frames"][0]["source_comparison"], "match")
        self.assertFalse((self.root / "CLI_COMMAND_RAN").exists())


if __name__ == "__main__":
    unittest.main()

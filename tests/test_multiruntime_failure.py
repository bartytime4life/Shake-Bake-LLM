"""Synthetic runtime locations and exact source across supported formats."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.troubleshoot import locate_failure


class MultiruntimeFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sb-multiruntime-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source.encode("utf-8"))
        return path

    def test_node_first_project_frame_keeps_v8_order_and_exact_source(self):
        source = "function parse(value) {\n  return value.count;\n}\nparse(undefined);\n"
        path = self.write("src/count.js", source)
        raw = ("TypeError: Cannot read properties of undefined (reading 'count')\r\n"
               "    at internal (node:internal/task_queues:95:5)\r\n"
               f"    at parse ({path}:2:16)\r\n"
               f"    at {path}:4:1\r\n")
        result = locate_failure(self.root, raw, "node src/count.js")
        self.assertEqual(result["format"], "node")
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["frames"][0]["status"], "runtime_internal")
        self.assertEqual(result["innermost_project_frame"], "F2")
        self.assertEqual(result["frames"][1]["column"], 16)
        self.assertEqual(result["frames"][1]["source_comparison"], "unknown")
        self.assertEqual(result["evidence"][0]["text"], source)
        self.assertEqual(result["evidence"][0]["file_sha256"], hashlib.sha256(source.encode()).hexdigest())
        self.assertIn("first project frame", result["guidance"][0]["title"])

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_real_node_output_from_disposable_generated_input_is_located(self):
        # This test driver runs only its own generated fixture. The locator
        # receives text and must never execute the recorded command itself.
        source = "const marker = 1;\nthrow new Error('generated fixture failure');\n"
        path = self.write("generated runtime.mjs", source)
        run = subprocess.run([shutil.which("node"), str(path)], cwd=self.root,
                             capture_output=True, text=True, timeout=5)
        self.assertNotEqual(run.returncode, 0)
        result = locate_failure(self.root, run.stderr, "NOT EXECUTED BY LOCATOR")
        self.assertEqual(result["format"], "node")
        self.assertEqual(result["error_output"], run.stderr)
        frame = next(item for item in result["frames"] if item["frame_id"] == result["innermost_project_frame"])
        self.assertEqual((frame["path"], frame["line"]), (path.name, 2))
        self.assertEqual(result["terminal_exception"]["message"], "generated fixture failure")
        self.assertEqual(path.read_bytes(), source.encode())

    def test_typescript_binds_selected_source_to_its_own_diagnostic(self):
        self.write("src/count.ts", "const count: number = 'many';\n")
        raw = ("/outside/not-read.ts(4,2): error TS2304: Cannot find name 'outside'.\n"
               "src/count.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'.\n")
        result = locate_failure(self.root, raw)
        self.assertEqual(result["format"], "typescript")
        self.assertEqual(result["frames"][0]["status"], "outside_project")
        self.assertEqual(result["innermost_project_frame"], "F2")
        self.assertEqual(result["terminal_exception"]["type"], "TS2322")
        self.assertEqual(result["frames"][1]["column"], 7)
        self.assertEqual(result["error_output"], raw)

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_node_eof_keeps_reported_line_and_labels_preceding_context(self):
        source = "function incomplete() {\n"
        path = self.write("eof.js", source)
        run = subprocess.run([shutil.which("node"), str(path)], cwd=self.root,
                             capture_output=True, text=True, timeout=5)
        result = locate_failure(self.root, run.stderr)
        frame = next(item for item in result["frames"] if item["frame_id"] == result["innermost_project_frame"])
        self.assertEqual(frame["line"], 2)
        self.assertEqual(frame["context_line"], 1)
        self.assertEqual(frame["location_kind"], "end_of_file")
        self.assertEqual(result["error_output"], run.stderr)
        self.assertEqual(result["evidence"][0]["text"], source)
        self.assertEqual(result["evidence"][0]["end_line"], 1)

    def test_other_out_of_range_node_locations_remain_unlocated(self):
        self.write("main.js", "throw new TypeError('bad');\n")
        result = locate_failure(self.root, "TypeError: bad\n    at main.js:2:1\n")
        self.assertFalse(result["source_located"])
        self.assertEqual(result["frames"][0]["status"], "line_out_of_range")

    def test_eof_context_is_not_reused_as_an_out_of_range_stack_location(self):
        source = "function incomplete() {\n"
        path = self.write("main.js", source)
        # The distinct spellings identify one file, but only the caret-less
        # EOF header authorizes preceding context. The unrelated stack's
        # column-bearing claim still points beyond the stored source.
        for header_path, stack_path in ((str(path), "main.js"), ("main.js", str(path))):
            with self.subTest(header_path=header_path, stack_path=stack_path):
                raw = (f"{header_path}:2\n\n\n\nSyntaxError: Unexpected end of input\n"
                       f"TypeError: unrelated later error\n    at run ({stack_path}:2:1)\n")
                result = locate_failure(self.root, raw)
                eof_frame, stack_frame = result["frames"]
                self.assertEqual(eof_frame["status"], "located")
                self.assertEqual((eof_frame["line"], eof_frame["context_line"]), (2, 1))
                self.assertEqual(eof_frame["location_kind"], "end_of_file")
                self.assertEqual(stack_frame["status"], "line_out_of_range")
                self.assertIsNone(stack_frame["evidence_id"])
                self.assertNotIn("location_kind", stack_frame)
                self.assertNotIn("context_line", stack_frame)
                self.assertEqual(result["error_output"], raw)
                self.assertEqual(len(result["evidence"]), 1)
                self.assertEqual(result["evidence"][0]["text"], source)

    def test_node_frame_without_bound_exception_does_not_borrow_another_message(self):
        self.write("main.js", "throw new Error('actual');\n")
        logs = ["    at main.js:1:1\nError: unrelated later message\n",
                "".join(f"Error: unrelated {index}\n" for index in range(20))
                + "Error: clipped message\n    at main.js:1:1\n"]
        for raw in logs:
            with self.subTest(raw=raw):
                result = locate_failure(self.root, raw)
                self.assertTrue(result["source_located"])
                self.assertIsNone(result["terminal_exception"])

    def test_colored_python_matches_without_changing_log_or_source(self):
        source = "def run():\n    raise ValueError('boom')  \n"
        self.write("main.py", source)
        raw = ('\x1b[31mTraceback (most recent call last):\x1b[0m\n'
               '  File "\x1b[35mmain.py\x1b[0m", line \x1b[35m2\x1b[0m, in run\n'
               "    raise ValueError('boom')\n\x1b[31mValueError\x1b[0m: boom\n")
        result = locate_failure(self.root, raw)
        self.assertEqual(result["format"], "python")
        self.assertEqual(result["frames"][0]["source_comparison"], "match")
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["evidence"][0]["text"], source)

    def test_ecmascript_unicode_separators_count_but_formfeed_does_not(self):
        source = "const first = 1;\u2028const second = 2;\u2029\fthrow new Error('boom');\n"
        self.write("unicode.js", source)
        result = locate_failure(self.root, "Error: boom\n    at unicode.js:3:1\n")
        self.assertEqual(result["frames"][0]["status"], "located")
        record = result["evidence"][0]
        self.assertEqual((record["start_line"], record["end_line"]), (1, 3))
        self.assertEqual(record["text"], source)

    def test_local_file_url_preserves_reported_path_and_captures_decoded_path(self):
        path = self.write("a folder/main.mjs", "throw new Error('boom');\n")
        uri = path.as_uri()
        result = locate_failure(self.root, f"Error: boom\n    at run ({uri}:1:7)\n")
        self.assertEqual(result["frames"][0]["reported_path"], uri)
        self.assertEqual(result["frames"][0]["path"], "a folder/main.mjs")
        self.assertTrue(result["source_located"])

    def test_remote_generated_internal_and_encoded_traversal_locations_never_read(self):
        locations = [("https://example.invalid/src/app.js", "remote_url"),
                     ("webpack:///src/app.js", "unsupported_location"),
                     ("node:internal/main/run_main_module", "runtime_internal"),
                     ("file:///tmp/%2e%2e/private.js", "path_not_allowed"),
                     ("file://remote-host/tmp/app.js", "invalid_file_url")]
        with patch("shake_bake.troubleshoot._read", side_effect=AssertionError("no source read")):
            for location, expected in locations:
                with self.subTest(location=location):
                    result = locate_failure(self.root, f"Error: boom\n    at run ({location}:1:7)\n")
                    self.assertEqual(result["frames"][0]["status"], expected)
                    self.assertFalse(result["source_located"])


if __name__ == "__main__":
    unittest.main()

"""Synthetic pasted failures: exact location and refusal, never project execution."""

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.troubleshoot import (MAX_COMMAND_BYTES, MAX_ERROR_BYTES, MAX_EVIDENCE_BYTES,
                                     MAX_EXCEPTION_MESSAGE_BYTES, locate_failure)


class FailureLocatorTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "approved project"
        self.root.mkdir()

    def source(self, path="app.py", text="def run():\n    return missing\n\nrun()\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
        return target

    def trace(self, path="app.py", line=2, statement="return missing", exception="NameError: name 'missing' is not defined"):
        return (f'Traceback (most recent call last):\n  File "{path}", line {line}, in run\n'
                + (f"    {statement}\n" if statement is not None else "") + exception + "\n")

    def test_relative_frame_finishes_exact_source_location(self):
        target = self.source()
        raw = self.trace()
        command = "python3 app.py"
        before = target.read_bytes()
        result = locate_failure(self.root, raw, command)
        self.assertEqual(result["outcome"], "ANSWER")
        self.assertEqual(result["kind"], "failure_source_report")
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["command"], command)
        self.assertEqual(result["error_sha256"], hashlib.sha256(raw.encode()).hexdigest())
        frame = result["frames"][0]
        self.assertEqual(frame["status"], "located")
        self.assertEqual(frame["source_comparison"], "match")
        self.assertEqual(result["innermost_project_frame"], "F1")
        record = result["evidence"][0]
        self.assertEqual(record["text"], before.decode())
        self.assertEqual(record["file_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(record["excerpt_sha256"], hashlib.sha256(record["text"].encode()).hexdigest())
        self.assertEqual(target.read_bytes(), before)
        self.assertIn("root cause", result["limitations"][0])

    def test_absolute_in_root_path_and_spaces_are_exact(self):
        target = self.source("a folder/app with space.py")
        result = locate_failure(self.root, self.trace(str(target)))
        self.assertEqual(result["frames"][0]["path"], "a folder/app with space.py")
        self.assertEqual(result["frames"][0]["status"], "located")

    def test_quote_in_filename_is_literal_not_an_escape(self):
        self.source('a"quote.py')
        result = locate_failure(self.root, self.trace('a"quote.py'))
        self.assertEqual(result["frames"][0]["path"], 'a"quote.py')
        self.assertTrue(result["source_located"])

    def test_external_absolute_and_similar_prefix_paths_are_never_opened(self):
        self.source()
        outside = self.root.parent / "approved project-other" / "app.py"
        with patch("shake_bake.troubleshoot._read", side_effect=AssertionError("must not read")):
            for path in ("/etc/passwd", str(outside)):
                with self.subTest(path=path):
                    result = locate_failure(self.root, self.trace(path))
                    self.assertEqual(result["frames"][0]["status"], "outside_project")
                    self.assertEqual(result["frames"][0]["reported_path"], path)
                    self.assertFalse(result["source_located"])

    def test_no_basename_guessing(self):
        self.source("src/app.py")
        result = locate_failure(self.root, self.trace("app.py"))
        self.assertFalse(result["source_located"])
        self.assertEqual(result["frames"][0]["status"], "source_unavailable_or_not_allowed")

    def test_traversal_credentials_and_windows_paths_are_refused(self):
        for path in ("../secret.py", str(self.root / ".." / "secret.py"), ".env", ".env.private",
                     ".ssh/key.py", "credentials.json", "C:\\work\\app.py"):
            with self.subTest(path=path), patch("shake_bake.troubleshoot._read", side_effect=AssertionError("must not read")):
                result = locate_failure(self.root, self.trace(path))
                self.assertEqual(result["frames"][0]["status"], "path_not_allowed")

    def test_file_and_directory_symlinks_are_refused(self):
        original = self.source("real/app.py")
        (self.root / "linked.py").symlink_to(original)
        (self.root / "linked-dir").symlink_to(original.parent, target_is_directory=True)
        for path in ("linked.py", "linked-dir/app.py"):
            with self.subTest(path=path):
                result = locate_failure(self.root, self.trace(path))
                self.assertFalse(result["source_located"])
                self.assertEqual(result["frames"][0]["status"], "source_unavailable_or_not_allowed")

    def test_source_statement_mismatch_is_visible(self):
        self.source(text="def run():\n    return fixed\n")
        result = locate_failure(self.root, self.trace())
        self.assertEqual(result["frames"][0]["source_comparison"], "mismatch")
        self.assertEqual(result["frames"][0]["status"], "located")
        self.assertTrue(any("source matches" in item["title"] for item in result["guidance"]))

    def test_statement_whitespace_matches_python_traceback_formatting(self):
        self.source(text="def run():\n\treturn missing  \n")
        formatted = "".join(traceback.StackSummary.from_list(
            [("app.py", 2, "run", "\treturn missing  ")]).format())
        self.assertIn("    return missing\n", formatted)
        raw = "Traceback (most recent call last):\n" + formatted + "NameError: missing\n"
        result = locate_failure(self.root, raw)
        self.assertEqual(result["frames"][0]["source_comparison"], "match")
        self.assertEqual(result["evidence"][0]["text"], "def run():\n\treturn missing  \n")
        self.assertEqual(result["error_output"], raw)

    def test_statement_missing_is_unknown(self):
        self.source()
        result = locate_failure(self.root, self.trace(statement=None))
        self.assertEqual(result["frames"][0]["source_comparison"], "unknown")

    def test_current_line_out_of_range_is_not_a_location(self):
        self.source()
        result = locate_failure(self.root, self.trace(line=99))
        self.assertEqual(result["frames"][0]["status"], "line_out_of_range")
        self.assertFalse(result["source_located"])

    def test_python_caret_lines_do_not_replace_the_statement(self):
        self.source()
        raw = self.trace().replace("    return missing\n", "    return missing\n           ^^^^^^^\n")
        result = locate_failure(self.root, raw)
        self.assertEqual(result["frames"][0]["statement"], "return missing")
        self.assertEqual(result["frames"][0]["source_comparison"], "match")

    def test_chained_exceptions_keep_final_chain_and_project_frame_distinct(self):
        self.source()
        self.source("entry.py", "run()\n")
        raw = (self.trace() + "\nThe above exception was the direct cause of the following exception:\n\n"
               + self.trace("entry.py", 1, "run()", "RuntimeError: operation failed"))
        result = locate_failure(self.root, raw)
        self.assertEqual([item["type"] for item in result["exceptions"]], ["NameError", "RuntimeError"])
        self.assertEqual(result["terminal_exception"]["type"], "RuntimeError")
        self.assertEqual(result["innermost_project_frame"], "F2")
        self.assertEqual(result["chain_relations"], [{"from_chain": 0, "to_chain": 1, "relation": "direct_cause"}])

    def test_prior_chain_project_frame_is_not_presented_as_final_chain_location(self):
        self.source()
        raw = (self.trace() + "\nDuring handling of the above exception, another exception occurred:\n\n"
               + self.trace("/external/tool.py", exception="RuntimeError: failed cleanup"))
        result = locate_failure(self.root, raw)
        self.assertTrue(result["source_located"])
        self.assertIsNone(result["innermost_project_frame"])
        self.assertEqual(result["chain_relations"][0]["relation"], "during_handling")

    def test_truncated_later_chain_does_not_relabel_prior_exception_as_terminal(self):
        self.source()
        raw = (self.trace() + "\nDuring handling of the above exception, another exception occurred:\n\n"
               + "Traceback (most recent call last):\n")
        result = locate_failure(self.root, raw)
        self.assertTrue(result["source_located"])
        self.assertIsNone(result["innermost_project_frame"])
        self.assertIsNone(result["terminal_exception"])
        self.assertEqual(result["exceptions"][0]["type"], "NameError")

    def test_independent_tracebacks_keep_final_failure_and_source_together(self):
        self.source()
        self.source("entry.py", "raise RuntimeError('last failure')\n")
        raw = self.trace() + "\n" + self.trace("entry.py", 1, "raise RuntimeError('last failure')", "RuntimeError: last failure")
        result = locate_failure(self.root, raw)
        self.assertEqual([frame["chain_index"] for frame in result["frames"]], [0, 1])
        self.assertEqual([item["chain_index"] for item in result["exceptions"]], [0, 1])
        self.assertEqual(result["terminal_exception"]["type"], "RuntimeError")
        self.assertEqual(result["innermost_project_frame"], "F2")
        self.assertEqual(result["chain_relations"], [])
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["error_sha256"], hashlib.sha256(raw.encode()).hexdigest())

    def test_generated_unittest_output_does_not_attribute_final_failure_to_earlier_source(self):
        # Execute only these disposable fixtures to get the standard runner's
        # real multiple-error format. The locator never executes inspected code.
        suite = self.root.parent / "generated suite"
        for package, exception in (("first", "ValueError"), ("last", "PermissionError")):
            folder = suite / package
            folder.mkdir(parents=True)
            (folder / "__init__.py").write_text("", encoding="utf-8")
            (folder / "test_case.py").write_text(
                "import unittest\nclass Cases(unittest.TestCase):\n"
                f"    def test_failure(self):\n        raise {exception}('{package} failure')\n",
                encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "first.test_case", "last.test_case"],
            cwd=suite, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr.count("Traceback (most recent call last):"), 2)
        result = locate_failure(suite / "first", completed.stderr)
        self.assertEqual(result["terminal_exception"]["type"], "PermissionError")
        self.assertTrue(result["source_located"])
        self.assertIsNone(result["innermost_project_frame"])
        self.assertEqual([frame["chain_index"] for frame in result["frames"]], [0, 1])
        self.assertEqual([frame["status"] for frame in result["frames"]], ["located", "outside_project"])
        self.assertEqual(result["chain_relations"], [])
        self.assertEqual(result["error_output"], completed.stderr)
        self.assertIn("No frame in the final traceback", result["guidance"][0]["detail"])

    def test_truncated_independent_traceback_does_not_reuse_prior_terminal_or_source(self):
        self.source()
        raw = self.trace() + "\nTraceback (most recent call last):\n"
        result = locate_failure(self.root, raw)
        self.assertTrue(result["source_located"])
        self.assertIsNone(result["terminal_exception"])
        self.assertIsNone(result["innermost_project_frame"])
        self.assertEqual(result["chain_relations"], [])
        self.assertEqual(result["exceptions"][0]["type"], "NameError")

    def test_independent_standalone_syntax_errors_do_not_share_final_source(self):
        self.source(text="def run(:\n    pass\n")
        raw = ('  File "app.py", line 1\n    def run(:\n            ^\nSyntaxError: first invalid syntax\n'
               '\n  File "/external/later.py", line 9\n    return )\n           ^\nSyntaxError: final invalid syntax\n')
        result = locate_failure(self.root, raw)
        self.assertEqual([frame["chain_index"] for frame in result["frames"]], [0, 1])
        self.assertEqual(result["terminal_exception"]["message"], "final invalid syntax")
        self.assertTrue(result["source_located"])
        self.assertIsNone(result["innermost_project_frame"])
        self.assertEqual(result["chain_relations"], [])
        self.assertEqual(result["error_output"], raw)

    def test_explicit_chain_followed_by_standalone_syntax_block_advances_only_once(self):
        self.source()
        self.source("invalid.py", "def run(:\n")
        markers = (("The above exception was the direct cause of the following exception:", "direct_cause"),
                   ("During handling of the above exception, another exception occurred:", "during_handling"))
        for marker, relation in markers:
            with self.subTest(relation=relation):
                raw = (self.trace() + "\n" + marker + "\n\n"
                       + '  File "invalid.py", line 1\n    def run(:\n            ^\nSyntaxError: invalid syntax\n')
                result = locate_failure(self.root, raw)
                self.assertEqual([frame["chain_index"] for frame in result["frames"]], [0, 1])
                self.assertEqual(result["innermost_project_frame"], "F2")
                self.assertEqual(result["terminal_exception"]["type"], "SyntaxError")
                self.assertEqual(result["chain_relations"], [{"from_chain": 0, "to_chain": 1, "relation": relation}])

    def test_missing_package_exception_only_has_actionable_bounded_guidance(self):
        raw = "ModuleNotFoundError: No module named 'example_package'\n"
        result = locate_failure(self.root, raw, "python3 -m example")
        self.assertEqual(result["outcome"], "ABSTAIN")
        self.assertTrue(result["supported_format"])
        self.assertFalse(result["source_located"])
        self.assertEqual(result["terminal_exception"]["type"], "ModuleNotFoundError")
        detail = result["guidance"][0]["detail"]
        self.assertIn("different interpreter", detail)
        self.assertIn("before installing", detail)

    def test_unknown_plain_log_invents_no_exception_or_cause(self):
        raw = "Application failed while preparing input. Please retry.\n"
        result = locate_failure(self.root, raw)
        self.assertFalse(result["supported_format"])
        self.assertFalse(result["source_located"])
        self.assertIsNone(result["terminal_exception"])
        self.assertEqual(result["frames"], [])

    def test_only_derived_exception_message_is_clipped_at_a_utf8_boundary(self):
        for message in ("\x01" * 60000, "€" * 3000):
            with self.subTest(character=repr(message[0])):
                raw = "ValueError: " + message
                result = locate_failure(self.root, raw)
                terminal = result["terminal_exception"]
                self.assertEqual(result["error_output"], raw)
                self.assertTrue(terminal["message_truncated"])
                self.assertEqual(terminal["message_bytes"], len(message.encode("utf-8")))
                self.assertLessEqual(len(terminal["message"].encode("utf-8")), MAX_EXCEPTION_MESSAGE_BYTES)
                self.assertTrue(message.startswith(terminal["message"]))
                self.assertIn("exception_message_budget", result["cutoffs"])
                self.assertEqual(result["exceptions"][-1], terminal)

    def test_short_exception_message_is_unchanged_and_explicitly_complete(self):
        result = locate_failure(self.root, "ValueError: short message")
        self.assertEqual(result["terminal_exception"]["message"], "short message")
        self.assertFalse(result["terminal_exception"]["message_truncated"])
        self.assertNotIn("exception_message_budget", result["cutoffs"])

    def test_syntax_error_file_block_without_traceback_header_is_supported(self):
        self.source(text="def run(:\n    pass\n")
        raw = '  File "app.py", line 1\n    def run(:\n            ^\nSyntaxError: invalid syntax\n'
        result = locate_failure(self.root, raw)
        self.assertEqual(result["frames"][0]["source_comparison"], "match")
        self.assertEqual(result["terminal_exception"]["type"], "SyntaxError")
        self.assertTrue(any("matches current source" in item["detail"] for item in result["guidance"]))

    def test_qualified_json_and_permission_errors_have_specific_checks(self):
        for exception, fragment in (("json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)", "JSON input"),
                                    ("PermissionError: [Errno 13] Permission denied", "safe permission change")):
            with self.subTest(exception=exception):
                result = locate_failure(self.root, exception)
                self.assertTrue(result["supported_format"])
                self.assertTrue(any(fragment in item["detail"] for item in result["guidance"]))

    def test_long_trace_keeps_innermost_twenty_frames_and_at_most_ten_windows(self):
        text = "".join(f"value_{index} = {index}\n" for index in range(1, 32))
        self.source(text=text)
        raw = "Traceback (most recent call last):\n" + "".join(
            f'  File "app.py", line {index}, in f{index}\n    value_{index} = {index}\n' for index in range(1, 31)) + "ValueError: stop\n"
        result = locate_failure(self.root, raw)
        self.assertEqual(len(result["frames"]), 20)
        self.assertEqual(result["frames"][0]["frame_id"], "F11")
        self.assertEqual(len(result["evidence"]), 10)
        self.assertEqual(result["innermost_project_frame"], "F30")
        self.assertIn("frame_budget", result["cutoffs"])
        self.assertIn("capture_budget", result["cutoffs"])

    def test_repeated_frames_share_one_exact_evidence_record(self):
        self.source()
        raw = self.trace().replace("NameError:", '  File "app.py", line 2, in run\n    return missing\nNameError:')
        result = locate_failure(self.root, raw)
        self.assertEqual(len(result["evidence"]), 1)
        self.assertEqual([item["evidence_id"] for item in result["frames"]], ["E1", "E1"])

    def test_evidence_byte_budget_shrinks_context_without_changing_source(self):
        text = "x" * 10_000 + "\n" + "return missing\n" + "y" * 10_000 + "\n"
        self.source(text=text)
        result = locate_failure(self.root, self.trace())
        self.assertLessEqual(result["selected_excerpt_bytes"], MAX_EVIDENCE_BYTES)
        record = result["evidence"][0]
        self.assertIn("return missing\n", record["text"])
        self.assertEqual(record["text"], "".join(text.splitlines(keepends=True)[record["start_line"] - 1:record["end_line"]]))
        self.assertIn("context_excerpt_budget", result["cutoffs"])

    def test_oversized_target_line_is_explicitly_uncaptured(self):
        self.source(text="x" * (MAX_EVIDENCE_BYTES + 1) + "\n")
        result = locate_failure(self.root, self.trace(line=1))
        self.assertFalse(result["source_located"])
        self.assertEqual(result["frames"][0]["status"], "excerpt_budget")
        self.assertIn("evidence_byte_budget", result["cutoffs"])

    def test_non_utf8_binary_and_oversized_files_are_not_captured(self):
        for content, status in ((b"\xff\n", "utf8_required"), (b"a\x00b\n", "text_file_required"),
                                (b"x" * (256 * 1024 + 1), "file_too_large")):
            with self.subTest(status=status):
                (self.root / "app.py").write_bytes(content)
                result = locate_failure(self.root, self.trace(line=1))
                self.assertEqual(result["frames"][0]["status"], status)

    def test_source_line_numbers_ignore_unicode_and_form_feed_separators(self):
        self.source(text='note = "a\u2028b"\n\f    return missing\n')
        result = locate_failure(self.root, self.trace())
        self.assertEqual(result["evidence"][0]["end_line"], 2)
        # Python strips a leading form feed from the displayed statement too.
        self.assertEqual(result["frames"][0]["source_comparison"], "match")

    def test_crlf_bytes_and_trailing_newline_are_preserved(self):
        target = self.source(text="def run():\r\n    return missing\r\n")
        result = locate_failure(self.root, self.trace().replace("\n", "\r\n"))
        self.assertEqual(result["evidence"][0]["text"].encode(), target.read_bytes())
        self.assertEqual(result["frames"][0]["source_comparison"], "match")

    def test_input_limits_utf8_and_surrogates_fail_without_truncation(self):
        for raw in ("", " ", "x" * (MAX_ERROR_BYTES + 1), "é" * (MAX_ERROR_BYTES // 2 + 1), "bad\ud800", "bad\x00"):
            with self.subTest(raw=repr(raw[:10])):
                with self.assertRaises(Refusal) as raised:
                    locate_failure(self.root, raw)
                self.assertEqual(raised.exception.code, "invalid_error_output")
        for command in ("x" * (MAX_COMMAND_BYTES + 1), "bad\ud800", "bad\x00", None):
            with self.subTest(command=repr(command)[:20]):
                with self.assertRaises(Refusal) as raised:
                    locate_failure(self.root, "ValueError: stop", command)
                self.assertEqual(raised.exception.code, "invalid_failure_command")

    def test_untrusted_command_and_source_are_retained_but_never_executed(self):
        marker = self.root / "must-not-exist"
        source = f'__import__("pathlib").Path({str(marker)!r}).write_text("bad")\n'
        self.source(text=source)
        command = "$(touch must-not-exist); python3 app.py"
        result = locate_failure(self.root, self.trace(line=1, statement=source.rstrip("\n")), command)
        self.assertFalse(marker.exists())
        self.assertEqual(result["command"], command)
        self.assertEqual(result["evidence"][0]["text"], source)


if __name__ == "__main__":
    unittest.main()

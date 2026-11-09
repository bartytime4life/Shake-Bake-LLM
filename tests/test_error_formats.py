"""Synthetic location claims and explicit disposable development fixtures."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from shake_bake.contracts import Refusal
from shake_bake.error_formats import (MAX_ERROR_BYTES, MAX_FRAMES, MAX_FUNCTION_BYTES,
                                      MAX_MESSAGE_BYTES, MAX_PATH_BYTES,
                                      parse_javascript, strip_terminal_controls)


class JavascriptFormatTests(unittest.TestCase):
    def test_node_frames_keep_innermost_first_and_columns(self):
        raw = ("TypeError: invalid task\n"
               "    at run (/approved project/src/app.js:12:7)\n"
               "    at Object.<anonymous> (/approved project/start.js:3:1)\n"
               "    at Module._compile (node:internal/modules/cjs/loader:1521:14)\n")
        result = parse_javascript(raw)
        self.assertEqual(result["format"], "node")
        self.assertEqual(result["frame_order"], "innermost_first")
        self.assertEqual(result["primary_frame_id"], "F1")
        self.assertEqual(result["terminal_exception"]["type"], "TypeError")
        self.assertEqual(result["terminal_exception"]["message"], "invalid task")
        self.assertEqual(result["frames"][0]["reported_path"], "/approved project/src/app.js")
        self.assertEqual(result["frames"][0]["line"], 12)
        self.assertEqual(result["frames"][0]["column"], 7)
        self.assertEqual(result["frames"][0]["function"], "run")
        self.assertIsNone(result["frames"][0]["statement"])
        self.assertEqual(result["frames"][2]["path_status"], "runtime_internal")
        self.assertIsNone(result["frames"][2]["lookup_path"])

    def test_relative_bare_async_and_constructor_frames(self):
        result = parse_javascript("Error: fail\n"
                                  "    at src/task.js:1:2\n"
                                  "    at async src/worker.js:7:8\n"
                                  "    at new Task (src/model.js:4:6)\n")
        self.assertEqual([f["lookup_path"] for f in result["frames"]],
                         ["src/task.js", "src/worker.js", "src/model.js"])
        self.assertEqual([f["function"] for f in result["frames"]], [None, "async", "new Task"])

    def test_spaces_and_parentheses_in_filename_remain_exact(self):
        frame = parse_javascript("Error: fail\n    at run (/approved project/a (copy).js:2:3)\n")["frames"][0]
        self.assertEqual(frame["lookup_path"], "/approved project/a (copy).js")
        self.assertEqual(frame["function"], "run")

    def test_local_file_url_decodes_once_without_changing_reported_claim(self):
        path = "file:///approved%20project/a%25b%23c.mjs"
        frame = parse_javascript(f"Error: fail\n    at run ({path}:8:2)\n")["frames"][0]
        self.assertEqual(frame["reported_path"], path)
        self.assertEqual(frame["lookup_path"], "/approved project/a%b#c.mjs")
        self.assertEqual(frame["path_status"], "not_checked")

    def test_localhost_file_url_is_local_but_other_hosts_and_credentials_are_excluded(self):
        local = parse_javascript("Error: fail\n    at file://localhost/tmp/run.mjs:1:1\n")["frames"][0]
        self.assertEqual(local["lookup_path"], "/tmp/run.mjs")
        for path in ("file://server/tmp/run.mjs", "file://user@localhost/tmp/run.mjs",
                     "file://localhost:80/tmp/run.mjs", "file:relative/run.mjs"):
            with self.subTest(path=path):
                frame = parse_javascript(f"Error: fail\n    at {path}:1:2\n")["frames"][0]
                self.assertEqual(frame["path_status"], "invalid_file_url")
                self.assertIsNone(frame["lookup_path"])

    def test_malformed_or_ambiguous_file_urls_do_not_get_rewritten(self):
        for path in ("file:///tmp/%ZZ.mjs", "file:///tmp/%FF.mjs", "file:///tmp/%00.mjs",
                     "file:///tmp/a.mjs?token=secret", "file:///tmp/a.mjs#source",
                     "file:///tmp/a\tb.mjs"):
            with self.subTest(path=path):
                frame = parse_javascript(f"Error: fail\n    at {path}:1:2\n")["frames"][0]
                self.assertEqual(frame["path_status"], "invalid_file_url")
                self.assertIsNone(frame["lookup_path"])

    def test_url_traversal_claim_is_passed_to_caller_without_normalization(self):
        path = "file:///approved/%2e%2e/outside.mjs"
        frame = parse_javascript(f"Error: fail\n    at {path}:1:2\n")["frames"][0]
        self.assertEqual(frame["lookup_path"], "/approved/../outside.mjs")

    def test_remote_and_virtual_locations_are_never_local_candidates(self):
        for path, status in (("https://example.test/app.js", "remote_url"),
                             ("http://localhost:3000/app.js", "remote_url"),
                             ("webpack:///src/app.js", "unsupported_location"),
                             ("node:internal/process/task_queues", "runtime_internal"),
                             ("<anonymous>", "runtime_internal")):
            with self.subTest(path=path):
                frame = parse_javascript(f"Error: fail\n    at {path}:1:2\n")["frames"][0]
                self.assertEqual(frame["path_status"], status)
                self.assertIsNone(frame["lookup_path"])

    def test_windows_claim_is_not_translated_to_a_posix_path(self):
        frame = parse_javascript("Error: fail\n    at run (C:\\project\\app.js:3:4)\n")["frames"][0]
        self.assertEqual(frame["lookup_path"], "C:\\project\\app.js")

    def test_nested_eval_and_nonnumeric_frames_are_omitted(self):
        result = parse_javascript("Error: fail\n"
                                  "    at eval (eval at run (/approved/app.js:10:2), <anonymous>:1:1)\n"
                                  "    at async Promise.all (index 0)\n"
                                  "    at String.split (<anonymous>)\n"
                                  "    at run (/approved/app.js:0:2)\n")
        self.assertEqual(result["frames"], [])

    def test_node_error_code_is_separate_from_message(self):
        result = parse_javascript("Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'task'\n"
                                  "    at run (src/start.mjs:4:1)\n")
        self.assertEqual(result["terminal_exception"]["type"], "Error")
        self.assertEqual(result["terminal_exception"]["code"], "ERR_MODULE_NOT_FOUND")

    def test_node_syntax_header_locates_project_before_internal_stack(self):
        result = parse_javascript("/approved/app.js:2\nconst broken = ;\n               ^\n\n"
                                  "SyntaxError: Unexpected token ';'\n"
                                  "    at wrapSafe (node:internal/modules/cjs/loader:1378:20)\n")
        self.assertEqual(result["frames"][0]["lookup_path"], "/approved/app.js")
        self.assertEqual(result["frames"][0]["line"], 2)
        self.assertIsNone(result["frames"][0]["column"])
        self.assertEqual(result["frames"][0]["exception_index"], 0)
        self.assertEqual(result["primary_frame_id"], "F1")

    def test_unrelated_path_line_without_caret_is_not_a_frame(self):
        result = parse_javascript("/approved/app.js:2\nError: unrelated text\n")
        self.assertEqual(result["frames"], [])

    def test_unexpected_eof_without_caret_retains_exact_reported_location(self):
        for path, line, source, marker in (("/approved/app.cjs", 1, "function unfinished() {", " " * 23),
                                           ("file:///approved/app.mjs", 2, "", "")):
            with self.subTest(path=path):
                result = parse_javascript(f"{path}:{line}\n{source}\n{marker}\n\n"
                                          "SyntaxError: Unexpected end of input\n"
                                          "    at wrapSafe (node:internal/modules/cjs/loader:1512:18)\n")
                frame = result["frames"][0]
                self.assertEqual(frame["reported_path"], path)
                self.assertEqual(frame["line"], line)
                self.assertIsNone(frame["column"])
                self.assertEqual(frame["exception_index"], 0)
                self.assertEqual(result["primary_frame_id"], frame["frame_id"])

    def test_no_caret_eof_requires_the_normal_source_block(self):
        for body, error in (("", "SyntaxError: Unexpected end of input"),
                            ("source\nnot a marker\n\n", "SyntaxError: Unexpected end of input"),
                            ("source\n   \n\n", "Error: Unexpected end of input"),
                            ("source\n   \n\n", "SyntaxError: Unrelated message")):
            with self.subTest(body=body, error=error):
                result = parse_javascript(f"/approved/app.js:2\n{body}{error}\n")
                self.assertEqual(result["frames"], [])

    def test_runtime_source_header_does_not_hide_stack_column_and_function(self):
        result = parse_javascript("/approved/app.js:2\nthrow new Error('fail');\n^\n\nError: fail\n"
                                  "    at run (/approved/app.js:2:7)\n"
                                  "    at main (/approved/app.js:4:1)\n")
        self.assertEqual(len(result["frames"]), 2)
        self.assertEqual(result["frames"][0]["column"], 7)
        self.assertEqual(result["frames"][0]["function"], "run")
        self.assertEqual([frame["frame_id"] for frame in result["frames"]], ["F1", "F2"])

    def test_multiple_error_stacks_keep_exception_binding(self):
        result = parse_javascript("TypeError: first\n    at run (first.js:1:2)\n"
                                  "RangeError: second\n    at run (second.js:3:4)\n")
        self.assertEqual([f["exception_index"] for f in result["frames"]], [0, 1])
        self.assertEqual([e["message"] for e in result["exceptions"]], ["first", "second"])

    def test_node_cause_frames_bind_their_own_error(self):
        result = parse_javascript("Error: wrapper failed\n"
                                  "    at wrap (/outside/runner.cjs:1:12) {\n"
                                  "  [cause]: TypeError: inner detail\n"
                                  "      at fail (/approved/inner.js:2:4)\n"
                                  "}\n")
        self.assertEqual(len(result["exceptions"]), 2)
        frame = next(item for item in result["frames"] if item["lookup_path"] == "/approved/inner.js")
        exception = result["exceptions"][frame["exception_index"]]
        self.assertEqual((exception["type"], exception["message"]), ("TypeError", "inner detail"))

    def test_nested_causes_and_later_stack_keep_exception_binding(self):
        result = parse_javascript("Error: outer\n    at outer (outer.js:1:1)\n"
                                  "  [cause]: RangeError: middle {\n"
                                  "      at middle (middle.js:2:3)\n"
                                  "    [cause]: TypeError: inner\n"
                                  "        at inner (inner.js:4:5)\n"
                                  "  }\n}\n"
                                  "Error: separate\n    at later (later.js:6:7)\n")
        self.assertEqual([item["exception_index"] for item in result["frames"]], [0, 1, 2, 3])
        self.assertEqual([item["type"] for item in result["exceptions"]],
                         ["Error", "RangeError", "TypeError", "Error"])

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_node_eof_and_cause_from_disposable_generated_fixtures(self):
        # Only these generated fixtures execute. The production parser receives
        # output text and never runs the command or source it is inspecting.
        with tempfile.TemporaryDirectory(prefix="sb-node-format-") as scratch:
            root = Path(scratch)
            for name, source, line in (("broken.cjs", "function unfinished() {", 1),
                                       ("broken.mjs", "export function unfinished() {\n", 2)):
                path = root / name
                path.write_text(source, encoding="utf-8")
                run = subprocess.run([shutil.which("node"), str(path)], capture_output=True,
                                     text=True, timeout=5)
                self.assertNotEqual(run.returncode, 0)
                result = parse_javascript(run.stderr)
                frame = result["frames"][0]
                self.assertEqual(frame["lookup_path"], str(path))
                self.assertEqual(frame["line"], line)
                self.assertEqual(result["terminal_exception"]["type"], "SyntaxError")
            inner = root / "inner.cjs"
            inner.write_text("module.exports = () => { throw new TypeError('inner detail') };\n", encoding="utf-8")
            wrapper = root / "wrapper.cjs"
            wrapper.write_text("try { require('./inner.cjs')() } catch (cause) { throw new Error('outer wrapper', {cause}) }\n",
                               encoding="utf-8")
            run = subprocess.run([shutil.which("node"), str(wrapper)], capture_output=True,
                                 text=True, timeout=5)
            self.assertNotEqual(run.returncode, 0)
            result = parse_javascript(run.stderr)
            frame = next(item for item in result["frames"] if item["lookup_path"] == str(inner))
            exception = result["exceptions"][frame["exception_index"]]
            self.assertEqual((exception["type"], exception["message"]), ("TypeError", "inner detail"))

    def test_frame_budget_keeps_innermost_twenty(self):
        raw = "Error: fail\n" + "".join(f"    at run (src/{i}.js:{i + 1}:1)\n" for i in range(30))
        result = parse_javascript(raw)
        self.assertEqual(len(result["frames"]), MAX_FRAMES)
        self.assertEqual(result["frames"][0]["reported_path"], "src/0.js")
        self.assertEqual(result["frames"][-1]["reported_path"], "src/19.js")
        self.assertIn("frame_budget", result["cutoffs"])

    def test_metadata_budgets_do_not_create_truncated_read_candidates(self):
        result = parse_javascript("Error: " + "é" * 2000 + "\n    at " + "run" * 500
                                  + " (" + "/" + "a" * 5000 + ".js:1:2)\n")
        frame = result["frames"][0]
        self.assertLessEqual(len(frame["reported_path"].encode()), MAX_PATH_BYTES)
        self.assertTrue(frame["reported_path_truncated"])
        self.assertEqual(frame["path_status"], "path_metadata_budget")
        self.assertIsNone(frame["lookup_path"])
        self.assertLessEqual(len(frame["function"].encode()), MAX_FUNCTION_BYTES)
        self.assertLessEqual(len(result["terminal_exception"]["message"].encode()), MAX_MESSAGE_BYTES)
        self.assertTrue(result["terminal_exception"]["message_truncated"])
        self.assertEqual(result["terminal_exception"]["message_bytes"], 4000)
        self.assertTrue({"path_metadata_budget", "function_metadata_budget", "exception_message_budget"}
                        <= set(result["cutoffs"]))

    def test_input_budget_surrogates_and_nuls_are_rejected(self):
        for raw in ("a" * (MAX_ERROR_BYTES + 1), "\ud800", "Error: null\x00", None):
            with self.subTest(raw_type=type(raw)), self.assertRaises(Refusal):
                parse_javascript(raw)

    def test_unrecognized_text_is_not_a_supported_format(self):
        result = parse_javascript("Build stopped. See the application dashboard.\n")
        self.assertIsNone(result["format"])
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["exceptions"], [])


class TypescriptFormatTests(unittest.TestCase):
    def test_nonpretty_position_and_message(self):
        result = parse_javascript("src/task.ts(12,7): error TS2322: Type 'string' is not assignable to type 'number'.\n")
        self.assertEqual(result["format"], "typescript")
        self.assertEqual(result["frame_order"], "diagnostic_order")
        self.assertEqual(result["frames"][0]["reported_path"], "src/task.ts")
        self.assertEqual(result["frames"][0]["line"], 12)
        self.assertEqual(result["frames"][0]["column"], 7)
        self.assertEqual(result["terminal_exception"]["type"], "TS2322")
        self.assertEqual(result["frames"][0]["exception_index"], 0)

    def test_pretty_position_with_ansi_and_spaced_absolute_path(self):
        raw = ("\x1b[96m/approved project/src/task.ts\x1b[0m:\x1b[93m12\x1b[0m:\x1b[93m7\x1b[0m - "
               "\x1b[91merror\x1b[0m\x1b[90m TS2304: \x1b[0mCannot find name 'missing'.\n\n"
               "\x1b[7m12\x1b[0m missing();\n\x1b[7m  \x1b[0m \x1b[91m~~~~~~~\x1b[0m\n")
        result = parse_javascript(raw)
        self.assertEqual(result["frames"][0]["lookup_path"], "/approved project/src/task.ts")
        self.assertEqual(result["terminal_exception"]["type"], "TS2304")
        self.assertEqual(result["terminal_exception"]["message"], "Cannot find name 'missing'.")
        self.assertIn("\x1b[96m", raw)

    def test_each_diagnostic_binds_its_own_exception_including_global_errors(self):
        result = parse_javascript("error TS18003: No inputs were found.\n"
                                  "/outside/first.ts(1,2): error TS2304: Cannot find name 'first'.\n"
                                  "src/second.ts(3,4): error TS2322: Type 'string' is not assignable.\n")
        self.assertEqual([f["exception_index"] for f in result["frames"]], [1, 2])
        for frame, kind, message in zip(result["frames"], ["TS2304", "TS2322"],
                                        ["Cannot find name 'first'.", "Type 'string' is not assignable."]):
            exception = result["exceptions"][frame["exception_index"]]
            self.assertEqual((exception["type"], exception["message"]), (kind, message))

    def test_two_diagnostics_same_file_keep_distinct_line_and_message(self):
        result = parse_javascript("src/app.ts(1,1): error TS2304: Cannot find name 'first'.\n"
                                  "src/app.ts:2:3 - error TS2345: Argument is invalid.\n")
        self.assertEqual([f["line"] for f in result["frames"]], [1, 2])
        self.assertEqual([f["exception_index"] for f in result["frames"]], [0, 1])
        self.assertEqual(result["terminal_exception"]["type"], "TS2304")

    def test_diagnostic_budget_keeps_exception_indices_stable(self):
        raw = "".join(f"src/{i}.ts(1,2): error TS2304: Missing item {i}.\n" for i in range(30))
        result = parse_javascript(raw)
        self.assertEqual(len(result["frames"]), MAX_FRAMES)
        self.assertEqual(len(result["exceptions"]), MAX_FRAMES)
        self.assertEqual([f["exception_index"] for f in result["frames"]], list(range(MAX_FRAMES)))
        self.assertIn("frame_budget", result["cutoffs"])
        self.assertIn("exception_budget", result["cutoffs"])

    def test_global_error_has_message_but_no_invented_source_location(self):
        result = parse_javascript("error TS18003: No inputs were found in config file.\n")
        self.assertEqual(result["format"], "typescript")
        self.assertEqual(result["frames"], [])
        self.assertIsNone(result["primary_frame_id"])

    def test_diagnostic_format_does_not_guess_from_build_tool_prefixes(self):
        for raw in ("ERROR in src/app.ts:2:3 TS2304: missing", "src/app.ts:2:3: error unknown",
                    "warning TS2304: missing", "src/app.ts(0,1): error TS2304: missing"):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_javascript(raw)["format"])


class TerminalMatchingTests(unittest.TestCase):
    def test_initial_utf8_bom_is_removed_only_from_the_matching_copy(self):
        raw = "\ufeffsrc/task.ts(1,2): error TS2322: Invalid value.\r\n"
        self.assertEqual(strip_terminal_controls(raw), raw[1:])
        result = parse_javascript(raw)
        self.assertEqual(result["format"], "typescript")
        self.assertEqual(result["frames"][0]["lookup_path"], "src/task.ts")
        self.assertTrue(raw.startswith("\ufeff"))
        self.assertEqual(strip_terminal_controls("\ufeff\ufefftext"), "\ufefftext")
        self.assertEqual(strip_terminal_controls("text\ufeff"), "text\ufeff")

    def test_complete_color_hyperlink_and_cursor_sequences_are_removed(self):
        raw = "\x1b[1mError\x1b[0m: fail\n    at run (\x1b]8;;file:///tmp/app.js\x1b\\/tmp/app.js\x1b]8;;\x07:2:3)\x1b[K\n"
        matching = strip_terminal_controls(raw)
        self.assertEqual(matching, "Error: fail\n    at run (/tmp/app.js:2:3)\n")
        self.assertEqual(parse_javascript(raw)["frames"][0]["lookup_path"], "/tmp/app.js")

    def test_c1_sequences_and_python_traceback_colors_match_without_raw_mutation(self):
        raw = '\x9b31mTraceback (most recent call last):\x9b0m\r\n  File "app.py", line 2\r\n'
        self.assertEqual(strip_terminal_controls(raw), 'Traceback (most recent call last):\r\n  File "app.py", line 2\r\n')
        self.assertTrue(raw.startswith("\x9b31m"))

    def test_backspace_and_unclosed_escape_strings_do_not_rewrite_paths(self):
        raw = "Error: fail\n    at a\bb.js:2:3\n\x1b]8;;unterminated"
        self.assertEqual(strip_terminal_controls(raw), raw)
        self.assertEqual(parse_javascript(raw)["frames"][0]["lookup_path"], "a\bb.js")


if __name__ == "__main__":
    unittest.main()

"""Separate Node aggregate members without flattening unsupported structures."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.collector import _read
from shake_bake.error_formats import MAX_FRAMES, MAX_MESSAGE_BYTES, parse_javascript
from shake_bake.troubleshoot import locate_failure


def aggregate(first="first.js", second="second.js", *, bracket=True):
    header = "[AggregateError: All promises were rejected] {" if bracket else "AggregateError: batch failed"
    return (header + "\n  [errors]: [\n"
            "    TypeError: first input failed\n"
            f"        at first ({first}:1:7),\n"
            "    RangeError: second input failed\n"
            f"        at second ({second}:2:9)\n"
            "  ]\n}\n")


class NodeAggregateFormatTests(unittest.TestCase):
    def test_bracketed_promise_any_members_keep_their_own_messages(self):
        result = parse_javascript(aggregate())
        self.assertEqual(result["format"], "node")
        self.assertEqual([item["type"] for item in result["exceptions"]],
                         ["AggregateError", "TypeError", "RangeError"])
        self.assertEqual(result["terminal_exception"]["message"], "All promises were rejected")
        self.assertEqual([frame["exception_index"] for frame in result["frames"]], [1, 2])
        self.assertEqual([item.get("aggregate_parent_index") for item in result["exceptions"]], [None, 0, 0])
        self.assertEqual(result["cutoffs"], [])

    def test_explicit_aggregate_outer_stack_and_member_stacks_are_distinct(self):
        raw = ("AggregateError: batch failed\n    at batch (batch.js:3:5) {\n"
               + aggregate(bracket=False).split("\n", 1)[1])
        result = parse_javascript(raw)
        self.assertEqual([frame["exception_index"] for frame in result["frames"]], [0, 1, 2])
        self.assertEqual(result["frames"][0]["lookup_path"], "batch.js")
        # The brace suffix is Node's object framing, not part of the path.
        self.assertEqual(result["terminal_exception"]["type"], "AggregateError")

    def test_array_commas_are_removed_only_inside_explicit_error_member_stacks(self):
        result = parse_javascript(aggregate())
        self.assertEqual([frame["lookup_path"] for frame in result["frames"]], ["first.js", "second.js"])
        self.assertEqual([frame["column"] for frame in result["frames"]], [7, 9])
        outside = parse_javascript("Error: ordinary\n    at first.js:1:7,\n")
        self.assertEqual(outside["frames"], [])

    def test_empty_promise_any_array_has_aggregate_message_and_no_invented_frame(self):
        result = parse_javascript("[AggregateError: All promises were rejected] { [errors]: [] }\n")
        self.assertEqual(result["terminal_exception"]["type"], "AggregateError")
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["cutoffs"], [])
        explicit = parse_javascript("AggregateError: no inputs\n    at batch (batch.js:1:1) {\n  [errors]: []\n}\n")
        self.assertEqual(explicit["cutoffs"], [])
        self.assertEqual(explicit["frames"][0]["exception_index"], 0)

    def test_indented_error_text_outside_an_array_does_not_become_an_exception(self):
        result = parse_javascript("Error: outer\n    TypeError: arbitrary log text\n        at first.js:1:7\n")
        self.assertEqual(len(result["exceptions"]), 1)
        self.assertNotIn("aggregate_parent_index", result["exceptions"][0])

    def test_nested_and_unsupported_member_structures_cannot_borrow_outer_message(self):
        bodies = [
            "    AggregateError: nested {\n      [errors]: [\n        TypeError: inner\n            at first.js:1:1\n      ]\n    }\n",
            "    AggregateError: nested\n        at first.js:1:1\n        at runtime (node:internal/loader:2:2) {\n      [errors]: [\n        TypeError: inner\n            at second.js:2:2\n      ]\n    }\n",
            "    Error: member {\n        at first.js:1:1\n      [cause]: TypeError: inner\n          at second.js:2:2\n    }\n",
            "    Error: member\n        at first.js:1:1\n        at runtime (node:internal/loader:2:2) {\n      [cause]: TypeError: inner\n          at second.js:2:2\n    }\n",
            "    'primitive rejection',\n        at first.js:1:1\n",
            "   TypeError: wrong indentation\n        at first.js:1:1\n",
            "    TypeError: multiline\n    continuation not an error header\n        at first.js:1:1\n",
        ]
        for body in bodies:
            with self.subTest(body=body):
                result = parse_javascript("AggregateError: outer\n  [errors]: [\n" + body + "  ]\n}\n")
                self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])
                self.assertTrue(result["frames"])
                for frame in result["frames"]:
                    self.assertIsNone(frame["exception_index"])
                    self.assertEqual(frame["path_status"], "node_aggregate_format_unsupported")

    def test_later_member_revocation_keeps_outer_stack_and_completed_sibling(self):
        raw = ("AggregateError: outer\n    at outer (outer.js:1:1) {\n  [errors]: [\n"
               "    RangeError: supported sibling\n        at sibling (sibling.js:2:2),\n"
               "    AggregateError: nested\n        at nested (nested.js:3:3)\n"
               "        at runtime (node:internal/loader:4:4) {\n      [errors]: [\n"
               "        TypeError: inner\n            at inner (inner.js:4:4)\n      ]\n    }\n  ]\n}\n")
        result = parse_javascript(raw)
        self.assertEqual([frame["exception_index"] for frame in result["frames"]], [0, 1, None, None])
        self.assertEqual([frame["path_status"] for frame in result["frames"]],
                         ["not_checked", "not_checked", "node_aggregate_format_unsupported", "node_aggregate_format_unsupported"])
        self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])

    def test_completed_sibling_survives_a_later_primitive_member_without_an_error_header(self):
        raw = ("AggregateError: outer\n    at outer (outer.js:1:1) {\n  [errors]: [\n"
               "    RangeError: supported sibling\n        at sibling (sibling.js:2:2),\n"
               "    'primitive rejection'\n  ]\n}\n")
        result = parse_javascript(raw)
        self.assertEqual([frame["exception_index"] for frame in result["frames"]], [0, 1])
        self.assertEqual([frame["path_status"] for frame in result["frames"]], ["not_checked", "not_checked"])
        self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])

    def test_errors_property_without_an_aggregate_parent_is_explicitly_unsupported(self):
        result = parse_javascript("Error: ordinary\n  [errors]: [\n    TypeError: inner\n        at first.js:1:1\n  ]\n}\n")
        self.assertEqual(len(result["exceptions"]), 1)
        self.assertIsNone(result["frames"][0]["exception_index"])
        self.assertEqual(result["frames"][0]["path_status"], "node_aggregate_format_unsupported")
        self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])

    def test_incomplete_array_is_visible_and_later_independent_error_resets_binding(self):
        raw = ("AggregateError: outer\n  [errors]: [\n    TypeError: member\n        at first.js:1:1\n"
               "RangeError: later\n    at second.js:2:2\n")
        result = parse_javascript(raw)
        self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])
        self.assertEqual(result["frames"][-1]["exception_index"], 2)
        self.assertIsNone(result["frames"][0]["exception_index"])
        self.assertEqual(result["frames"][0]["path_status"], "node_aggregate_format_unsupported")
        self.assertEqual(result["exceptions"][2]["type"], "RangeError")
        truncated = parse_javascript(raw.split("RangeError:", 1)[0])
        self.assertIn("node_aggregate_format_unsupported", truncated["cutoffs"])
        self.assertIsNone(truncated["frames"][0]["exception_index"])
        self.assertEqual(truncated["frames"][0]["path_status"], "node_aggregate_format_unsupported")

    def test_member_limits_do_not_assign_a_clipped_error_to_previous_member(self):
        members = "".join(f"    TypeError: member {number}\n        at {number}.js:1:1\n" for number in range(22))
        result = parse_javascript("AggregateError: outer\n  [errors]: [\n" + members + "  ]\n}\n")
        self.assertEqual(len(result["exceptions"]), MAX_FRAMES)
        self.assertEqual(len(result["frames"]), MAX_FRAMES)
        self.assertEqual([frame["exception_index"] for frame in result["frames"][:-1]], list(range(1, MAX_FRAMES)))
        self.assertIsNone(result["frames"][-1]["exception_index"])
        self.assertIn("exception_budget", result["cutoffs"])
        self.assertIn("frame_budget", result["cutoffs"])

    def test_aggregate_member_message_is_bounded_without_truncating_path_claims(self):
        raw = aggregate().replace("first input failed", "é" * 2000)
        result = parse_javascript(raw)
        self.assertEqual(result["frames"][0]["reported_path"], "first.js")
        self.assertLessEqual(len(result["exceptions"][1]["message"].encode()), MAX_MESSAGE_BYTES)
        self.assertTrue(result["exceptions"][1]["message_truncated"])
        self.assertIn("exception_message_budget", result["cutoffs"])


class NodeAggregateSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="sb-node-aggregate-source-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.first_source = "throw new TypeError('first input failed');\n"
        self.second_source = "const marker = 1;\nthrow new RangeError('second input failed');\n"
        (self.root / "first.js").write_text(self.first_source)
        (self.root / "second.js").write_text(self.second_source)

    def test_selected_member_source_and_error_stay_associated_with_exact_raw_input(self):
        raw = "\ufeff" + aggregate().replace("\n", "\r\n")
        command = "DO NOT EXECUTE; touch AGGREGATE_COMMAND_RAN\r\n"
        result = locate_failure(self.root, raw, command)
        self.assertEqual(result["error_output"], raw)
        self.assertEqual(result["error_sha256"], hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(result["command"], command)
        self.assertEqual(result["terminal_exception"]["type"], "TypeError")
        self.assertEqual(result["terminal_exception"]["message"], "first input failed")
        self.assertEqual(result["terminal_exception"]["aggregate_parent_index"], 0)
        self.assertEqual([item["text"] for item in result["evidence"]], [self.first_source, self.second_source])
        self.assertTrue(any(item["title"] == "Review aggregate members separately" for item in result["guidance"]))
        self.assertFalse((self.root / "AGGREGATE_COMMAND_RAN").exists())

    def test_external_first_member_does_not_lend_its_message_to_selected_second_member(self):
        result = locate_failure(self.root, aggregate(first="/outside/first.js"))
        self.assertEqual(result["frames"][0]["status"], "outside_project")
        self.assertEqual(result["terminal_exception"]["type"], "RangeError")
        self.assertEqual(result["terminal_exception"]["message"], "second input failed")
        self.assertEqual(result["evidence"][0]["text"], self.second_source)

    def test_unsupported_nested_structure_is_not_read_and_has_visible_guidance(self):
        raw = ("AggregateError: outer\n  [errors]: [\n    AggregateError: nested {\n"
               "      [errors]: [\n        TypeError: inner\n            at first.js:1:1\n      ]\n    }\n  ]\n}\n")
        with patch("shake_bake.troubleshoot._read", side_effect=AssertionError("unsupported source must not be opened")):
            result = locate_failure(self.root, raw)
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["frames"][0]["status"], "node_aggregate_format_unsupported")
        self.assertIsNone(result["innermost_project_frame"])
        self.assertIn("could not be interpreted", result["guidance"][0]["title"])
        self.assertEqual(result["error_output"], raw)

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_generated_promise_any_and_explicit_aggregate_errors(self):
        # The test driver executes only its own disposable generated fixture;
        # production location receives stderr and never executes a command.
        sources = {
            "promise.mjs": "await Promise.any([Promise.reject(new TypeError('first input failed')), Promise.reject(new RangeError('second input failed'))]);\n",
            "explicit.cjs": "const errors = [new TypeError('first input failed'), new RangeError('second input failed')];\nthrow new AggregateError(errors, 'batch failed');\n",
            "limited.cjs": "Error.stackTraceLimit = 1;\nconst errors = [new TypeError('first input failed'), new RangeError('second input failed')];\nthrow new AggregateError(errors, 'batch failed');\n",
        }
        for name, source in sources.items():
            with self.subTest(name=name):
                path = self.root / name
                path.write_text(source)
                process = subprocess.run([shutil.which("node"), str(path)], cwd=self.root,
                                         capture_output=True, text=True, timeout=5)
                self.assertNotEqual(process.returncode, 0)
                result = locate_failure(self.root, process.stderr, "NEVER EXECUTE THIS RECORDED COMMAND")
                self.assertEqual(result["error_output"], process.stderr)
                self.assertEqual([item["type"] for item in result["exceptions"]],
                                 ["AggregateError", "TypeError", "RangeError"])
                project_frames = [frame for frame in result["frames"] if frame["status"] == "located"]
                self.assertEqual([frame["exception_index"] for frame in project_frames],
                                 [1, 2] if name == "promise.mjs" else [0, 1, 2])
                self.assertNotIn("node_aggregate_format_unsupported", result["cutoffs"])
                self.assertEqual(path.read_bytes(), source.encode())

    def generated_nested_result(self, *, cause=False, sibling=False):
        # Each module is a disposable synthetic fixture created by this test.
        # Real Node output places object framing after the member's stack,
        # which is the point at which provisional source claims must be revoked.
        member = self.root / "unsupported.cjs"
        member.write_text("module.exports = new TypeError('member with cause', {cause: new Error('inner cause')});\n"
                          if cause else "module.exports = new AggregateError([new TypeError('inner')], 'nested');\n")
        entry = self.root / "entry.cjs"
        source = "const member = require('./unsupported.cjs');\nthrow new AggregateError([member], 'outer');\n"
        allowed = {"entry.cjs"}
        if sibling:
            (self.root / "sibling.cjs").write_text("module.exports = new RangeError('supported sibling');\n")
            source = ("const sibling = require('./sibling.cjs');\nconst member = require('./unsupported.cjs');\n"
                      "throw new AggregateError([sibling, member], 'outer');\n")
            allowed.add("sibling.cjs")
        entry.write_text(source)
        # Keep all three stacks inside the production frame budget so the
        # sibling case tests revocation rather than incidental frame clipping.
        process = subprocess.run([shutil.which("node"), "--stack-trace-limit=3", str(entry)], cwd=self.root,
                                 capture_output=True, text=True, timeout=5)
        self.assertNotEqual(process.returncode, 0)
        reads = []

        def bounded_read(root, path):
            self.assertIn(path, allowed, "unsupported member source must never be read")
            reads.append(path)
            return _read(root, path)

        with patch("shake_bake.troubleshoot._read", side_effect=bounded_read):
            result = locate_failure(self.root, process.stderr)
        self.assertEqual(result["error_output"], process.stderr)
        self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])
        self.assertEqual(result["terminal_exception"]["message"], "outer")
        unsupported = [frame for frame in result["frames"] if frame.get("lookup_path") == str(member)]
        self.assertTrue(unsupported, "the actual member stack must be present to exercise revocation")
        for frame in unsupported:
            self.assertIsNone(frame["exception_index"])
            self.assertEqual(frame["status"], "node_aggregate_format_unsupported")
            self.assertIsNone(frame["evidence_id"])
        primary = next(frame for frame in result["frames"] if frame["frame_id"] == result["innermost_project_frame"])
        self.assertEqual((primary["path"], primary["line"]), ("entry.cjs", 3 if sibling else 2))
        return result, reads

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_nested_aggregate_revokes_member_frames_printed_before_its_properties(self):
        result, reads = self.generated_nested_result()
        self.assertEqual(reads, ["entry.cjs"])
        self.assertEqual({item["path"] for item in result["evidence"]}, {"entry.cjs"})

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_supported_sibling_survives_later_nested_member_revocation(self):
        result, reads = self.generated_nested_result(sibling=True)
        self.assertEqual(set(reads), {"entry.cjs", "sibling.cjs"})
        sibling = next(frame for frame in result["frames"] if frame.get("path") == "sibling.cjs")
        self.assertEqual(sibling["status"], "located")
        self.assertEqual(result["exceptions"][sibling["exception_index"]]["message"], "supported sibling")

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_cause_member_revokes_frames_printed_before_its_cause_property(self):
        result, reads = self.generated_nested_result(cause=True)
        self.assertEqual(reads, ["entry.cjs"])
        self.assertEqual({item["path"] for item in result["evidence"]}, {"entry.cjs"})

    @unittest.skipUnless(shutil.which("node"), "optional development Node.js unavailable")
    def test_actual_completed_sibling_remains_readable_before_a_primitive_rejection(self):
        sibling_source = "module.exports = new RangeError('supported sibling');\n"
        (self.root / "sibling.cjs").write_text(sibling_source)
        entry = self.root / "entry.cjs"
        entry.write_text("const sibling = require('./sibling.cjs');\nthrow new AggregateError([sibling, 'primitive rejection'], 'outer');\n")
        process = subprocess.run([shutil.which("node"), "--stack-trace-limit=3", str(entry)], cwd=self.root,
                                 capture_output=True, text=True, timeout=5)
        self.assertNotEqual(process.returncode, 0)
        result = locate_failure(self.root, process.stderr)
        sibling = next(frame for frame in result["frames"] if frame.get("path") == "sibling.cjs")
        self.assertEqual(sibling["status"], "located")
        self.assertEqual(result["exceptions"][sibling["exception_index"]]["message"], "supported sibling")
        self.assertIn(sibling_source, [item["text"] for item in result["evidence"]])
        self.assertIn("node_aggregate_format_unsupported", result["cutoffs"])
        self.assertEqual(result["error_output"], process.stderr)


if __name__ == "__main__":
    unittest.main()

"""Synthetic pytest report text; pytest is not a runtime or test dependency."""

import unittest

from shake_bake.contracts import Refusal
from shake_bake.pytest_formats import (MAX_ERROR_BYTES, MAX_EXCEPTIONS, MAX_FRAMES,
                                      MAX_MESSAGE_BYTES, MAX_RELATIONS, parse_pytest)


def section(title="FAILURES"):
    return f" {title} ".center(79, "=") + "\n"


def heading(title):
    return f" {title} ".center(79, "_") + "\n"


def long_failure(path="test_case.py", line=3, error="ValueError", message="invalid value",
                 statement="raise ValueError('invalid value')"):
    return (f"    def test_case():\n>       {statement}\nE       {error}: {message}\n\n"
            f"{path}:{line}: {error}\n")


AUTO = (section() + heading("test_total")
        + '    def test_total():\n>       assert total("many") == 3\n               ^^^^^^^^^^^^^\n\n'
          'test_counts.py:4: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\n'
          "value = 'many'\n\n    def total(value):\n>       return int(value)\n               ^^^^^^^^^^\n"
          "E       ValueError: invalid literal for int() with base 10: 'many'\n\ncounts.py:2: ValueError\n"
        + heading("test_other")
        + "    def test_other():\n>       assert 2 == 3\nE       assert 2 == 3\n\ntest_counts.py:7: AssertionError\n"
        + section("short test summary info")
        + "FAILED test_counts.py::test_total - ValueError: invalid literal for int() wit...\n"
          "FAILED test_counts.py::test_other - assert 2 == 3\n2 failed in 0.01s\n")

SHORT = (section() + heading("test_total")
         + 'test_counts.py:4: in test_total\n    assert total("many") == 3\n           ^^^^^^^^^^^^^\n'
           "counts.py:2: in total\n    return int(value)\n           ^^^^^^^^^^\n"
           "E   ValueError: invalid literal for int() with base 10: 'many'\n"
         + heading("test_other")
         + "test_counts.py:7: in test_other\n    assert 2 == 3\nE   assert 2 == 3\n"
         + section("short test summary info")
         + "FAILED test_counts.py::test_total - ValueError: invalid literal for int() wit...\n"
           "FAILED test_counts.py::test_other - assert 2 == 3\n")


class PytestFormatTests(unittest.TestCase):
    def test_default_and_long_source_first_blocks_keep_case_binding(self):
        result = parse_pytest(AUTO)
        self.assertEqual(result["format"], "pytest")
        self.assertEqual([(f["reported_path"], f["line"], f["chain_index"]) for f in result["frames"]],
                         [("test_counts.py", 4, 0), ("counts.py", 2, 0), ("test_counts.py", 7, 1)])
        self.assertEqual([f["statement"] for f in result["frames"]],
                         ['assert total("many") == 3', "return int(value)", "assert 2 == 3"])
        self.assertEqual([(e["type"], e["message"], e["chain_index"]) for e in result["exceptions"]],
                         [("ValueError", "invalid literal for int() with base 10: 'many'", 0),
                          ("AssertionError", "assert 2 == 3", 1)])
        self.assertEqual(result["last_chain"], 1)
        self.assertEqual(result["cutoffs"], [])
        self.assertEqual(result["chain_relations"], [])
        self.assertTrue(all(f["function"] is None for f in result["frames"]))

    def test_short_frames_precede_source_and_terminal_message(self):
        result = parse_pytest(SHORT)
        self.assertEqual([f["function"] for f in result["frames"]], ["test_total", "total", "test_other"])
        self.assertEqual([f["statement"] for f in result["frames"]],
                         ['assert total("many") == 3', "return int(value)", "assert 2 == 3"])
        self.assertEqual(result["exceptions"][-1]["type"], "AssertionError")
        self.assertEqual(result["exceptions"][-1]["message"], "assert 2 == 3")
        self.assertEqual(result["cutoffs"], [])

    def test_long_case_name_has_single_underscore_edges_not_a_traceback_separator(self):
        name = "test_" + "very_long_case_name_" * 8
        raw = (section() + heading("test_first") + long_failure("first.py")
               + f"_ {name} _\n" + long_failure("final.py"))
        result = parse_pytest(raw)
        self.assertEqual([f["chain_index"] for f in result["frames"]], [0, 1])
        self.assertEqual(result["last_chain"], 1)
        self.assertEqual(parse_pytest(AUTO)["last_chain"], 1)

    def test_error_setup_section_and_later_failure_are_independent(self):
        raw = (section("ERRORS") + heading("ERROR at setup of test_setup")
               + long_failure("fixtures.py", 2, "KeyError", "'setup'", "raise KeyError('setup')")
               + section() + heading("test_case") + long_failure())
        result = parse_pytest(raw)
        self.assertEqual([f["chain_index"] for f in result["frames"]], [0, 1])
        self.assertEqual(result["exceptions"][-1]["type"], "ValueError")
        self.assertEqual(result["last_chain"], 1)

    def test_direct_cause_keeps_related_blocks_in_the_same_case(self):
        raw = (section() + heading("test_chain")
               + long_failure("inner.py", 2, "KeyError", "'first'", "raise KeyError('first')")
               + "\nThe above exception was the direct cause of the following exception:\n\n"
               + long_failure("outer.py", 8, "RuntimeError", "last", "raise RuntimeError('last') from err"))
        result = parse_pytest(raw)
        self.assertEqual([f["chain_index"] for f in result["frames"]], [0, 1])
        self.assertEqual([e["message"] for e in result["exceptions"]], ["'first'", "last"])
        self.assertEqual(result["chain_relations"], [{"from_chain": 0, "to_chain": 1, "relation": "direct_cause"}])
        self.assertEqual(result["last_chain"], 1)

    def test_short_handling_chain_resets_exception_and_statement(self):
        raw = (section() + heading("test_chain")
               + "inner.py:2: in inner\n    raise ValueError('first')\nE   ValueError: first\n"
               + "During handling of the above exception, another exception occurred:\n"
               + "outer.py:9: in outer\n    raise TypeError('last')\nE   TypeError: last\n")
        result = parse_pytest(raw)
        self.assertEqual([e["message"] for e in result["exceptions"]], ["first", "last"])
        self.assertEqual(result["chain_relations"][0]["relation"], "during_handling")
        self.assertEqual(result["frames"][-1]["statement"], "raise TypeError('last')")

    def test_captured_stdout_stderr_and_logs_are_not_source_or_messages(self):
        for kind in ("stdout", "stderr", "log"):
            with self.subTest(kind=kind):
                raw = (section() + heading("test_case") + long_failure()
                       + f" Captured {kind} call ".center(79, "-") + "\n"
                       + "injected.py:99: in false\n    run()\nE   TypeError: fake\n"
                         "___________________ test_false ____________________\n"
                         ">       injected()\nE       RuntimeError: fake again\ninjected.py:100: RuntimeError\n"
                         "Traceback (most recent call last):\n  File \"injected.py\", line 80, in false\n"
                       + section("short test summary info") + "FAILED test_case.py::test_case\n")
                result = parse_pytest(raw)
                self.assertEqual([f["reported_path"] for f in result["frames"]], ["test_case.py"])
                self.assertEqual([e["message"] for e in result["exceptions"]], ["invalid value"])
                self.assertEqual(result["last_chain"], 0)

    def test_real_next_case_after_captured_output_is_not_omitted(self):
        raw = (section() + heading("test_first") + long_failure("first.py")
               + " Captured stdout call ".center(79, "-") + "\nprinted text\n"
               + heading("test_final") + long_failure("final.py", 8, "TypeError", "final"))
        result = parse_pytest(raw)
        self.assertEqual([f["reported_path"] for f in result["frames"]], ["first.py", "final.py"])
        self.assertEqual(result["exceptions"][-1]["message"], "final")
        self.assertEqual(result["last_chain"], 1)

    def test_captured_summary_and_section_banners_do_not_hide_the_final_case(self):
        for printed_banner in (section("short test summary info"), section(), section("ERRORS")):
            with self.subTest(banner=printed_banner):
                raw = (section() + heading("test_first") + long_failure("first.py")
                       + " Captured stdout call ".center(79, "-") + "\n" + printed_banner
                       + "E   TypeError: fake\n"
                       + heading("test_final") + long_failure("final.py", 8, "TypeError", "final"))
                result = parse_pytest(raw)
                self.assertEqual([f["reported_path"] for f in result["frames"]], ["first.py", "final.py"])
                self.assertEqual(result["exceptions"][-1]["message"], "final")
                self.assertEqual(result["last_chain"], 1)
                self.assertEqual(result["cutoffs"], [])

    def test_collection_syntax_error_E_file_source_and_caret_locate_the_project(self):
        raw = (section("ERRORS") + heading("ERROR collecting test_bad.py")
               + "/outside/ast.py:52: in parse\n    return compile(source, filename, mode, flags,\n"
                 'E     File "tests/test_bad.py", line 1\n'
                 "E       def test_broken(:\nE                       ^\nE   SyntaxError: invalid syntax\n")
        result = parse_pytest(raw)
        self.assertEqual([(f["reported_path"], f["line"]) for f in result["frames"]],
                         [("/outside/ast.py", 52), ("tests/test_bad.py", 1)])
        self.assertEqual(result["frames"][-1]["statement"], "def test_broken(:")
        self.assertEqual(result["exceptions"][-1]["type"], "SyntaxError")
        self.assertEqual(result["exceptions"][-1]["message"], "invalid syntax")
        self.assertEqual(result["cutoffs"], [])

    def test_E_file_alone_or_with_wrong_shape_is_an_explicit_gap(self):
        bodies = ("E   SyntaxError: invalid syntax\n",
                  "E       broken source\nE   SyntaxError: invalid syntax\n",
                  "E       broken source\nE          ^\nE   ValueError: wrong terminal\n",
                  "    broken source\nE          ^\nE   SyntaxError: invalid syntax\n")
        for body in bodies:
            with self.subTest(body=body):
                raw = (section("ERRORS") + heading("ERROR collecting test_bad.py")
                       + 'E     File "tests/test_bad.py", line 1\n' + body)
                result = parse_pytest(raw)
                self.assertEqual(result["frames"], [])
                self.assertIn("pytest_traceback_format_unsupported", result["cutoffs"])

    def test_captured_E_syntax_block_never_becomes_a_frame(self):
        raw = (section() + heading("test_case") + long_failure()
               + " Captured stdout call ".center(79, "-") + "\n"
                 'E     File "fake.py", line 8\nE       def broken(:\n'
                 "E                  ^\nE   SyntaxError: fake syntax\n")
        result = parse_pytest(raw)
        self.assertEqual([f["reported_path"] for f in result["frames"]], ["test_case.py"])
        self.assertEqual([e["type"] for e in result["exceptions"]], ["ValueError"])

    def test_short_summary_locations_never_become_frames(self):
        raw = (section() + heading("test_case") + long_failure()
               + section("short test summary info")
               + "FAILED foreign.py::test_other - ValueError: unrelated\n"
                 "foreign.py:99: in unrelated\n    break_it()\nE   RuntimeError: false\n")
        result = parse_pytest(raw)
        self.assertEqual([f["reported_path"] for f in result["frames"]], ["test_case.py"])
        self.assertEqual(result["exceptions"][-1]["message"], "invalid value")

    def test_requires_both_report_section_and_case_header_for_locations(self):
        for raw in (long_failure(), heading("test_case") + long_failure(), section() + long_failure(),
                    "test.py:5: in run\n    fail()\nE   ValueError: fail\n",
                    "prefix " + section() + heading("test_case") + long_failure()):
            with self.subTest(raw=raw[:40]):
                result = parse_pytest(raw)
                self.assertEqual(result["frames"], [])
                self.assertEqual(result["exceptions"], [])

    def test_unrelated_E_text_is_not_pytest(self):
        result = parse_pytest("E   ValueError: note\nE   assert false\nany.py:5: AssertionError\n")
        self.assertIsNone(result["format"])
        self.assertEqual(result["cutoffs"], [])

    def test_native_traceback_remains_standard_python(self):
        raw = (section() + heading("test_case") + "Traceback (most recent call last):\n"
               + '  File "test_case.py", line 3, in test_case\n    raise ValueError("value")\nValueError: value\n')
        result = parse_pytest(raw)
        self.assertIsNone(result["format"])
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["cutoffs"], [])

    def test_native_with_captured_output_does_not_fall_back_to_unsafe_full_log_parse(self):
        raw = (section() + heading("test_case") + "Traceback (most recent call last):\n"
               + '  File "test_case.py", line 3, in test_case\nValueError: value\n'
               + " Captured stdout call ".center(79, "-") + "\n"
               + 'Traceback (most recent call last):\n  File "fake.py", line 8, in run\nTypeError: fake\n')
        result = parse_pytest(raw)
        self.assertEqual(result["format"], "pytest")
        self.assertEqual(result["frames"], [])
        self.assertIn("pytest_traceback_format_unsupported", result["cutoffs"])

    def test_line_format_is_explicitly_unsupported_without_a_case_heading(self):
        result = parse_pytest(section() + "E   ValueError: fail\nproject.py:3: ValueError: fail\n")
        self.assertEqual(result["format"], "pytest")
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["exceptions"], [])
        self.assertIn("pytest_traceback_format_unsupported", result["cutoffs"])

    def test_no_traceback_summary_is_an_explicit_gap(self):
        result = parse_pytest(section("short test summary info") + "FAILED test_case.py::test_case\n")
        self.assertEqual(result["format"], "pytest")
        self.assertEqual(result["frames"], [])
        self.assertIn("pytest_traceback_format_unsupported", result["cutoffs"])

    def test_exception_group_does_not_flatten_tree_or_promote_earlier_case(self):
        raw = (section() + heading("test_first") + long_failure("first.py") + heading("test_group")
               + "  + Exception Group Traceback (most recent call last):\n"
                 '  |   File "group.py", line 2, in test_group\n'
                 "  | ExceptionGroup: group (2 sub-exceptions)\n    | ValueError: one\n    | TypeError: two\n")
        result = parse_pytest(raw)
        self.assertEqual([f["reported_path"] for f in result["frames"]], ["first.py"])
        self.assertEqual(result["last_chain"], 1)
        self.assertTrue(all(f["chain_index"] < result["last_chain"] for f in result["frames"]))
        self.assertIn("pytest_traceback_format_unsupported", result["cutoffs"])

    def test_partial_final_case_advances_final_chain_without_borrowing_message(self):
        raw = (section() + heading("test_first") + long_failure("first.py") + heading("test_partial")
               + "    def test_partial():\n>       missing()\nE       TypeError: partial\n")
        result = parse_pytest(raw)
        self.assertEqual(result["last_chain"], 1)
        self.assertEqual(len(result["exceptions"]), 1)
        self.assertEqual(result["exceptions"][0]["chain_index"], 0)
        self.assertEqual(result["frames"][0]["chain_index"], 0)
        self.assertIn("pytest_incomplete_case", result["cutoffs"])

    def test_long_location_requires_a_source_marker_and_not_arbitrary_paths(self):
        raw = (section() + heading("test_case")
               + "ignored.py:8: ValueError\nE       ValueError: ignored\n"
               + long_failure("real.py"))
        result = parse_pytest(raw)
        self.assertEqual([f["reported_path"] for f in result["frames"]], ["real.py"])

    def test_paths_remain_exact_and_unchecked_including_traversal_claims(self):
        path = "../outside/a file: copy.py"
        result = parse_pytest(section() + heading("test_case") + long_failure(path))
        frame = result["frames"][0]
        self.assertEqual(frame["reported_path"], path)
        self.assertEqual((frame["path"], frame["status"], frame["evidence_id"]), (None, "not_checked", None))
        self.assertEqual(frame["source_comparison"], "unknown")

    def test_exception_message_is_utf8_bounded_without_mutating_input(self):
        message = "é" * (MAX_MESSAGE_BYTES + 5)
        raw = section() + heading("test_case") + long_failure(message=message)
        before = raw.encode("utf-8")
        result = parse_pytest(raw)
        exception = result["exceptions"][0]
        self.assertEqual(exception["message_bytes"], len(message.encode("utf-8")))
        self.assertTrue(exception["message_truncated"])
        self.assertLessEqual(len(exception["message"].encode("utf-8")), MAX_MESSAGE_BYTES)
        self.assertIn("exception_message_budget", result["cutoffs"])
        self.assertEqual(raw.encode("utf-8"), before)

    def test_frame_and_exception_caps_retain_final_cases(self):
        raw = section() + "".join(heading(f"test_{i}") + long_failure(f"case_{i}.py", message=str(i))
                                  for i in range(MAX_FRAMES + 3))
        result = parse_pytest(raw)
        self.assertEqual(len(result["frames"]), MAX_FRAMES)
        self.assertEqual(len(result["exceptions"]), MAX_EXCEPTIONS)
        self.assertEqual(result["frames"][0]["reported_path"], "case_3.py")
        self.assertEqual(result["frames"][-1]["reported_path"], "case_22.py")
        self.assertEqual(result["frames"][-1]["frame_id"], "F23")
        self.assertEqual(result["exceptions"][-1]["message"], "22")
        self.assertEqual(result["last_chain"], 22)
        self.assertIn("frame_budget", result["cutoffs"])
        self.assertIn("exception_budget", result["cutoffs"])

    def test_relation_cap_retains_final_chains(self):
        blocks = []
        for i in range(MAX_RELATIONS + 3):
            if i:
                blocks.append("The above exception was the direct cause of the following exception:\n")
            blocks.append(long_failure(f"case_{i}.py", message=str(i)))
        result = parse_pytest(section() + heading("test_chain") + "".join(blocks))
        self.assertEqual(len(result["chain_relations"]), MAX_RELATIONS)
        self.assertEqual(result["chain_relations"][-1]["to_chain"], 22)
        self.assertEqual(result["last_chain"], 22)
        self.assertIn("chain_budget", result["cutoffs"])

    def test_csi_controls_bom_and_crlf_are_only_normalized_for_matching(self):
        raw = "\ufeff" + AUTO.replace("FAILURES", "\x1b[31mFAILURES\x1b[0m").replace("\n", "\r\n")
        before = raw.encode("utf-8")
        result = parse_pytest(raw)
        self.assertEqual(len(result["frames"]), 3)
        self.assertEqual(result["last_chain"], 1)
        self.assertEqual(raw.encode("utf-8"), before)

    def test_invalid_line_numbers_are_not_rewritten(self):
        for position in ("0", "-1", "01", "10000000000", "x"):
            with self.subTest(position=position):
                raw = section() + heading("test_case") + f"test.py:{position}: in run\n    fail()\nE   ValueError: fail\n"
                self.assertEqual(parse_pytest(raw)["frames"], [])

    def test_invalid_input_refuses_before_matching(self):
        for raw in (None, 12, b"failure", "bad\x00input", "\ud800", "a" * (MAX_ERROR_BYTES + 1)):
            with self.subTest(type=type(raw).__name__):
                with self.assertRaises(Refusal):
                    parse_pytest(raw)


if __name__ == "__main__":
    unittest.main()

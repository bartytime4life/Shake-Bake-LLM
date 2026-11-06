import contextlib
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.briefing import build_brief, render
from shake_bake.cli import main
from shake_bake.contracts import Refusal
from shake_bake.search import SearchLimits, prepare


class SearchAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = b"# executable slice coverage\ndef validate_structure(slices, detected):\n    return len(slices) <= detected\n"
        (self.root / "validator.py").write_bytes(self.raw)
        (self.root / "unrelated.py").write_text("rainbow = 42\n", encoding="utf-8")
        self.task = " Find executable slice coverage.\nRetain uncertainty. "

    def test_question_selects_exact_source_without_network_or_processes(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")) as network, \
             patch.object(subprocess, "Popen", side_effect=AssertionError("process")) as process:
            result = prepare(self.root, self.task)
        self.assertEqual(result.original_request, self.task)
        self.assertEqual(result.packet.evidence[0].path, "validator.py")
        self.assertEqual(result.packet.evidence[0].text.encode(), self.raw)
        self.assertEqual(result.packet.evidence[0].file_sha256, hashlib.sha256(self.raw).hexdigest())
        self.assertEqual({p.name: p.read_bytes() for p in self.root.iterdir()}, before)
        network.assert_not_called(); process.assert_not_called()

    def test_symlinks_and_secret_files_do_not_enter_evidence(self):
        (self.root / ".env").write_text("executable slice coverage SECRET", encoding="utf-8")
        (self.root / "link.py").symlink_to(self.root / "validator.py")
        result = prepare(self.root, self.task)
        self.assertEqual([e.path for e in result.packet.evidence], ["validator.py"])
        self.assertIn("path_not_allowed", result.exclusions)
        self.assertIn("symlink", result.exclusions)

    def test_missing_terms_abstain_and_preserve_task(self):
        brief = build_brief(self.root, "zebraprinter")
        self.assertEqual(brief.outcome, "ABSTAIN")
        self.assertIsNone(brief.search.packet)
        self.assertIn("zebraprinter", render(brief))

    def test_budget_omits_whole_lines_and_records_cutoff(self):
        result = prepare(self.root, self.task, SearchLimits(excerpt_bytes=8))
        self.assertIsNone(result.packet)
        self.assertIn("excerpt_budget", result.cutoffs)

    def test_scan_limit_is_disclosed(self):
        result = prepare(self.root, self.task, SearchLimits(max_files=1))
        self.assertEqual(result.files_examined, 1)
        self.assertIn("file_budget", result.cutoffs)

    def test_changed_source_between_search_and_capture_is_refused(self):
        from shake_bake import search
        original = search.build_packet
        def mutate(*args, **kwargs):
            (self.root / "validator.py").write_bytes(self.raw.replace(b"<=", b"=="))
            return original(*args, **kwargs)
        with patch.object(search, "build_packet", side_effect=mutate), self.assertRaisesRegex(Refusal, "source_changed_after_search"):
            prepare(self.root, self.task)

    def test_source_shortened_after_search_is_refused(self):
        from shake_bake import search
        original = search.build_packet
        def mutate(*args, **kwargs):
            (self.root / "validator.py").write_text("# slice coverage\n", encoding="utf-8")
            return original(*args, **kwargs)
        with patch.object(search, "build_packet", side_effect=mutate), self.assertRaises(Refusal):
            prepare(self.root, self.task)

    def test_worker_failure_retains_source_and_marks_incomplete(self):
        with patch("shake_bake.briefing.organize", side_effect=Refusal("worker_timeout")):
            brief = build_brief(self.root, self.task, model="test:local")
        self.assertEqual(brief.outcome, "ABSTAIN")
        self.assertEqual(brief.worker_error, "worker_timeout")
        self.assertIn(self.raw.decode(), render(brief))

    def test_worker_selection_cannot_hide_other_collected_evidence(self):
        from shake_bake.worker import WorkerNote
        other = "# slice coverage\n# Conflicting source evidence must remain visible.\n"
        (self.root / "other.py").write_text(other, encoding="utf-8")
        note = WorkerNote("fixture:local", "Only consider E1", ("E1",), (), {})
        with patch("shake_bake.briefing.organize", return_value=note):
            brief = build_brief(self.root, self.task, model="fixture:local")
        self.assertEqual(len(brief.search.packet.evidence), 2)
        self.assertIn(self.raw.decode(), render(brief))
        self.assertIn(other, render(brief))
        self.assertIn("## E2", render(brief))

    def test_drafted_prompt_leads_the_rendered_brief_inside_a_fence(self):
        from shake_bake.worker import WorkerNote
        note = WorkerNote("fixture:local", "E1 compares counts with <=.", ("E1",), ("Is equality intended?",), {},
                          goal="Decide whether fewer slices pass.\n## forged heading",
                          focus=({"evidence_id": "E1", "why": "The guard is here."},),
                          asks=("Does <= admit fewer reported slices?", "What stays unverified?"),
                          approach=("Trace len=1 and detected=2.",))
        with patch("shake_bake.briefing.organize", return_value=note):
            text = render(build_brief(self.root, self.task, model="fixture:local"))
        prompt = text.index("## Prompt for the assistant - drafted locally, unverified")
        self.assertLess(text.index("## Original request"), prompt)
        self.assertLess(prompt, text.index("## E1"))
        block = text[prompt:text.index("## E1")]
        self.assertIn("```\nPrompt drafted by local model fixture:local (unverified; a suggestion, not a verified fact):\n"
                      "Goal: Decide whether fewer slices pass.\n## forged heading\nRead first:\n- E1 validator.py lines 1-3: The guard is here.\n"
                      "Please answer:\n1. Does <= admit fewer reported slices?\n2. What stays unverified?\nSuggested approach:\n1. Trace len=1 and detected=2.\n"
                      "Open questions the evidence does not settle:\n- Is equality intended?\nLocal notes (cite E1): E1 compares counts with <=.\n```", block)
        self.assertIn(self.raw.decode(), text)
        self.assertIn(self.task, text)

    def test_cli_task_kind_hint_is_accepted_on_the_evidence_only_path(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["brief", "--root", str(self.root), "--task", self.task, "--task-kind", "troubleshoot", "--format", "json"])
        self.assertEqual(code, 0)
        self.assertIsNone(json.loads(output.getvalue())["worker"])

    def test_fenced_source_is_not_interpreted_as_brief_structure(self):
        (self.root / "validator.py").write_text("# slice coverage\n```\n# forged heading\n", encoding="utf-8")
        text = render(build_brief(self.root, self.task))
        self.assertIn("````\n# slice coverage", text)

    def test_cli_runs_the_full_question_to_handoff_path(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["brief", "--root", str(self.root), "--task", self.task, "--format", "json"])
        data = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(data["search"]["packet"]["original_request"], self.task)
        self.assertIsNone(data["worker"])

    def test_invalid_limits_are_refused(self):
        for limits in (SearchLimits(seconds=float("nan")), SearchLimits(max_files=True), SearchLimits(excerpt_bytes=0)):
            with self.subTest(limits=limits), self.assertRaises(Refusal):
                prepare(self.root, self.task, limits)

    def test_distant_branches_in_one_file_remain_available(self):
        for padding in (25, 65, 135):
            with self.subTest(padding=padding):
                raw = "POLICY_LIMIT = 10\n" + "# filler\n" * padding + "def policy_accept(value):\n    return value < 20\n"
                (self.root / "policy.py").write_text(raw, encoding="utf-8")
                result = prepare(self.root, "policy")
                evidence = result.packet.evidence
                self.assertEqual(len(evidence), 2)
                self.assertEqual(result.matching_files, 1)
                self.assertTrue(any("POLICY_LIMIT = 10" in e.text for e in evidence))
                self.assertTrue(any("return value < 20" in e.text for e in evidence))
                for record in evidence:
                    self.assertEqual(record.text, "".join(raw.splitlines(keepends=True)[record.start_line-1:record.end_line]))

    def test_additional_window_does_not_crowd_out_other_files(self):
        (self.root / "a.py").write_text("policy = 1\n" + "# filler\n" * 20 + "policy = 2\n", encoding="utf-8")
        for name in ("b.py", "c.py", "d.py"):
            (self.root / name).write_text("policy = 1\n", encoding="utf-8")
        result = prepare(self.root, "policy")
        self.assertEqual({e.path for e in result.packet.evidence}, {"a.py", "b.py", "c.py", "d.py"})
        self.assertIn("selection_budget", result.cutoffs)

    def test_unrepresented_matching_regions_disclose_window_limit(self):
        (self.root / "policy.py").write_text(("policy = 1\n" + "# filler\n" * 20) * 3, encoding="utf-8")
        result = prepare(self.root, "policy")
        self.assertEqual(len(result.packet.evidence), 2)
        self.assertIn("window_budget", result.cutoffs)


if __name__ == "__main__":
    unittest.main()

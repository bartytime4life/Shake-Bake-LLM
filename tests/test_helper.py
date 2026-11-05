import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.helper import HelperSession
from test_worker import stub_server


@unittest.skipUnless(sys.platform == "linux", "Linux task-supervision profile")
class HelperAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = "# executable slice coverage\ndef validate(slices, detected):\n    return len(slices) <= detected\n"
        (self.root / "validator.py").write_text(self.source, encoding="utf-8")
        self.task = " Inspect executable slice coverage.\nKeep contradictory evidence visible. "

    def session(self, **kwargs):
        helper = HelperSession({"demo": self.root}, **kwargs)
        self.addCleanup(helper.close)
        return helper

    def wait_for_result(self, helper, identifier):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            result = helper.get_result(identifier)
            if result["state"] != "RUNNING":
                return result
            time.sleep(0.005)
        self.fail("task did not finish")

    def test_real_child_returns_preparation_and_fetches_exact_snapshot(self):
        helper = self.session(evidence_only=True)
        self.assertEqual(helper.list_projects()["projects"], ["demo"])
        self.assertNotIn(str(self.root), json.dumps(helper.list_projects()))
        identifier = helper.start_task("demo", self.task)["task_id"]
        result = self.wait_for_result(helper, identifier)
        self.assertEqual(result["state"], "DONE")
        self.assertEqual(result["original_request"], self.task)
        self.assertEqual(result["result_kind"], "preparation_result")
        self.assertFalse(result["final_answer_ready"])
        self.assertTrue(result["requires_host_reasoning"])
        self.assertNotIn("text", result["evidence"][0])
        evidence = helper.fetch_evidence(identifier, "E1")
        self.assertEqual(evidence["text"], self.source)
        self.assertEqual(evidence["excerpt_sha256"], hashlib.sha256(self.source.encode()).hexdigest())

    def test_unknown_project_refused_before_any_child(self):
        helper = self.session(evidence_only=True)
        for value in ("../outside", str(self.root), "other"):
            with self.subTest(value=value), self.assertRaisesRegex(Refusal, "project_not_allowed"):
                helper.start_task(value, self.task)
        self.assertEqual(helper._jobs, {})

    def test_explicit_helper_mode_is_required(self):
        with self.assertRaisesRegex(Refusal, "explicit_helper_mode_required"):
            HelperSession({"demo": self.root})
        with self.assertRaises(Refusal):
            HelperSession({"demo": self.root}, evidence_only=True, model="fixture:local")

    def test_model_mode_delegates_to_simulated_ollama(self):
        with stub_server() as (port, requests):
            helper = self.session(model="fixture:local", port=port)
            identifier = helper.start_task("demo", self.task)["task_id"]
            result = self.wait_for_result(helper, identifier)
        self.assertEqual(result["state"], "DONE")
        self.assertEqual(result["mode"], "ollama_helper")
        self.assertEqual(result["worker"]["label"], "unverified_worker_interpretation")
        self.assertEqual([p for p, _ in requests], ["/api/show", "/api/chat"])
        self.assertFalse(result["final_answer_ready"])

    def test_confident_wrong_note_cannot_become_final_answer_or_hide_source(self):
        wrong = json.dumps({"summary": "I am completely certain this is safe.", "evidence_ids": ["E1"], "questions": []})
        with stub_server(content=wrong) as (port, _):
            helper = self.session(model="fixture:local", port=port)
            identifier = helper.start_task("demo", self.task)["task_id"]
            result = self.wait_for_result(helper, identifier)
        self.assertFalse(result["final_answer_ready"])
        self.assertTrue(result["requires_host_reasoning"])
        self.assertEqual(result["verification"]["worker_notes"], "unverified_interpretation")
        self.assertEqual(helper.fetch_evidence(identifier, "E1")["text"], self.source)

    def test_busy_refusal_does_not_start_second_worker(self):
        with stub_server(delay=0.15) as (port, _):
            helper = self.session(model="fixture:local", port=port)
            identifier = helper.start_task("demo", self.task)["task_id"]
            with self.assertRaisesRegex(Refusal, "helper_busy"):
                helper.start_task("demo", self.task)
            self.assertEqual(len(helper._jobs), 1)
            helper.cancel_task(identifier)

    def test_cancel_terminates_only_owned_runner_and_reaps_it(self):
        with stub_server(delay=0.15) as (port, _):
            helper = self.session(model="fixture:local", port=port)
            identifier = helper.start_task("demo", self.task)["task_id"]
            job = helper._jobs[identifier]
            result = helper.cancel_task(identifier)
            self.assertEqual(result["state"], "CANCELLED")
            self.assertIsNotNone(job.process.poll())
            self.assertTrue(all(stream.closed for stream in job.streams))
            self.assertEqual(helper.get_result(identifier)["state"], "CANCELLED")

    def test_shutdown_terminates_runner_and_rejects_new_work(self):
        with stub_server(delay=0.15) as (port, _):
            helper = self.session(model="fixture:local", port=port)
            identifier = helper.start_task("demo", self.task)["task_id"]
            process = helper._jobs[identifier].process
            helper.close()
            self.assertIsNotNone(process.poll())
            with self.assertRaisesRegex(Refusal, "helper_closed"):
                helper.start_task("demo", self.task)

    def test_captured_snapshot_does_not_masquerade_as_live_source(self):
        helper = self.session(evidence_only=True)
        identifier = helper.start_task("demo", self.task)["task_id"]
        self.wait_for_result(helper, identifier)
        (self.root / "validator.py").write_text("changed", encoding="utf-8")
        evidence = helper.fetch_evidence(identifier, "E1")
        self.assertEqual(evidence["text"], self.source)
        self.assertEqual(evidence["freshness"], "captured_snapshot_not_live_revalidation")
        evidence["text"] = "mutated client copy"
        self.assertEqual(helper.fetch_evidence(identifier, "E1")["text"], self.source)

    def test_unknown_evidence_and_handles_refused(self):
        helper = self.session(evidence_only=True)
        with self.assertRaises(Refusal):
            helper.get_result("unknown")
        identifier = helper.start_task("demo", self.task)["task_id"]
        self.wait_for_result(helper, identifier)
        for value in ("E0", "E99", "../private", "E2"):
            with self.subTest(value=value), self.assertRaises(Refusal):
                helper.fetch_evidence(identifier, value)

    def test_worker_failure_keeps_evidence_and_abstains(self):
        with stub_server(remote=True) as (port, _):
            helper = self.session(model="fixture:local", port=port)
            identifier = helper.start_task("demo", self.task)["task_id"]
            result = self.wait_for_result(helper, identifier)
        self.assertEqual(result["outcome"], "ABSTAIN")
        self.assertIsNone(result["worker"])
        self.assertEqual(helper.fetch_evidence(identifier, "E1")["text"], self.source)

    def test_no_match_never_claims_a_final_answer(self):
        helper = self.session(evidence_only=True)
        identifier = helper.start_task("demo", "zebraprinter")["task_id"]
        result = self.wait_for_result(helper, identifier)
        self.assertEqual(result["outcome"], "ABSTAIN")
        self.assertFalse(result["final_answer_ready"])
        self.assertNotIn("evidence", result)

    def test_search_gaps_remain_visible_without_evidence(self):
        helper = self.session(evidence_only=True)
        request = " ".join("zebraprinter" + chr(97 + i) for i in range(17))
        identifier = helper.start_task("demo", request)["task_id"]
        result = self.wait_for_result(helper, identifier)
        self.assertEqual(result["outcome"], "ABSTAIN")
        self.assertIn("query_term_budget", result["cutoffs"])
        self.assertEqual(result["files_examined"], 1)
        self.assertEqual(result["matching_files"], 0)
        self.assertIn("exclusions", result)

    def test_completed_jobs_are_bounded_and_old_handles_expire(self):
        helper = self.session(evidence_only=True)
        identifiers = []
        for _ in range(9):
            identifier = helper.start_task("demo", self.task)["task_id"]
            identifiers.append(identifier)
            self.wait_for_result(helper, identifier)
        self.assertEqual(len(helper._jobs), 8)
        with self.assertRaisesRegex(Refusal, "unknown_or_expired_task"):
            helper.get_result(identifiers[0])

    def test_inspected_cwd_cannot_shadow_the_preparation_package(self):
        fake = self.root / "shake_bake"
        fake.mkdir()
        (fake / "__init__.py").write_text('raise RuntimeError("inspected package was imported")\n', encoding="utf-8")
        helper = self.session(evidence_only=True)
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            identifier = helper.start_task("demo", self.task)["task_id"]
            result = self.wait_for_result(helper, identifier)
        finally:
            os.chdir(previous)
        self.assertEqual(result["state"], "DONE")
        self.assertEqual(result["original_request"], self.task)

    def test_project_tmpdir_does_not_put_task_streams_in_project(self):
        with patch("shake_bake.helper.tempfile.gettempdir", return_value=str(self.root)):
            helper = self.session(evidence_only=True)
        self.assertNotEqual(helper._scratch, self.root)
        self.assertNotIn(self.root, helper._scratch.parents)
        identifier = helper.start_task("demo", self.task)["task_id"]
        self.assertEqual(self.wait_for_result(helper, identifier)["state"], "DONE")


if __name__ == "__main__":
    unittest.main()

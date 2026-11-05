import copy
import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.doctor import inspect, inspect_model
from shake_bake.worker import generation_settings
from test_worker import stub_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
spec = importlib.util.spec_from_file_location("model_trial", ROOT / "benchmarks/model_trial.py")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


class StartupReadiness(unittest.TestCase):
    def test_invalid_startup_ports_refuse_before_creating_workers(self):
        from shake_bake.gui import main
        with patch("shake_bake.gui.Controller", side_effect=AssertionError("worker started")), patch("sys.stderr", new_callable=io.StringIO):
            for args in (["--port", "-1"], ["--ollama-port", "65536"]):
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)

    def test_default_checks_do_not_contact_model_or_collect_source(self):
        with patch("shake_bake.doctor.local_inventory", side_effect=AssertionError("model contacted")), \
             patch("shake_bake.collector.build_packet", side_effect=AssertionError("source collected")):
            result = inspect(gui_port=45937)
        self.assertEqual(result["ollama"]["status"], "NOT_CHECKED")
        self.assertIsNone(result["model_accuracy"])
        self.assertIsNone(result["environment"]["gpu_throughput"])
        self.assertTrue(all(c["status"] == "PASS" for c in result["checks"] if c["name"] != "Workbench port"))

    def test_busy_port_and_missing_local_service_are_reported(self):
        with socket.socket() as busy:
            busy.bind(("127.0.0.1", 0))
            result = inspect(gui_port=busy.getsockname()[1])
        self.assertFalse(result["gui_startup_checks_passed"])
        with patch("shake_bake.doctor.local_inventory", side_effect=Refusal("worker_transport_failed")):
            result = inspect(check_ollama=True)
        self.assertEqual(result["ollama"]["code"], "worker_transport_failed")

    def test_model_preflight_is_metadata_only_and_refuses_remote_model(self):
        with stub_server() as (port, requests):
            result = inspect_model("fixture:local", port)
        self.assertEqual(result["reported_digest"], "a" * 64)
        self.assertEqual([path for path, _ in requests], ["/api/tags", "/api/version", "/api/show", "/api/tags", "/api/version"])
        self.assertFalse(result["generation_requested"])
        with stub_server(remote=True) as (port, requests):
            with self.assertRaisesRegex(Refusal, "local_model_metadata_required"):
                inspect_model("fixture:local", port)
        self.assertNotIn("/api/chat", [path for path, _ in requests])


class ModelTrialAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "run"

    def diagnostic(self, **kwargs):
        return trial.run_trial(self.folder, evidence_only=True, case_ids=["boundary"], **kwargs)

    def files(self):
        return (self.folder / "trial.json").read_bytes(), json.loads((self.folder / "reviews.json").read_text())

    def complete_review(self, reviews, *, supported=True):
        reviews["reviewer"] = "TEST REVIEW ONLY"
        for entry in reviews["entries"]:
            entry.update(supported_handoff=supported, critical_misses=0, unsupported_claims=0,
                         unsupported_critical_claims=0, useful_abstention=False, notes="TEST ONLY: controlling source span reviewed.")

    def test_diagnostic_keeps_accuracy_unset_and_checkpoints_each_attempt(self):
        with patch("socket.create_connection", side_effect=AssertionError("network")):
            receipt = self.diagnostic(repeats=2)
        self.assertEqual(receipt["status"], "FINISHED")
        self.assertEqual(receipt["completed_attempt_count"], 2)
        self.assertEqual(receipt["unique_case_count"], 1)
        self.assertEqual(len((self.folder / "attempts.jsonl").read_text().splitlines()), 2)
        raw, reviews = self.files()
        result = trial.score(raw, reviews)
        self.assertIsNone(result["reviewed_handoff_accuracy"])
        self.assertEqual(result["usage"]["attempts_without_usage"], 2)
        self.assertFalse(result["auto_promotion_allowed"])

    def test_actual_http_trial_pins_model_identity_and_records_settings_and_usage(self):
        with stub_server() as (port, requests):
            receipt = trial.run_trial(self.folder, model="fixture:local", port=port, case_ids=["boundary"])
        self.assertEqual(receipt["status"], "FINISHED")
        self.assertEqual(receipt["failed_attempt_count"], 0)
        worker = receipt["attempts"][0]["brief"]["worker"]
        self.assertEqual(worker["observed_model_digest"], "a" * 64)
        self.assertEqual(receipt["requested_worker_settings"]["options"], generation_settings())
        self.assertEqual(receipt["requested_worker_settings"]["keep_alive"],0)
        self.assertIs(receipt["requested_worker_settings"]["think"],False)
        self.assertEqual(worker["observed_runtime_version"],receipt["model_preflight"]["runtime_version"])
        self.assertEqual(worker["requested_configuration"],receipt["requested_worker_settings"])
        self.assertEqual(worker["usage"]["eval_count"], 12)
        for path, payload in requests:
            if path == "/api/chat":
                self.assertNotIn("grading-keys", json.dumps(payload))
        raw, reviews = self.files()
        self.complete_review(reviews)
        result = trial.score(raw, reviews)
        self.assertEqual(result["semantic_model_accuracy"], 1.0)
        self.assertEqual(result["unique_cases"], 1)
        self.assertFalse(result["auto_promotion_allowed"])

    def test_digest_change_stops_without_substitution_and_keeps_attempt(self):
        with stub_server(after_digest="b" * 64) as (port, requests):
            receipt = trial.run_trial(self.folder, model="fixture:local", port=port, repeats=3, case_ids=["boundary"])
        self.assertEqual(receipt["status"], "STOPPED")
        self.assertEqual(receipt["stop_reason"], "qualified_model_digest_changed")
        self.assertEqual(len(receipt["attempts"]), 1)
        self.assertEqual(sum(path == "/api/chat" for path, _ in requests), 1)
        raw, reviews = self.files()
        self.complete_review(reviews, supported=False)
        self.assertIsNone(trial.score(raw, reviews)["semantic_model_accuracy"])

    def test_failed_attempts_stay_in_accuracy_denominator(self):
        with stub_server(override={"done_reason": "length"}) as (port, _):
            receipt = trial.run_trial(self.folder, model="fixture:local", port=port, repeats=2, case_ids=["boundary"])
        self.assertEqual(receipt["failed_attempt_count"], 2)
        raw, reviews = self.files()
        self.complete_review(reviews, supported=False)
        result = trial.score(raw, reviews)
        self.assertEqual(result["semantic_model_accuracy"], 0.0)
        self.assertEqual(result["usage"]["attempts_without_usage"], 2)
        self.assertFalse(result["usage"]["full_task_total_known"])
        reviews["entries"][0]["supported_handoff"] = True
        with self.assertRaisesRegex(Refusal, "failed_attempt_cannot_be_correct"):
            trial.score(raw, reviews)

    def test_timeout_stops_before_next_request_because_daemon_work_may_continue(self):
        original = trial.lab.run_cases
        def timeout(**kwargs):
            result = original(case_ids=kwargs["case_ids"])
            result["cases"][0]["brief"]["worker_error"] = "worker_timeout"
            return result
        with patch.object(trial.lab, "run_cases", side_effect=timeout) as calls:
            receipt = self.diagnostic(repeats=3)
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(receipt["status"], "STOPPED")
        self.assertEqual(receipt["stop_reason"], "worker_timeout")
        self.assertEqual(receipt["failed_attempt_count"], 1)

    def test_runtime_change_stops_trial_without_dropping_failed_attempt(self):
        with stub_server(after_runtime="9.0.0") as (port, requests):
            receipt=trial.run_trial(self.folder,model="fixture:local",port=port,repeats=2,case_ids=["boundary"])
        self.assertEqual(receipt["status"],"STOPPED")
        self.assertEqual(receipt["stop_reason"],"worker_runtime_changed")
        self.assertEqual(receipt["failed_attempt_count"],1)
        self.assertEqual(len(receipt["attempts"]),1)
        self.assertEqual(sum(path=="/api/chat" for path,_ in requests),1)

    def test_partial_or_invalid_reviews_cannot_become_a_pass(self):
        self.diagnostic(repeats=2)
        raw, reviews = self.files()
        self.complete_review(reviews)
        reviews["entries"][0]["critical_misses"] = None
        self.assertIsNone(trial.score(raw, reviews)["reviewed_handoff_accuracy"])
        self.complete_review(reviews)
        reviews["entries"][0]["critical_misses"] = True
        with self.assertRaisesRegex(Refusal, "invalid_review_value"):
            trial.score(raw, reviews)
        self.complete_review(reviews)
        reviews["entries"][1] = copy.deepcopy(reviews["entries"][0])
        with self.assertRaisesRegex(Refusal, "invalid_review_entries"):
            trial.score(raw, reviews)
        _, reviews = self.files()
        reviews["trial_sha256"] = "0" * 64
        with self.assertRaisesRegex(Refusal, "review_receipt_mismatch"):
            trial.score(raw, reviews)

    def test_interrupt_leaves_completed_checkpoints_and_no_full_accuracy(self):
        original = trial.lab.run_cases
        calls = 0
        def interrupt(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return original(**kwargs)
        with patch.object(trial.lab, "run_cases", side_effect=interrupt):
            receipt = self.diagnostic(repeats=3)
        self.assertEqual(receipt["status"], "INTERRUPTED")
        self.assertEqual(len(receipt["attempts"]), 1)
        raw, reviews = self.files()
        self.assertIsNone(trial.score(raw, reviews)["reviewed_handoff_accuracy"])

    def test_changed_source_is_stopped_before_model_call(self):
        with patch.object(trial.lab, "tree_hash", side_effect=["original", "changed"]), \
             patch.object(trial.lab, "run_cases", side_effect=AssertionError("should not run")):
            receipt = self.diagnostic()
        self.assertEqual(receipt["status"], "STOPPED")
        self.assertEqual(receipt["stop_reason"], "fixture_changed")
        self.assertFalse(receipt["attempts"])

    def test_no_overwrites_and_case_and_repeat_limits(self):
        self.diagnostic()
        before = (self.folder / "trial.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.diagnostic()
        self.assertEqual((self.folder / "trial.json").read_bytes(), before)
        for kwargs in ({"repeats": 4}, {"case_ids": ["not-a-case"]}, {"case_ids": ["boundary", "boundary"]}):
            with self.assertRaises(Refusal):
                trial.run_trial(Path(self.temp.name) / "other", evidence_only=True, **kwargs)
        with self.assertRaisesRegex(Refusal, "trial_output_inside_dataset"):
            trial.run_trial(trial.lab.LAB / "new-run", evidence_only=True)


if __name__ == "__main__":
    unittest.main()

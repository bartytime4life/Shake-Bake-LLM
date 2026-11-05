"""Temporary synthetic data tests the private-dataset mechanism, not accuracy."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from test_worker import stub_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
import model_trial as trial
import run_task_lab as lab


class ExternalDatasetAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.dataset = self.base / "private-cases"
        self.fixture = self.dataset / "fixtures" / "boundary"
        self.fixture.mkdir(parents=True)
        (self.fixture / "ranges.py").write_text("# Boundary check\ndef contains(start, end, position):\n    return start <= position < end\n")
        self.manifest = {"schema_version": "1", "dataset_id": "SYNTHETIC-TEST-ONLY", "split": "held_out", "cases": [
            {"id": "boundary", "task": "Explain the boundary check for position 20 and end 20.", "limits": {}}]}
        self.keys = {"schema_version": "1", "never_send_to_worker": True, "cases": {"boundary": {
            "anchors": [{"path": "ranges.py", "contains": "position < end"}], "required_cutoffs": [],
            "required_findings": ["PRIVATE_GRADING_SENTINEL: end is excluded."]}}}
        self.write_inputs()

    def write_inputs(self):
        (self.dataset / "manifest.json").write_text(json.dumps(self.manifest))
        (self.dataset / "grading-keys.json").write_text(json.dumps(self.keys))

    def run_trial(self, **kwargs):
        return trial.run_trial(self.base / "run", dataset=self.dataset, evidence_only=True, **kwargs)

    def test_external_identity_is_recorded_but_no_accuracy_or_promotion_is_inferred(self):
        with patch("socket.create_connection", side_effect=AssertionError("network")):
            receipt = self.run_trial(repeats=2)
        self.assertEqual(receipt["status"], "FINISHED")
        self.assertEqual(receipt["dataset"]["dataset_id"], "SYNTHETIC-TEST-ONLY")
        self.assertTrue(receipt["dataset"]["split_is_owner_declared"])
        self.assertEqual(receipt["unique_case_count"], 1)
        self.assertEqual(receipt["completed_attempt_count"], 2)
        self.assertFalse(receipt["auto_promotion_allowed"])
        self.assertIsNone(receipt["native_host_baseline"])
        self.assertIsNone(receipt["semantic_model_accuracy"])
        raw = (self.base / "run/trial.json").read_bytes()
        reviews = json.loads((self.base / "run/reviews.json").read_text())
        self.assertEqual(trial.score(raw, reviews)["review_status"], "PENDING")

    def test_grading_keys_stay_outside_actual_model_request(self):
        with stub_server() as (port, requests):
            result = lab.run_cases(dataset=self.dataset, model="fixture:local", port=port)
        self.assertEqual(result["mechanical_passes"], 1)
        chats = [payload for route, payload in requests if route == "/api/chat"]
        self.assertEqual(len(chats), 1)
        serialized = json.dumps(chats)
        self.assertNotIn("PRIVATE_GRADING_SENTINEL", serialized)
        self.assertNotIn("grading-keys", serialized)
        self.assertNotIn("SYNTHETIC-TEST-ONLY", serialized)
        self.assertIn("position < end", serialized)

    def test_changed_manifest_stops_before_another_attempt(self):
        original = lab.run_cases
        def mutate(**kwargs):
            result = original(**kwargs)
            self.manifest["cases"][0]["task"] = "Different boundary question"
            self.write_inputs()
            return result
        with patch.object(lab, "run_cases", side_effect=mutate) as calls:
            receipt = self.run_trial(repeats=2)
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(receipt["stop_reason"], "trial_inputs_changed")
        self.assertEqual(receipt["completed_attempt_count"], 1)

    def test_changed_keys_stop_before_model_preparation(self):
        original = lab.tree_hash
        def mutate(root):
            result = original(root)
            self.keys["cases"]["boundary"]["anchors"][0]["contains"] = "changed"
            self.write_inputs()
            return result
        with patch.object(lab, "tree_hash", side_effect=mutate), \
             patch.object(lab, "run_cases", side_effect=AssertionError("preparation started")):
            receipt = self.run_trial()
        self.assertEqual(receipt["stop_reason"], "trial_inputs_changed")
        self.assertFalse(receipt["attempts"])

    def test_key_drift_during_final_attempt_is_retained_and_cannot_finish_as_a_pass(self):
        original = lab.build_brief
        def mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.dataset / "grading-keys.json").write_text("changed during preparation")
            return result
        with patch.object(lab, "build_brief", side_effect=mutate):
            receipt = self.run_trial()
        self.assertEqual(receipt["status"], "STOPPED")
        self.assertEqual(receipt["stop_reason"], "trial_inputs_changed")
        self.assertEqual(receipt["completed_attempt_count"], 1)
        self.assertEqual(receipt["failed_attempt_count"], 1)
        self.assertFalse(receipt["attempts"][0]["dataset_unchanged"])

    def test_path_traversal_duplicate_cases_and_invalid_limits_refuse(self):
        for changes in ({"id": "../outside"}, {"limits": {"unexpected": True}}, {"limits": {"max_files": 0}}):
            original = dict(self.manifest["cases"][0])
            self.manifest["cases"][0].update(changes)
            self.write_inputs()
            with self.subTest(changes=changes), self.assertRaises(Refusal):
                lab.load_dataset(self.dataset)
            self.manifest["cases"][0] = original
        self.manifest["cases"].append(dict(self.manifest["cases"][0]))
        self.write_inputs()
        with self.assertRaisesRegex(Refusal, "invalid_dataset_case"):
            lab.load_dataset(self.dataset)

    def test_symlink_fixture_or_grading_key_is_refused_without_network(self):
        secret = self.base / "owner-file.txt"
        secret.write_text("PRIVATE_GRADING_SENTINEL")
        (self.fixture / "linked.txt").symlink_to(secret)
        with patch("socket.create_connection", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(Refusal, "dataset_links"):
                self.run_trial()
        (self.fixture / "linked.txt").unlink()
        (self.dataset / "grading-keys.json").unlink()
        (self.dataset / "grading-keys.json").symlink_to(secret)
        with self.assertRaises(Refusal):
            lab.load_dataset(self.dataset)

    def test_outputs_cannot_enter_dataset_and_previous_runs_are_not_overwritten(self):
        with self.assertRaisesRegex(Refusal, "trial_output_inside_dataset"):
            trial.run_trial(self.dataset / "results", dataset=self.dataset, evidence_only=True)
        self.run_trial()
        before = (self.base / "run/trial.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_trial()
        self.assertEqual((self.base / "run/trial.json").read_bytes(), before)

    def test_bundle_cannot_be_relabeled_held_out(self):
        self.assertEqual(lab.load_dataset(lab.LAB)[3]["split"], "development")
        with patch.object(lab, "__file__", str(self.base / "benchmarks/run_task_lab.py")):
            with self.assertRaisesRegex(Refusal, "held_out_dataset_must_be_outside_checkout"):
                lab.load_dataset(self.dataset)


if __name__ == "__main__":
    unittest.main()

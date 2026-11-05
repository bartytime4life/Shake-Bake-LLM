"""Qualification records here are fabricated test data, not model results."""

import contextlib
import copy
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.cli import main
from shake_bake.contracts import Refusal
from shake_bake.routing import assist, choose, pipeline_id, validate_policy
from test_worker import stub_server


def policy_fixture():
    return {"schema_version": "1", "enabled": True,
            "baselines": {"code": {"dataset_id": "test-held-out-v1", "host_baseline_id": "simulated-host", "case_count": 20, "accuracy": 0.9}},
            "profiles": [{"id": "test-profile", "task_kind": "code", "model": "fixture:local", "status": "qualified",
                          "digest": "a" * 64, "pipeline_id": pipeline_id(),
                          "evaluation": {"dataset_id": "test-held-out-v1", "host_baseline_id": "simulated-host", "case_count": 20,
                                         "split": "held_out", "reviewed": True, "critical_misses": 0, "unsupported_critical_claims": 0,
                                         "accuracy": 0.95, "median_latency_ms": 100}}]}


class RoutingAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = "# executable slice coverage\ndef validate(slices, detected):\n    return len(slices) <= detected\n"
        (self.root / "validator.py").write_text(self.source, encoding="utf-8")
        self.task = "Inspect executable slice coverage."
        self.policy = policy_fixture()
        self.policy_path = self.base / "routing.json"

    def save_policy(self):
        self.policy_path.write_text(json.dumps(self.policy), encoding="utf-8")
        return self.policy_path

    def test_best_recorded_accuracy_wins_over_lower_latency(self):
        fast = copy.deepcopy(self.policy["profiles"][0])
        fast.update(id="fast-profile", model="fixture:fast")
        fast["evaluation"].update(accuracy=0.9, median_latency_ms=1)
        self.policy["profiles"].append(fast)
        decision = choose(self.policy, "code", {"fixture:local": "a" * 64, "fixture:fast": "a" * 64})
        self.assertEqual(decision.profile_id, "test-profile")
        self.assertIn("highest recorded accuracy", decision.why)

    def test_critical_errors_and_below_baseline_records_never_qualify(self):
        for change in ({"critical_misses": 1}, {"unsupported_critical_claims": 1}, {"accuracy": 0.85}):
            with self.subTest(change=change):
                policy = policy_fixture()
                policy["profiles"][0]["evaluation"].update(change)
                self.assertEqual(choose(policy, "code", {"fixture:local": "a" * 64}).mode, "evidence_only")

    def test_development_unreviewed_or_different_trials_are_rejected(self):
        for change in ({"split": "development"}, {"reviewed": False}, {"dataset_id": "other"}, {"case_count": 19}):
            with self.subTest(change=change):
                policy = policy_fixture()
                policy["profiles"][0]["evaluation"].update(change)
                self.assertEqual(choose(policy, "code", {"fixture:local": "a" * 64}).mode, "evidence_only")

    def test_stale_pipeline_and_changed_digest_are_rejected(self):
        self.assertEqual(choose(self.policy, "code", {"fixture:local": "b" * 64}).reason, "qualified_model_unavailable")
        self.assertEqual(choose(self.policy, "code", {"fixture:local": "a" * 64}, current_pipeline="b" * 64).reason, "no_qualified_profile")

    def test_off_switch_retains_source_and_contacts_no_service(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            decision, brief = assist(self.root, self.task, "code", policy_path=None, disabled=True)
        self.assertEqual(decision.reason, "local_ai_disabled")
        self.assertEqual(brief.outcome, "ABSTAIN")
        self.assertIn(self.source, "".join(e.text for e in brief.search.packet.evidence))

    def test_global_off_switch_contacts_no_service(self):
        self.policy["enabled"] = False
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            decision, _ = assist(self.root, self.task, "code", policy_path=self.save_policy())
        self.assertEqual(decision.reason, "local_ai_disabled")

    def test_shipped_candidate_policy_never_contacts_a_model(self):
        path = Path(__file__).resolve().parents[1] / "examples/routing-policy.json"
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            decision, brief = assist(self.root, self.task, "code", policy_path=path)
        self.assertEqual(decision.reason, "no_qualified_profile")
        self.assertIsNotNone(brief.search.packet)

    def test_real_http_route_checks_digest_and_returns_unverified_note(self):
        with stub_server() as (port, requests):
            decision, brief = assist(self.root, self.task, "code", policy_path=self.save_policy(), port=port)
        self.assertEqual(decision.mode, "local_model")
        self.assertEqual(brief.worker.observed_model_digest, "a" * 64)
        self.assertEqual(brief.worker.label, "unverified_worker_interpretation")
        self.assertEqual([p for p, _ in requests], ["/api/tags", "/api/tags", "/api/show", "/api/version", "/api/chat", "/api/tags", "/api/version"])
        self.assertFalse(any(payload and "messages" in payload for path, payload in requests if path != "/api/chat"))

    def test_identity_change_after_inference_discards_note_and_keeps_source(self):
        with stub_server(after_digest="b" * 64) as (port, _):
            decision, brief = assist(self.root, self.task, "code", policy_path=self.save_policy(), port=port)
        self.assertEqual(decision.reason, "qualified_model_digest_changed")
        self.assertEqual(decision.attempted_model, "fixture:local")
        self.assertEqual(decision.attempted_profile_id, "test-profile")
        self.assertEqual(brief.outcome, "ABSTAIN")
        self.assertIsNone(brief.worker)
        self.assertEqual(brief.search.packet.evidence[0].text, self.source)

    def test_policy_inside_inspected_source_is_not_trusted(self):
        path = self.root / "routing.json"
        path.write_text(json.dumps(self.policy), encoding="utf-8")
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            decision, brief = assist(self.root, self.task, "code", policy_path=path)
        self.assertEqual(decision.reason, "routing_policy_inside_source")
        self.assertIsNotNone(brief.search.packet)

    def test_changed_initial_inventory_prevents_source_submission(self):
        with stub_server(inventory={"fixture:local": "b" * 64}) as (port, requests):
            decision, brief = assist(self.root, self.task, "code", policy_path=self.save_policy(), port=port)
        self.assertEqual(decision.reason, "qualified_model_unavailable")
        self.assertEqual([path for path, _ in requests], ["/api/tags"])
        self.assertIsNotNone(brief.search.packet)

    def test_disabled_or_failed_profiles_are_rejected_without_inventory_calls(self):
        for disabled in (True, False):
            self.policy = policy_fixture()
            if disabled:
                self.policy["profiles"][0]["status"] = "disabled"
            else:
                self.policy["profiles"][0]["evaluation"]["critical_misses"] = 1
            with self.subTest(disabled=disabled), patch.object(socket, "create_connection", side_effect=AssertionError("network")):
                decision, brief = assist(self.root, self.task, "code", policy_path=self.save_policy())
            self.assertEqual(decision.reason, "no_qualified_profile")
            self.assertIsNone(brief.worker)
            self.assertIsNotNone(brief.search.packet)

    def test_invalid_policy_keeps_source_without_network(self):
        self.policy_path.write_text('{"enabled":true,"enabled":false}', encoding="utf-8")
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            decision, brief = assist(self.root, self.task, "code", policy_path=self.policy_path)
        self.assertEqual(decision.mode, "evidence_only")
        self.assertIsNotNone(brief.search.packet)

    def test_malformed_scores_and_cloud_tags_are_refused(self):
        for value in (True, float("nan"), -1, 2, 10 ** 1000):
            policy = policy_fixture()
            policy["profiles"][0]["evaluation"]["accuracy"] = value
            with self.subTest(value=value), self.assertRaises(Refusal):
                validate_policy(policy)
        self.policy["profiles"][0]["model"] = "fixture:cloud"
        with self.assertRaises(Refusal):
            validate_policy(self.policy)

    def test_cli_explains_missing_qualification_without_claiming_final_answer(self):
        path = Path(__file__).resolve().parents[1] / "examples/routing-policy.json"
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            code = main(["assist", "--root", str(self.root), "--task", self.task, "--task-kind", "code", "--policy", str(path), "--format", "json"])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 3)
        self.assertFalse(result["final_answer_ready"])
        self.assertTrue(result["requires_host_reasoning"])
        self.assertEqual(result["routing"]["reason"], "no_qualified_profile")


if __name__ == "__main__":
    unittest.main()

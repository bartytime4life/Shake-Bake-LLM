"""Synthetic candidate trials through the recovered application's real child."""

from pathlib import Path
import time
import unittest
from unittest.mock import patch

from shake_bake.collector import build_packet
from shake_bake.contracts import Refusal, Selection
from shake_bake.gui import Controller, DEMO
from shake_bake.worker import organize
from test_worker import stub_server

CANDIDATE = {"model": "fixture:local", "digest": "a" * 64, "acknowledged": True}
TASK = {"project_id": "starter-demo", "task": "Find executable slice coverage.", "task_kind": "code"}


def completed(controller, identifier):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        result = controller.call("result", identifier)
        if result["state"] != "RUNNING":
            return result
        time.sleep(.01)
    raise AssertionError("synthetic trial did not finish")


class CandidateWorkbenchTests(unittest.TestCase):
    def controller(self, **kwargs):
        controller = Controller({"starter-demo": DEMO}, **kwargs)
        self.addCleanup(controller.close)
        return controller

    def test_owner_launch_flag_is_required(self):
        controller = self.controller()
        with self.assertRaisesRegex(Refusal, "candidate_trial_not_allowed"):
            controller.call("start", {**TASK, "candidate": CANDIDATE})
        self.assertEqual(controller.call("state")["recent"], [])

    def test_acknowledgement_digest_and_shape_cannot_be_bypassed(self):
        controller = self.controller(allow_trials=True)
        for candidate in ({**CANDIDATE, "acknowledged": False}, {**CANDIDATE, "digest": "wrong"}, {**CANDIDATE, "root": "/etc"}):
            with self.subTest(candidate=candidate), self.assertRaises(Refusal):
                controller.call("start", {**TASK, "candidate": candidate})
        self.assertEqual(controller.call("state")["recent"], [])

    def test_real_child_keeps_exact_source_and_candidate_label(self):
        before = {p.name:p.read_bytes() for p in DEMO.iterdir() if p.is_file()}
        with stub_server() as (port, requests):
            controller = self.controller(allow_trials=True, port=port)
            started = controller.call("start", {**TASK, "candidate": CANDIDATE})
            result = completed(controller, started["task_id"])
        self.assertEqual(result["state"], "DONE", result)
        self.assertEqual(result["original_request"], TASK["task"])
        self.assertEqual(result["routing"]["mode"], "candidate_trial")
        self.assertIsNone(result["routing"]["profile_id"])
        self.assertFalse(result["final_answer_ready"])
        self.assertEqual(result["worker"]["observed_model_digest"], "a" * 64)
        self.assertTrue(result["evidence"])
        self.assertEqual(result["project_id"], TASK["project_id"])
        chat = next(body for path, body in requests if path == "/api/chat")
        self.assertIs(chat["think"], False)
        self.assertEqual(chat["keep_alive"], 0)
        self.assertEqual(before, {p.name:p.read_bytes() for p in DEMO.iterdir() if p.is_file()})

    def test_changed_digest_discards_notes_and_retains_evidence(self):
        with stub_server(after_digest="b" * 64) as (port, _):
            controller = self.controller(allow_trials=True, port=port)
            started = controller.call("start", {**TASK, "candidate": CANDIDATE})
            result = completed(controller, started["task_id"])
        self.assertIsNone(result["worker"])
        self.assertEqual(result["worker_error"], "qualified_model_digest_changed")
        self.assertTrue(result["evidence"])
        self.assertFalse(result["final_answer_ready"])

    def test_global_pause_blocks_candidate_and_inventory_without_calls(self):
        controller = self.controller(allow_trials=True)
        controller.call("settings", {"enabled": False})
        with patch("shake_bake.gui.local_inventory") as inventory:
            self.assertEqual(controller.call("inventory")["state"], "paused")
        inventory.assert_not_called()
        with self.assertRaisesRegex(Refusal, "candidate_trial_not_allowed"):
            controller.call("start", {**TASK, "candidate": CANDIDATE})

    def test_returned_thinking_is_not_accepted_as_a_note(self):
        packet = build_packet(DEMO, "Find coverage", (Selection("validator.py", 1, 6),))
        with stub_server(override={"message":{"content":'{}',"thinking":"untrusted reasoning"}}) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_invalid_response"):
                organize(packet, "fixture:local", port=port)


if __name__ == "__main__":
    unittest.main()

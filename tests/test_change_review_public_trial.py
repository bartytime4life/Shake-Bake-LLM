import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
import change_review_public_trial as trial


class PublicChangeReviewTrialTests(unittest.TestCase):
    def test_public_host_enables_native_retrieval(self):
        args = trial.public_host_args(Path("/tmp/source"), Path("/tmp/answer"))
        self.assertIn("features.shell_tool=true", args)
        self.assertIn("features.code_mode_host=true", args)
        self.assertIn("features.code_mode=true", args)
        self.assertIn("permissions.trial.network.enabled=false", args)

    def test_public_prompt_preserves_task_and_diff_for_both_arms(self):
        row = {"task": "Fix the status", "exact_diff": "diff --git a/x b/x\n+value"}
        native = trial.public_prompt(row, None)
        prepared = trial.public_prompt(row, "packet")
        for prompt in (native, prepared):
            self.assertIn(row["task"], prompt)
            self.assertIn(row["exact_diff"], prompt)
            self.assertIn("untrusted", prompt)
            self.assertIn("native shell tool", prompt)
            self.assertIn("Do not execute source or tests", prompt)
        self.assertNotIn("packet", native)
        self.assertIn("packet", prepared)

    def test_plan_is_balanced_and_has_distinct_attempts(self):
        rows = trial.plan()
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({row["attempt_id"] for row in rows}), 8)
        for case in ("actuator-fault-status", "msgraph-readme-config"):
            for arm in ("native", "prepared"):
                self.assertEqual(sum(row["case_id"] == case and row["arm"] == arm for row in rows), 2)

    def test_action_audit_requires_completed_identical_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            events = [
                {"type": "thread.started"}, {"type": "turn.started"},
                {"type": "item.started", "item": {"id": "one", "type": "command_execution", "command": "rg -n x file.py"}},
                {"type": "item.completed", "item": {"id": "one", "type": "command_execution", "command": "rg -n x file.py",
                                                    "status": "completed", "exit_code": 0, "aggregated_output": "file.py:1:x\n"}},
                {"type": "turn.completed", "usage": {"input_tokens": 4}},
            ]
            path.write_text("\n".join(json.dumps(item) for item in events) + "\n")
            result = trial.parse_actions(path)
            self.assertEqual(result["actions"], [{"command": "rg -n x file.py", "exit_code": 0, "output_bytes": 12}])
            self.assertEqual(result["usage"], {"input_tokens": 4})
            events[3]["item"]["command"] = "cat secret"
            path.write_text("\n".join(json.dumps(item) for item in events) + "\n")
            with self.assertRaisesRegex(ValueError, "changed_host_command_identity"):
                trial.parse_actions(path)
            events[3]["item"]["type"] = "mcp_tool_call"
            path.write_text("\n".join(json.dumps(item) for item in events) + "\n")
            with self.assertRaisesRegex(ValueError, "unexpected_host_action"):
                trial.parse_actions(path)

    def test_fixture_identity_refuses_links_and_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "source.py"
            path.write_bytes(b"value = 1\n")
            row = {"files": [{"path": "source.py", "sha256": trial.sha(path.read_bytes()), "bytes": path.stat().st_size}]}
            self.assertEqual(len(trial.verify_root(root, row)), 64)
            path.write_bytes(b"value = 2\n")
            with self.assertRaisesRegex(ValueError, "public_fixture_identity_mismatch"):
                trial.verify_root(root, row)
            path.write_bytes(b"value = 1\n")
            (root / "link.py").symlink_to(path)
            with self.assertRaisesRegex(Exception, "dataset_links_or_special_files_refused"):
                trial.verify_root(root, row)


if __name__ == "__main__":
    unittest.main()

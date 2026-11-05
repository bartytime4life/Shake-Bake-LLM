"""Offline validation of synthetic host traces; these tests never call Codex."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("codex_host_smoke", ROOT / "integration/codex_host_smoke.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def fixture():
    identifier = "a" * 32
    events = []
    def call(tool, args, result):
        events.append({"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "shake_bake", "tool": tool,
            "arguments": args, "status": "completed", "error": None, "result": {"structured_content": result}}})
    call("list_projects", {}, {"projects": ["starter-demo"], "local_ai_paused": True})
    call("start_task", {"project_id": "not-approved", "task": smoke.TASK, "task_kind": "code"}, {"outcome": "DENY", "code": "project_not_permitted"})
    call("start_task", {"project_id": "starter-demo", "task": smoke.TASK, "task_kind": "code"}, {"task_id": identifier, "state": "RUNNING"})
    records = []
    for index, name in enumerate(("validator.py", "readme.md"), 1):
        raw = (smoke.DEMO / name).read_bytes()
        records.append({"evidence_id": f"E{index}", "path": name, "start_line": 1, "end_line": len(raw.decode().splitlines()),
                        "file_sha256": hashlib.sha256(raw).hexdigest(), "excerpt_sha256": hashlib.sha256(raw).hexdigest(), "text": raw.decode()})
    call("get_result", {"task_id": identifier}, {"state": "DONE", "original_request": smoke.TASK, "entry_point": "assistant",
        "final_answer_ready": False, "requires_host_reasoning": True, "worker": None, "routing": {"reason": "local_ai_disabled"},
        "evidence": [{key: record[key] for key in ("evidence_id", "path", "start_line", "end_line", "file_sha256")} for record in records]})
    for record in records:
        call("fetch_evidence", {"task_id": identifier, "evidence_id": record["evidence_id"]}, record)
    call("cancel_task", {"task_id": identifier}, {"task_id": identifier, "state": "DONE"})
    events.append({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}})
    answer = {"answer": "TEST ONLY: validator.py:6 accepts 1 <= 2; readme.md:3-5 establishes no test run.",
              "accepted_mismatch": {"reported_count": 1, "detected_count": 2}, "evidence_paths": ["validator.py:6", "readme.md:3-5"],
              "tests_executed": False, "helper_final_answer_ready": False, "denied_project_code": "project_not_permitted",
              "limitations": ["TEST ONLY: captured synthetic source."]}
    return events, answer


class HostSmokeTraceAcceptance(unittest.TestCase):
    def test_complete_synthetic_trace_is_accepted_without_calling_host(self):
        events, answer = fixture()
        with patch("subprocess.Popen", side_effect=AssertionError("host started")):
            result = smoke.validate_trace(events, answer)
        self.assertEqual(result["tool_calls"], 7)
        self.assertEqual(result["source_bytes"], 455)
        self.assertTrue(result["original_task_preserved"])

    def test_correct_answer_without_evidence_or_with_wrong_hash_is_rejected(self):
        events, answer = fixture()
        del events[4]
        with self.assertRaisesRegex(ValueError, "exact_evidence_not_fetched"):
            smoke.validate_trace(events, answer)
        events, answer = fixture()
        events[4]["item"]["result"]["structured_content"]["text"] = "invented source"
        with self.assertRaisesRegex(ValueError, "captured_bytes_changed"):
            smoke.validate_trace(events, answer)

    def test_host_paraphrasing_or_new_scope_does_not_count_as_original_request_preservation(self):
        for change in ({"task": smoke.TASK + " changed"}, {"project_id": "another-project"}):
            events, answer = fixture()
            events[2]["item"]["arguments"].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "original_task_or_scope_changed"):
                smoke.validate_trace(events, answer)

    def test_unrelated_tool_calls_and_shell_execution_are_rejected(self):
        for item in ({"type": "command_execution"}, {"type": "mcp_tool_call", "server": "other", "tool": "read"}):
            for event_type in ("item.started", "item.completed"):
                events, answer = fixture()
                events.insert(0, {"type": event_type, "item": item})
                with self.subTest(item=item, event_type=event_type), self.assertRaises(ValueError):
                    smoke.validate_trace(events, answer)
        for extra in ({"type": "error"}, {"type": "turn.failed"},
                      {"type": "item.started", "item": {"id": "unfinished", "type": "mcp_tool_call", "server": "shake_bake", "tool": "start_task"}}):
            events, answer = fixture()
            events.insert(0, extra)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                smoke.validate_trace(events, answer)

    def test_missing_refusal_worker_use_or_completion_claim_is_rejected(self):
        events, answer = fixture()
        events[1]["item"]["result"]["structured_content"] = {"task_id": "unexpected", "state": "RUNNING"}
        with self.assertRaisesRegex(ValueError, "project_refusal_not_observed"):
            smoke.validate_trace(events, answer)
        events, answer = fixture()
        events[3]["item"]["result"]["structured_content"]["worker"] = {"summary": "unexpected inference"}
        with self.assertRaisesRegex(ValueError, "preparation_boundary_changed"):
            smoke.validate_trace(events, answer)
        events, answer = fixture()
        answer["tests_executed"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_completion_claim"):
            smoke.validate_trace(events, answer)

    def test_cancellation_and_task_identity_must_match_the_completed_job(self):
        events, answer = fixture()
        events[6]["item"]["result"]["structured_content"]["state"] = "CANCELLED"
        with self.assertRaisesRegex(ValueError, "terminal_cancellation_not_confirmed"):
            smoke.validate_trace(events, answer)
        events, answer = fixture()
        events[3]["item"]["arguments"]["task_id"] = "other"
        with self.assertRaisesRegex(ValueError, "result_identity_mismatch"):
            smoke.validate_trace(events, answer)

    def test_equal_counts_do_not_satisfy_the_required_accepted_mismatch(self):
        events, answer = fixture()
        answer["accepted_mismatch"]["reported_count"] = 2
        with self.assertRaisesRegex(ValueError, "incorrect_concrete_mismatch"):
            smoke.validate_trace(events, answer)
        for citations in ([], ["validator.py:99", "readme.md:1"], ["validator.py:1", "readme.md:1"]):
            events, answer = fixture()
            answer["evidence_paths"] = citations
            with self.subTest(citations=citations), self.assertRaises(ValueError):
                smoke.validate_trace(events, answer)

    def test_run_configuration_is_temporary_and_disables_unrelated_actions(self):
        with patch.dict(os.environ, {"CODEX_HOME": "/synthetic/auth-home", "CODEX_THREAD_ID": "synthetic-parent", "PYTHONPATH": "unsafe"}):
            environment = smoke.clean_environment()
        self.assertEqual(environment["CODEX_HOME"], "/synthetic/auth-home")
        self.assertNotIn("CODEX_THREAD_ID", environment)
        self.assertNotIn("PYTHONPATH", environment)
        args = smoke.host_arguments("codex", Path("/test/workspace"), Path("/test/output"), Path("/test/connection.json"))
        options = tomllib.loads("\n".join(args[index+1] for index, value in enumerate(args) if value == "-c"))
        self.assertFalse(options["features"]["shell_tool"])
        self.assertFalse(options["features"]["apps"])
        self.assertFalse(options["features"]["plugins"])
        self.assertFalse(options["features"]["multi_agent"])
        self.assertEqual(options["mcp_servers"]["shake_bake"]["enabled_tools"], list(smoke.TOOLS))
        self.assertIn("--ignore-user-config", args)
        self.assertIn("--ephemeral", args)
        self.assertNotIn("--model", args)

    def test_missing_login_stays_blocked_without_starting_a_service_or_model(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            with patch.object(smoke.shutil, "which", return_value="codex"), \
                 patch.object(smoke.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)), \
                 patch.object(smoke.subprocess, "Popen", side_effect=AssertionError("process started")):
                result = smoke.run(output)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["failure"], "codex_login_required")
            self.assertTrue(result["private_connection_cleaned"])
            self.assertEqual(result["local_model_calls"], 0)
            with self.assertRaises(FileExistsError):
                smoke.run(output)


if __name__ == "__main__":
    unittest.main()

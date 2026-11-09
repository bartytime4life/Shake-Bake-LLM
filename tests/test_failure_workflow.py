"""Actual owner HTTP, trusted child and scoped project connection checks."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_gui
from shake_bake.contracts import Refusal


class FailureWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client = test_gui.WorkbenchAcceptance(methodName="runTest")
        self.client.setUp()
        self.addCleanup(self.client.doCleanups)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = 'def count(value):\n    return int(value)\n'
        (self.root / "parse.py").write_text(self.source)
        self.client.authenticate()

    def connect(self):
        status, _, raw = self.client.request("POST", "/api/projects", {"label": "Actual chosen folder", "path": str(self.root)})
        self.assertEqual(status, 200, raw)
        return json.loads(raw)["project_id"]

    def test_explicit_folder_connection_and_real_child_locate_exact_source(self):
        project = self.connect()
        error = f'Traceback (most recent call last):\r\n  File "{self.root}/parse.py", line 2, in count\r\n    return int(value)\r\nValueError: invalid literal\r\n'
        with patch("shake_bake.gui.local_inventory", side_effect=AssertionError("No model calls")):
            status, _, raw = self.client.request("POST", "/api/troubleshoot", {
                "project_id": project, "error_output": error, "command": "DO NOT RUN THIS"})
        self.assertEqual(status, 200, raw)
        result = json.loads(raw)
        self.assertEqual(result["error_output"], error)
        self.assertEqual(result["command"], "DO NOT RUN THIS")
        self.assertEqual(result["frames"][0]["source_comparison"], "match")
        self.assertEqual(result["evidence"][0]["text"], self.source)
        self.assertEqual((self.root / "parse.py").read_text(), self.source)
        self.assertEqual(list(self.root.iterdir()), [self.root / "parse.py"])

    def test_large_escaped_output_is_preserved_without_fake_source(self):
        project = self.connect()
        error = "Unrecognized run output\n" + "\x01" * 60000
        status, _, raw = self.client.request("POST", "/api/troubleshoot", {
            "project_id": project, "error_output": error, "command": ""})
        self.assertEqual(status, 200, raw[:100])
        result = json.loads(raw)
        self.assertEqual(result["error_output"], error)
        self.assertFalse(result["source_located"])
        self.assertEqual(result["evidence"], [])

    def test_control_heavy_exception_preserves_exact_error_with_clipped_metadata(self):
        project = self.connect()
        error = "ValueError: " + "\x01" * 60000
        status, _, raw = self.client.request("POST", "/api/troubleshoot", {
            "project_id": project, "error_output": error, "command": ""})
        self.assertEqual(status, 200, raw[:100])
        result = json.loads(raw)
        self.assertEqual(result["error_output"], error)
        self.assertTrue(result["supported_format"])
        self.assertFalse(result["source_located"])
        self.assertEqual(result["evidence"], [])
        terminal = result["terminal_exception"]
        self.assertEqual(terminal["type"], "ValueError")
        self.assertTrue(terminal["message_truncated"])
        self.assertLessEqual(len(terminal["message"].encode("utf-8")), 2048)
        self.assertEqual(terminal["message_bytes"], 60000)
        self.assertEqual(result["exceptions"][-1], terminal)
        self.assertIn("exception_message_budget", result["cutoffs"])

    def test_both_new_owner_routes_require_csrf_and_same_origin(self):
        for path, value in (("/api/projects", {"label": "Denied", "path": str(self.root)}),
                            ("/api/troubleshoot", {"project_id": "starter-demo", "error_output": "ValueError: error", "command": ""})):
            with self.subTest(path=path):
                self.assertEqual(self.client.request("POST", path, value, headers={"X-SB-CSRF": "wrong"})[0], 403)
                self.assertEqual(self.client.request("POST", path, value, headers={"Origin": "https://invalid.test"})[0], 403)

    def test_unapproved_root_cannot_be_selected_in_error_request_or_adapter(self):
        before = dict(self.client.controller.projects)
        status, _, _ = self.client.request("POST", "/api/troubleshoot", {
            "project_id": str(self.root), "error_output": "ValueError: error", "command": ""})
        self.assertEqual(status, 400)
        with self.assertRaises(Refusal):
            self.client.controller.call("adapter", {"method": "connect_project", "arguments": {
                "label": "Denied", "path": str(self.root)}, "projects": ("starter-demo",)})
        self.assertEqual(self.client.controller.projects, before)

    def test_new_source_cannot_contain_private_service_settings(self):
        protected = self.root / "private-settings"
        self.client.controller._protected_paths.append(protected)
        status, _, raw = self.client.request("POST", "/api/projects", {"label": "Wrong root", "path": str(self.root)})
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(raw)["error"], "project_contains_private_settings")


if __name__ == "__main__":
    unittest.main()

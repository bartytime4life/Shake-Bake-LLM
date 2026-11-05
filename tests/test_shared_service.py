"""Real private-file / loopback bridge tests; SDK and model inference separate."""

import http.client
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.gui import Controller, DEFAULT_POLICY, DEMO, WorkbenchServer
from shake_bake.shared import ConnectionPublication, SharedClient, load_connection
from shake_bake.worker import _request


class SharedServiceAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.other = self.directory / "other-source"; self.other.mkdir()
        (self.other / "source.py").write_text("# independent source\n")
        self.controller = Controller({"starter-demo": DEMO, "private": self.other}, DEFAULT_POLICY)
        self.server = WorkbenchServer(("127.0.0.1", 0), self.controller, adapter_projects=("starter-demo",))
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.01), daemon=True)
        self.thread.start()
        self.connection_file = self.directory / "connection.json"
        self.publication = ConnectionPublication(self.connection_file, self.server.server_port, self.server.adapter_token,
                                                 self.controller.projects.values())
        self.client = SharedClient(self.connection_file)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.client.close(); self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.publication.close(); self.controller.close()
        self.assertFalse(self.thread.is_alive())

    def wait_result(self, identifier):
        for _ in range(100):
            result = self.client.get_result(identifier)
            if result.get("state") != "RUNNING":
                return result
            time.sleep(.01)
        self.fail("shared preparation did not finish")

    def raw(self, *, token=None, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        try:
            hdr = {"Content-Type": "application/json"}
            if token is not None: hdr["Authorization"] = "Bearer " + token
            hdr.update(headers or {})
            connection.request("POST", "/api/helper", body=json.dumps(body or {"method": "list_projects", "arguments": {}}), headers=hdr)
            response = connection.getresponse(); raw = response.read()
            return response.status, json.loads(raw)
        finally:
            connection.close()

    def test_private_connection_and_project_listing_hide_token_and_host_paths(self):
        self.assertEqual(self.connection_file.stat().st_mode & 0o777, 0o600)
        listed = self.client.list_projects()
        self.assertEqual(listed["projects"], ["starter-demo"])
        self.assertNotIn(str(self.other), json.dumps(listed))
        self.assertNotIn(self.server.adapter_token, json.dumps(listed))
        state = self.controller.call("state")
        self.assertNotIn(self.server.adapter_token, json.dumps(state))

    def test_adapter_job_is_the_same_job_visible_in_gui_and_fetches_exact_evidence(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://example.invalid:1", "OLLAMA_HOST": "https://example.invalid"}):
            started = self.client.start_task("starter-demo", "Find executable slice coverage.", task_kind="troubleshoot")
            result = self.wait_result(started["task_id"])
        self.assertEqual(result["state"], "DONE", result)
        self.assertEqual(result["entry_point"], "assistant")
        self.assertEqual(result["task_kind"], "troubleshoot")
        self.assertFalse(result["final_answer_ready"])
        self.assertEqual(result["routing"]["reason"], "no_qualified_profile")
        self.assertNotIn("text", result["evidence"][0])
        exact = self.client.fetch_evidence(started["task_id"], "E1")
        visible = self.controller.call("result", started["task_id"])
        self.assertEqual(exact["text"], visible["evidence"][0]["text"])
        self.assertEqual(self.controller.call("state")["recent"][0]["task_id"], started["task_id"])

    def test_gui_pause_applies_to_adapter_jobs_without_inventory_or_model_calls(self):
        self.controller.call("settings", {"enabled": False})
        self.assertTrue(self.client.list_projects()["local_ai_paused"])
        started = self.client.start_task("starter-demo", "Find coverage.")
        result = self.wait_result(started["task_id"])
        self.assertEqual(result["routing"]["reason"], "local_ai_disabled")
        self.assertIsNone(result["worker"])
        self.assertTrue(result["evidence"])

    def test_gui_origin_job_is_observable_through_the_same_scoped_adapter(self):
        started = self.controller.call("start", {"project_id": "starter-demo", "task": "Find coverage.", "task_kind": "code"})
        result = self.wait_result(started["task_id"])
        self.assertEqual(result["entry_point"], "workspace")
        self.assertEqual(result["snapshot_id"], self.controller.call("result", started["task_id"])["snapshot_id"])

    def test_single_job_bound_and_gui_pause_cancel_an_adapter_model_job(self):
        from test_routing import policy_fixture
        from test_worker import stub_server
        with stub_server(delay=.1) as (port, requests):
            policy = self.directory / "routing.json"; policy.write_text(json.dumps(policy_fixture()))
            self.controller.close()
            self.controller = Controller({"starter-demo": DEMO, "private": self.other}, policy, port)
            self.server.controller = self.controller
            started = self.client.start_task("starter-demo", "Find executable slice coverage.")
            with self.assertRaisesRegex(Refusal, "helper_busy"):
                self.controller.call("start", {"project_id": "starter-demo", "task": "Find coverage.", "task_kind": "code"})
            self.controller.call("settings", {"enabled": False})
            result = self.client.get_result(started["task_id"])
            self.assertEqual(result["state"], "CANCELLED")
            self.assertIsNotNone(self.controller._session._jobs[started["task_id"]].process.poll())
            next_job = self.client.start_task("starter-demo", "Find coverage.")
            self.assertEqual(self.wait_result(next_job["task_id"])["routing"]["reason"], "local_ai_disabled")

    def test_adapter_cannot_widen_projects_models_or_access_unshared_jobs(self):
        denied = self.client.start_task("private", "Find source.")
        self.assertEqual(denied["code"], "project_not_permitted")
        private = self.controller.call("start", {"project_id": "private", "task": "Find source", "task_kind": "code"})
        self.assertEqual(self.client.get_result(private["task_id"])["code"], "task_not_permitted")
        self.assertEqual(self.client.cancel_task(private["task_id"])["code"], "task_not_permitted")
        status, value = self.raw(token=self.server.adapter_token, body={"method": "start_task", "arguments": {
            "project_id": "starter-demo", "task": "Find source", "task_kind": "code", "model": "other:local"}})
        self.assertEqual(status, 200)
        self.assertEqual(value["result"]["outcome"], "DENY")

    def test_missing_wrong_or_browser_credentials_refuse_before_controller(self):
        with patch.object(self.controller, "call", side_effect=AssertionError("controller reached")):
            for token, headers in ((None, {}), ("a" * 43, {}), (self.server.adapter_token, {"Origin": "null"}),
                                   (self.server.adapter_token, {"Origin": "http://127.0.0.1"}),
                                   (self.server.adapter_token, {"Sec-Fetch-Site": "same-origin"}),
                                   (self.server.adapter_token, {"Host": "evil.invalid"}),
                                   ("é" * 43, {})):
                with self.subTest(headers=headers):
                    self.assertEqual(self.raw(token=token, headers=headers)[0], 403)

    def test_shared_endpoint_is_disabled_by_default(self):
        server = WorkbenchServer(("127.0.0.1", 0), self.controller)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True); thread.start()
        try:
            with self.assertRaises(Refusal):
                _request("POST", "/api/helper", {"method": "list_projects", "arguments": {}}, server.server_port,
                         time.monotonic() + 1, authorization="Bearer " + "a" * 43)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=1)

    def test_bad_methods_shapes_and_evidence_references_are_refused(self):
        for body in ({"method": "settings", "arguments": {"enabled": True}},
                     {"method": "list_projects", "arguments": {"root": "/etc"}},
                     {"method": "get_result", "arguments": {"task_id": []}}):
            self.assertEqual(self.raw(token=self.server.adapter_token, body=body)[1]["result"]["outcome"], "DENY")
        started = self.client.start_task("starter-demo", "Find coverage."); self.wait_result(started["task_id"])
        self.assertEqual(self.client.fetch_evidence(started["task_id"], "E99")["outcome"], "DENY")

    def test_client_close_does_not_stop_shared_service_or_erase_retained_jobs(self):
        started = self.client.start_task("starter-demo", "Find coverage.")
        result = self.wait_result(started["task_id"])
        self.client.close()
        with self.assertRaisesRegex(Refusal, "shared_client_closed"):
            self.client.list_projects()
        second = SharedClient(self.connection_file)
        try:
            self.assertEqual(second.get_result(started["task_id"])["snapshot_id"], result["snapshot_id"])
        finally:
            second.close()


class ConnectionFileAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.path = self.root / "connection.json"

    def publish(self):
        publication = ConnectionPublication(self.path, 8421, "a" * 43, ())
        self.addCleanup(publication.close)
        return publication

    def test_publication_never_overwrites_an_existing_file_and_cleans_its_own_file(self):
        pub = self.publish(); before = self.path.read_bytes()
        with self.assertRaises(Refusal): self.publish()
        self.assertEqual(self.path.read_bytes(), before)
        pub.close(); self.assertFalse(self.path.exists()); pub.close()

    def test_cleanup_preserves_owner_replacement(self):
        pub = self.publish(); self.path.unlink(); self.path.write_text("owner replacement"); self.path.chmod(0o600)
        pub.close(); self.assertEqual(self.path.read_text(), "owner replacement")

    def test_failed_publication_does_not_leave_partial_credentials(self):
        with patch("shake_bake.shared.os.fsync", side_effect=OSError("test")):
            with self.assertRaises(Refusal): self.publish()
        self.assertFalse(self.path.exists())

    def test_publication_inside_source_is_refused_before_creating_directories(self):
        path = self.root / "new" / "connection.json"
        with self.assertRaisesRegex(Refusal, "connection_file_inside_source"):
            ConnectionPublication(path, 8421, "a" * 43, (self.root,))
        self.assertFalse(path.parent.exists())

    def test_permissions_symlinks_and_nonloopback_configuration_are_refused(self):
        self.publish(); self.path.chmod(0o644)
        with self.assertRaises(Refusal): load_connection(self.path)
        self.path.chmod(0o600); link = self.root / "link"; link.symlink_to(self.path)
        with self.assertRaises(Refusal): load_connection(link)
        value = json.loads(self.path.read_text()); value["host"] = "example.invalid"; self.path.write_text(json.dumps(value))
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            with self.assertRaises(Refusal): SharedClient(self.path)

    def test_nonprivate_parent_and_oversized_files_are_refused(self):
        self.root.chmod(0o755)
        try:
            with self.assertRaisesRegex(Refusal, "connection_directory_must_be_private_0700"):
                self.publish()
        finally:
            self.root.chmod(0o700)
        self.path.write_bytes(b"x" * 4097); self.path.chmod(0o600)
        with self.assertRaises(Refusal): load_connection(self.path)

    def test_invalid_schema_ports_and_tokens_refuse_before_network(self):
        self.publish(); original = json.loads(self.path.read_text())
        for changes in ({"port": True}, {"port": 0}, {"port": 65536}, {"schema_version": "future"}, {"token": "short"}):
            self.path.write_text(json.dumps({**original, **changes}))
            with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
                with self.assertRaises(Refusal): SharedClient(self.path)

    def test_header_injection_is_refused_before_network(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(Refusal, "invalid_local_authorization"):
                _request("POST", "/api/helper", {}, 8421, time.monotonic() + 1, authorization="Bearer x\r\nX: y")

    def test_mcp_cli_requires_an_explicit_shared_or_standalone_mode(self):
        import io
        from shake_bake.mcp_server import main
        with patch("sys.stderr", new_callable=io.StringIO):
            for args in ([], ["--project", "demo=/tmp", "--evidence-only"],
                         ["--connection-file", str(self.path), "--model", "fixture:local"]):
                with self.assertRaises(SystemExit) as result:
                    main(args)
                self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

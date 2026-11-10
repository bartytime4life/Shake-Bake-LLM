"""Synthetic source names and exact, escape-heavy runner/bridge transfers."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from shake_bake.collector import MAX_REQUEST_CHARS, build_packet
from shake_bake.contracts import Refusal, Selection
from shake_bake.helper import HelperSession
from shake_bake.gui import Controller, WorkbenchServer
from shake_bake.search import prepare
from shake_bake.shared import ConnectionPublication, SharedClient
from shake_bake.task_protocol import MAX_TASK_INPUT_BYTES, MAX_TASK_RESULT_BYTES, encode_result
from shake_bake.worker import MAX_RESPONSE_BYTES, _request


class SourceTextAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = "needle = 'café 🌱'\r\n"
        (self.root / "readable.py").write_bytes(self.source.encode("utf-8"))

    @unittest.skipUnless(os.name == "posix", "POSIX byte filenames")
    def test_non_utf8_filename_is_excluded_without_hiding_readable_source(self):
        raw_path = os.fsencode(self.root) + b"/needle_\xff.py"
        descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(descriptor, b"needle = 'unusable filename'\n")
        finally:
            os.close(descriptor)
        request = "Find needle. Preserve café, 🌱 and e\u0301.\r\n"
        result = prepare(self.root, request)
        self.assertEqual(result.original_request, request)
        self.assertEqual(result.exclusions["path_utf8_required"], 1)
        self.assertEqual([item.path for item in result.packet.evidence], ["readable.py"])
        self.assertEqual(result.packet.evidence[0].text, self.source)
        self.assertEqual(set(os.listdir(os.fsencode(self.root))), {b"readable.py", b"needle_\xff.py"})
        with self.assertRaisesRegex(Refusal, "path_utf8_required"):
            build_packet(self.root, request, (Selection(os.fsdecode(b"needle_\xff.py"), 1, 1),))

    def test_malformed_request_is_refused_before_source_reads(self):
        request = "Find needle \ud800"
        with patch("shake_bake.collector._read", side_effect=AssertionError("source read")):
            with self.assertRaisesRegex(Refusal, "request_utf8_required"):
                build_packet(self.root, request, (Selection("readable.py", 1, 1),))
        with patch("shake_bake.search.os.scandir", side_effect=AssertionError("source scanned")):
            with self.assertRaisesRegex(Refusal, "request_utf8_required"):
                prepare(self.root, request)

    def test_valid_unicode_filename_and_text_are_preserved(self):
        name = "café_🌱_e\u0301.py"
        (self.root / name).write_bytes(self.source.encode("utf-8"))
        result = prepare(self.root, "Find needle 🌱 e\u0301")
        record = next(item for item in result.packet.evidence if item.path == name)
        self.assertEqual(record.path, name)
        self.assertEqual(record.text, self.source)


@unittest.skipUnless(sys.platform == "linux", "Linux owned runner")
class RunnerTextAcceptance(unittest.TestCase):
    setUp = SourceTextAcceptance.setUp

    def helper(self):
        helper = HelperSession({"fixture": self.root}, evidence_only=True)
        self.addCleanup(helper.close)
        return helper

    def wait_result(self, helper, identifier):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            result = helper.get_result(identifier)
            if result["state"] != "RUNNING":
                return result
            time.sleep(.005)
        self.fail("owned runner did not complete")

    def test_owned_runner_keeps_valid_unicode_after_excluding_byte_filename(self):
        raw_path = os.fsencode(self.root) + b"/needle_\xff.py"
        descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        helper = self.helper()
        request = "Find needle. Preserve café, 🌱 and e\u0301.\r\n"
        identifier = helper.start_task("fixture", request)["task_id"]
        result = self.wait_result(helper, identifier)
        self.assertEqual(result["state"], "DONE", result)
        self.assertEqual(result["original_request"], request)
        self.assertEqual(result["exclusions"]["path_utf8_required"], 1)
        self.assertEqual(helper.fetch_evidence(identifier, "E1")["text"], self.source)

    def test_maximum_request_and_excerpt_budget_survive_json_escaping(self):
        (self.root / "readable.py").unlink()
        source = "needle " + "\x01" * (4096 - len("needle \n")) + "\n"
        paths = []
        for index in range(4):
            # Keep filename controls denied; escaping stress comes from the
            # unchanged original request and captured source contents.
            name = f"needle-{index}.py"
            paths.append(name)
            (self.root / name).write_bytes(source.encode("utf-8"))
        request = "needle " + "\x01" * (MAX_REQUEST_CHARS - len("needle "))
        captured = prepare(self.root, request)
        encoded = encode_result({"outcome": "ANSWER", "search": captured.to_dict(), "worker": None, "worker_error": None})
        self.assertGreater(len(encoded), 256 * 1024)
        self.assertLessEqual(len(encoded), MAX_TASK_RESULT_BYTES)
        self.assertEqual(captured.selected_excerpt_bytes, 16_384)
        helper = self.helper()
        identifier = helper.start_task("fixture", request)["task_id"]
        result = self.wait_result(helper, identifier)
        self.assertEqual(result["state"], "DONE", result)
        self.assertEqual(result["original_request"], request)
        self.assertEqual(len(result["evidence"]), 4)
        for record in result["evidence"]:
            exact = helper.fetch_evidence(identifier, record["evidence_id"])
            self.assertEqual(exact["text"], source)
            self.assertIn(exact["path"], paths)
            self.assertEqual(exact["excerpt_sha256"], hashlib.sha256(source.encode("utf-8")).hexdigest())

    def test_malformed_request_never_starts_a_runner(self):
        helper = self.helper()
        with patch("shake_bake.helper.subprocess.Popen", side_effect=AssertionError("runner started")):
            with self.assertRaisesRegex(Refusal, "request_utf8_required"):
                helper.start_task("fixture", "Find needle \udfff")
        self.assertEqual(helper._jobs, {})

    def test_oversized_serialized_input_reports_admission_refusal(self):
        helper = self.helper()
        with patch("shake_bake.helper.MAX_TASK_INPUT_BYTES", 1), \
                patch("shake_bake.helper.subprocess.Popen", side_effect=AssertionError("runner started")):
            with self.assertRaisesRegex(Refusal, "task_input_too_large"):
                helper.start_task("fixture", "Find needle")
        self.assertEqual(helper._jobs, {})


class ResultTransportAcceptance(unittest.TestCase):
    def test_result_budget_includes_newline_and_overflow_is_explicit(self):
        overhead = len(encode_result({"value": ""}))
        exact = encode_result({"value": "x" * (MAX_TASK_RESULT_BYTES - overhead)})
        self.assertEqual(len(exact), MAX_TASK_RESULT_BYTES)
        self.assertTrue(exact.endswith(b"\n"))
        overflow = encode_result({"value": "x" * (MAX_TASK_RESULT_BYTES - overhead + 1)})
        self.assertEqual(json.loads(overflow), {"outcome": "ERROR", "code": "task_result_too_large"})
        self.assertLess(len(overflow), MAX_TASK_RESULT_BYTES)

    def test_unexpected_invalid_result_text_has_a_wellformed_error(self):
        self.assertEqual(json.loads(encode_result({"text": "\ud800"})),
                         {"outcome": "ERROR", "code": "task_result_utf8_required"})

    def test_shared_transport_accepts_escaped_result_without_widening_ollama_default(self):
        expected = {"original_request": "needle " + "\x01" * 16000,
                    "evidence": [{"text": "needle " + "\x01" * 15000 + "\n"} for _ in range(2)]}
        body = json.dumps({"result": expected}, ensure_ascii=False).encode("utf-8")
        self.assertGreater(len(body), MAX_RESPONSE_BYTES)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "connection.json"
                publication = ConnectionPublication(path, server.server_port, "a" * 43, ())
                try:
                    client = SharedClient(path)
                    try:
                        self.assertEqual(client.get_result("synthetic-task"), expected)
                    finally:
                        client.close()
                finally:
                    publication.close()
            with self.assertRaisesRegex(Refusal, "worker_response_too_large"):
                _request("POST", "/api/chat", {}, server.server_port, time.monotonic() + 2)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_invalid_response_limits_refuse_before_connecting(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            for value in (True, 0, -1, 3 * 1024 * 1024):
                with self.subTest(value=value), self.assertRaisesRegex(Refusal, "invalid_local_response_limit"):
                    _request("POST", "/api/chat", {}, 11434, time.monotonic() + 1, response_limit=value)

    def test_ollama_input_default_is_unchanged_and_invalid_limits_refuse_before_connecting(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            payload = {"task": "needle " + "\x01" * 16000}
            with self.assertRaisesRegex(Refusal, "worker_input_too_large"):
                _request("POST", "/api/chat", payload, 11434, time.monotonic() + 1)
            for value in (True, 0, -1, 3 * 1024 * 1024):
                with self.subTest(value=value), self.assertRaisesRegex(Refusal, "invalid_local_request_limit"):
                    _request("POST", "/api/chat", {}, 11434, time.monotonic() + 1, request_limit=value)


@unittest.skipUnless(sys.platform == "linux", "Linux workbench and runner")
class WorkbenchRequestBudgetAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "source"
        self.root.mkdir()
        self.source = "needle = 'café 🌱'\r\n"
        (self.root / "readable.py").write_bytes(self.source.encode("utf-8"))
        self.controller = Controller({"fixture": self.root})
        self.controller.call("settings", {"enabled": False})
        self.server = WorkbenchServer(("127.0.0.1", 0), self.controller, adapter_projects=("fixture",))
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.01), daemon=True)
        self.thread.start()
        self.publication = ConnectionPublication(self.base / "connection.json", self.server.server_port,
                                                 self.server.adapter_token, [self.root])
        self.client = SharedClient(self.base / "connection.json")
        self.addCleanup(self.cleanup)
        self.request = "needle " + "\x01" * (MAX_REQUEST_CHARS - len("needle "))

    def cleanup(self):
        self.client.close(); self.publication.close()
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.controller.close()
        self.assertFalse(self.thread.is_alive())

    def gui(self, method, path, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Cookie": self.server.session_cookie_name + "=" + self.server.session_token,
                   "Origin": f"http://127.0.0.1:{self.server.server_port}",
                   "X-SB-CSRF": self.server.csrf_token, "Content-Type": "application/json"}
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def wait_result(self, getter):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            result = getter()
            if result["state"] != "RUNNING":
                return result
            time.sleep(.005)
        self.fail("workbench task did not complete")

    def test_gui_maximum_escape_heavy_request_roundtrips_exactly(self):
        raw = json.dumps({"project_id": "fixture", "task": self.request, "task_kind": "code"}).encode("utf-8")
        self.assertGreater(len(raw), 64 * 1024)
        status, started = self.gui("POST", "/api/tasks", raw)
        self.assertEqual(status, 202, started)
        result = self.wait_result(lambda: self.gui("GET", "/api/tasks/" + started["task_id"])[1])
        self.assertEqual(result["state"], "DONE", result)
        self.assertEqual(result["original_request"], self.request)
        self.assertEqual(result["evidence"][0]["text"], self.source)

    def test_shared_maximum_escape_heavy_request_roundtrips_exactly(self):
        started = self.client.start_task("fixture", self.request)
        result = self.wait_result(lambda: self.client.get_result(started["task_id"]))
        self.assertEqual(result["state"], "DONE", result)
        self.assertEqual(result["original_request"], self.request)
        self.assertEqual(self.client.fetch_evidence(started["task_id"], "E1")["text"], self.source)

    def test_gui_and_shared_refuse_over_budget_without_starting_work(self):
        raw = json.dumps({"project_id": "fixture", "task": "x" * MAX_TASK_INPUT_BYTES, "task_kind": "code"}).encode("utf-8")
        status, result = self.gui("POST", "/api/tasks", raw)
        self.assertEqual(status, 400)
        self.assertEqual(result, {"error": "request_size"})
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(Refusal, "shared_request_too_large"):
                self.client.start_task("x" * MAX_TASK_INPUT_BYTES, "Find needle")
        self.assertEqual(self.controller.call("state")["recent"], [])

    def test_shared_malformed_request_has_stable_refusal_before_connecting(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(Refusal, "request_utf8_required"):
                self.client.start_task("fixture", "Find needle \ud800")
        self.assertEqual(self.controller.call("state")["recent"], [])


if __name__ == "__main__":
    unittest.main()

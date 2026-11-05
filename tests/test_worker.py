from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from shake_bake.collector import build_packet
from shake_bake.contracts import Refusal, Selection
from shake_bake.worker import organize, parse_json


@contextmanager
def stub_server(*, remote=False, content=None, status=200, delay=0, override=None, chunked=False, inventory=None, after_digest=None, runtime_version="0.0.0-test", after_runtime=None):
    requests = []
    chat_seen = False
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            nonlocal chat_seen
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, payload))
            if delay:
                time.sleep(delay)
            if self.path == "/api/show":
                result = {"model_info": {"general.architecture": "fixture"}}
                if remote:
                    result["remote_host"] = "https://example.invalid"
            else:
                chat_seen = True
                result = {"model": payload["model"], "done": True, "done_reason": "stop", "eval_count": 12,
                          "message": {"content": content or json.dumps({"summary": "Coverage needs expert review.", "evidence_ids": ["E1"], "questions": ["Is exact equality required?"]})}}
                if override:
                    result.update(override)
            raw = json.dumps(result).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Transfer-Encoding" if chunked else "Content-Length", "chunked" if chunked else str(len(raw)))
                self.end_headers()
                if chunked:
                    for offset in range(0, len(raw), 31):
                        chunk = raw[offset:offset + 31]
                        self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                    self.wfile.write(b"0\r\n\r\n")
                else:
                    self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass
        def do_GET(self):
            requests.append((self.path, None))
            models = inventory if inventory is not None else {"fixture:local": "a" * 64}
            result = {"models": [{"name": name, "digest": after_digest if chat_seen and after_digest else digest}
                                  for name, digest in models.items()]}
            if self.path == "/api/version":
                result = {"version": after_runtime if chat_seen and after_runtime is not None else runtime_version}
            raw = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    thread.start()
    try:
        yield server.server_port, requests
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=1)
        if thread.is_alive():
            raise AssertionError("stub server failed to stop")


class WorkerAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sample.py").write_text("# slice coverage\n", encoding="utf-8")
        self.packet = build_packet(self.root, "Inspect coverage", (Selection("sample.py", 1, 1),))

    def test_real_loopback_http_preflight_and_chat_contract(self):
        with stub_server() as (port, requests):
            with patch.dict("os.environ", {"HTTP_PROXY": "http://example.invalid:9", "OLLAMA_HOST": "https://example.invalid"}):
                note = organize(self.packet, "fixture:local", port=port)
        self.assertEqual([p for p, _ in requests], ["/api/show", "/api/version", "/api/chat", "/api/version"])
        self.assertNotIn("evidence", requests[0][1])
        payload = next(body for path, body in requests if path == "/api/chat")
        self.assertFalse(payload["stream"])
        self.assertNotIn("tools", payload)
        self.assertEqual(payload["options"]["num_predict"], 512)
        self.assertEqual(json.loads(payload["messages"][1]["content"])["original_request"], self.packet.original_request)
        self.assertEqual(note.evidence_ids, ("E1",))
        self.assertEqual(note.label, "unverified_worker_interpretation")

    def test_remote_metadata_refuses_before_source_submission(self):
        with stub_server(remote=True) as (port, requests):
            with self.assertRaisesRegex(Refusal, "local_model_metadata_required"):
                organize(self.packet, "fixture:local", port=port)
        self.assertEqual([p for p, _ in requests], ["/api/show"])

    def test_cloud_or_url_model_names_refuse_before_connecting(self):
        with patch("socket.create_connection") as connect:
            for model in ("model:cloud", "http://example.invalid/x", "../sample", "x\nheader"):
                with self.subTest(model=model), self.assertRaises(Refusal):
                    organize(self.packet, model)
        connect.assert_not_called()

    def test_unknown_evidence_is_refused(self):
        with stub_server(content=json.dumps({"summary": "Claim", "evidence_ids": ["E99"], "questions": []})) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_invalid_evidence_reference"):
                organize(self.packet, "fixture:local", port=port)

    def test_duplicate_keys_are_refused(self):
        with self.assertRaisesRegex(Refusal, "worker_invalid_json"):
            parse_json('{"summary":"one","summary":"two"}')
        with self.assertRaises(Refusal):
            parse_json('{"value":NaN}')

    def test_truncated_reply_is_refused(self):
        with stub_server(override={"done_reason": "length"}) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_incomplete"):
                organize(self.packet, "fixture:local", port=port)

    def test_redirect_is_not_followed(self):
        with stub_server(status=302) as (port, requests):
            with self.assertRaisesRegex(Refusal, "worker_http_error"):
                organize(self.packet, "fixture:local", port=port)
        self.assertEqual(len(requests), 1)

    def test_total_deadline_stops_slow_reply(self):
        with stub_server(delay=0.1) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_timeout"):
                organize(self.packet, "fixture:local", port=port, seconds=0.02)

    def test_model_mismatch_and_invalid_usage_are_refused(self):
        for override, code in (({"model": "other:local"}, "worker_model_mismatch"), ({"eval_count": True}, "worker_invalid_usage")):
            with self.subTest(code=code), stub_server(override=override) as (port, _):
                with self.assertRaisesRegex(Refusal, code):
                    organize(self.packet, "fixture:local", port=port)

    def test_large_context_refuses_before_chat(self):
        packet = build_packet(self.root, "Inspect " + "x" * 7000, (Selection("sample.py", 1, 1),))
        with stub_server() as (port, requests):
            with self.assertRaisesRegex(Refusal, "worker_context_budget"):
                organize(packet, "fixture:local", port=port)
        self.assertEqual(len(requests), 1)

    def test_chunked_http_response_is_supported(self):
        with stub_server(chunked=True) as (port, _):
            note = organize(self.packet, "fixture:local", port=port)
        self.assertEqual(note.evidence_ids, ("E1",))

    def test_large_server_output_is_bounded(self):
        with stub_server(content="x" * 400000) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_response_too_large"):
                organize(self.packet, "fixture:local", port=port)

    def test_remote_chat_metadata_is_refused(self):
        with stub_server(override={"remote_host": "https://example.invalid"}) as (port, _):
            with self.assertRaisesRegex(Refusal, "remote_worker_response_refused"):
                organize(self.packet, "fixture:local", port=port)

    def test_added_fields_and_model_tool_calls_are_refused(self):
        note = {"summary": "Claim", "evidence_ids": ["E1"], "questions": [], "execute": "anything"}
        with stub_server(content=json.dumps(note)) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_invalid_note"):
                organize(self.packet, "fixture:local", port=port)
        with stub_server(override={"message": {"content": "{}", "tool_calls": [{"name": "run"}]}}) as (port, _):
            with self.assertRaisesRegex(Refusal, "worker_invalid_response"):
                organize(self.packet, "fixture:local", port=port)

    def test_descriptor_cleanup_after_success_and_timeout(self):
        import os
        if not Path("/proc/self/fd").exists():
            self.skipTest("Linux descriptor inventory required")
        before = len(os.listdir("/proc/self/fd"))
        with stub_server() as (port, _):
            organize(self.packet, "fixture:local", port=port)
        with stub_server(delay=0.05) as (port, _):
            with self.assertRaises(Refusal):
                organize(self.packet, "fixture:local", port=port, seconds=0.01)
        self.assertEqual(len(os.listdir("/proc/self/fd")), before)


if __name__ == "__main__":
    unittest.main()

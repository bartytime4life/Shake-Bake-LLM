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
def stub_server(*, remote=False, content=None, status=200, delay=0, override=None, chunked=False, inventory=None, after_digest=None, runtime_version="0.0.0-test", after_runtime=None, metadata=None):
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
                result.update(metadata or {})
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
        self.assertEqual(payload["options"]["num_predict"], 1024)
        self.assertEqual(json.loads(payload["messages"][1]["content"])["original_request"], self.packet.original_request)
        self.assertNotIn("task_kind", json.loads(payload["messages"][1]["content"]))
        self.assertEqual(note.evidence_ids, ("E1",))
        self.assertEqual(note.label, "unverified_worker_interpretation")
        # A legacy three-field note is still accepted; it just carries no drafted prompt.
        self.assertFalse(note.has_prompt)
        self.assertEqual((note.goal, note.focus, note.asks, note.approach), ("", (), (), ()))

    def test_handoff_prompt_fields_are_requested_validated_and_exposed(self):
        note = {"goal": "Decide whether the guard admits fewer reported slices than detected.",
                "focus": [{"evidence_id": "E1", "why": " The comparison lives here. "}],
                "asks": ["Does <= admit fewer reported slices?", "What stays unverified?"],
                "approach": ["Trace len(reported)=1 and detected=2 through the comparison."],
                "summary": "E1 compares counts with <=.", "evidence_ids": ["E1"], "questions": ["Is equality intended?"]}
        with stub_server(content=json.dumps(note)) as (port, requests):
            result = organize(self.packet, "fixture:local", port=port, task_kind="code")
        chat = next(body for path, body in requests if path == "/api/chat")
        self.assertEqual(set(chat["format"]["required"]), {"goal", "focus", "asks", "approach", "summary", "evidence_ids", "questions"})
        self.assertFalse(chat["format"]["additionalProperties"])
        self.assertEqual(chat["format"]["properties"]["focus"]["items"]["properties"]["evidence_id"]["enum"], ["E1"])
        self.assertEqual(json.loads(chat["messages"][1]["content"])["task_kind"], "code")
        self.assertIn("draft the best possible prompt", chat["messages"][0]["content"])
        self.assertLessEqual(len(chat["messages"][0]["content"].encode()), 4096)
        self.assertTrue(result.has_prompt)
        self.assertEqual(result.goal, note["goal"])
        self.assertEqual(result.focus, ({"evidence_id": "E1", "why": "The comparison lives here."},))
        self.assertEqual(result.asks, tuple(note["asks"]))
        self.assertEqual(result.approach, tuple(note["approach"]))
        self.assertEqual(result.questions, ("Is equality intended?",))
        self.assertEqual(result.requested_configuration["preparation_design"], "handoff_prompt_v1")
        self.assertEqual(result.to_dict()["asks"], tuple(note["asks"]))
        self.assertEqual(result.label, "unverified_worker_interpretation")

    def test_blank_prompt_fields_leave_notes_without_a_drafted_prompt(self):
        note = {"goal": "  ", "focus": [], "asks": ["   "], "approach": [], "summary": "Claim", "evidence_ids": ["E1"], "questions": []}
        with stub_server(content=json.dumps(note)) as (port, _):
            result = organize(self.packet, "fixture:local", port=port)
        self.assertFalse(result.has_prompt)
        self.assertEqual(result.asks, ())

    def test_datamarked_source_marks_only_the_worker_copy_and_strips_leaks(self):
        from shake_bake import worker
        note = {"goal": "Decide" + worker.DATAMARK + "coverage.", "focus": [{"evidence_id": "E1", "why": "slice" + worker.DATAMARK + "guard"}],
                "asks": ["Does <= admit fewer?"], "approach": [], "summary": "E1 compares counts.", "evidence_ids": ["E1"], "questions": []}
        with stub_server(content=json.dumps(note)) as (port, requests):
            with patch.object(worker, "DATAMARK_SOURCE", True):
                result = organize(self.packet, "fixture:local", port=port)
        chat = next(body for path, body in requests if path == "/api/chat")
        sent = json.loads(chat["messages"][1]["content"])
        self.assertEqual(sent["evidence"][0]["text"], "#" + worker.DATAMARK + "slice" + worker.DATAMARK + "coverage\n")
        self.assertEqual(sent["original_request"], self.packet.original_request)
        self.assertIn("datamarked", chat["messages"][0]["content"])
        self.assertLessEqual(len(chat["messages"][0]["content"].encode()), 4096)
        self.assertEqual(self.packet.evidence[0].text, "# slice coverage\n")
        self.assertEqual((result.goal, result.focus[0]["why"]), ("Decide coverage.", "slice guard"))
        self.assertEqual(result.usage["datamark_leaks"], 2)
        self.assertTrue(result.requested_configuration["datamark_source"])
        with stub_server(content=json.dumps(note)) as (port, requests):
            plain = organize(self.packet, "fixture:local", port=port)
        chat = next(body for path, body in requests if path == "/api/chat")
        self.assertEqual(json.loads(chat["messages"][1]["content"])["evidence"][0]["text"], "# slice coverage\n")
        self.assertNotIn("datamarked", chat["messages"][0]["content"])
        self.assertNotIn("datamark_leaks", plain.usage)
        self.assertFalse(plain.requested_configuration["datamark_source"])

    def test_invalid_prompt_fields_are_refused(self):
        base = {"summary": "Claim", "evidence_ids": ["E1"], "questions": []}
        for extra, code in (({"focus": [{"evidence_id": "E9", "why": "x"}]}, "worker_invalid_evidence_reference"),
                            ({"focus": [{"evidence_id": "E1", "why": "x"}, {"evidence_id": "E1", "why": "y"}]}, "worker_invalid_evidence_reference"),
                            ({"focus": [{"evidence_id": "E1", "why": "x", "run": "rm -rf"}]}, "worker_invalid_note"),
                            ({"focus": "E1"}, "worker_invalid_note"),
                            ({"asks": ["q"] * 7}, "worker_invalid_note"),
                            ({"asks": "not a list"}, "worker_invalid_note"),
                            ({"goal": "g" * 601}, "worker_invalid_note"),
                            ({"goal": ["list"]}, "worker_invalid_note"),
                            ({"approach": [1]}, "worker_invalid_note"),
                            ({"approach": ["s" * 401]}, "worker_invalid_note")):
            with self.subTest(extra=extra), stub_server(content=json.dumps({**base, **extra})) as (port, _):
                with self.assertRaisesRegex(Refusal, code):
                    organize(self.packet, "fixture:local", port=port)

    def test_unknown_task_kind_refuses_before_connecting(self):
        with patch("socket.create_connection") as connect:
            with self.assertRaisesRegex(Refusal, "invalid_task_kind"):
                organize(self.packet, "fixture:local", task_kind="shell")
        connect.assert_not_called()

    def test_remote_metadata_refuses_before_source_submission(self):
        with stub_server(remote=True) as (port, requests):
            with self.assertRaisesRegex(Refusal, "local_model_metadata_required"):
                organize(self.packet, "fixture:local", port=port)
        self.assertEqual([p for p, _ in requests], ["/api/show"])

    def test_thinking_only_and_malformed_controls_refuse_before_source_submission(self):
        for thinking, code in (({"values": [True]}, "worker_thinking_mode_unsupported"),
                               ({"values": ["low", "medium", "high"]}, "worker_thinking_mode_unsupported"),
                               ({"values": ["false"]}, "worker_thinking_mode_unsupported"),
                               ({"values": [0]}, "worker_invalid_thinking_metadata"),
                               ({"values": []}, "worker_invalid_thinking_metadata"),
                               ({"values": "false"}, "worker_invalid_thinking_metadata"),
                               (True, "worker_invalid_thinking_metadata")):
            with self.subTest(thinking=thinking), stub_server(metadata={"thinking": thinking}) as (port, requests):
                with self.assertRaisesRegex(Refusal, code):
                    organize(self.packet, "fixture:local", port=port)
                self.assertEqual(requests, [("/api/show", {"model": "fixture:local"})])

    def test_false_controls_and_legacy_metadata_keep_the_no_thinking_wire_contract(self):
        for metadata in (None, {"thinking": {"values": [False]}}, {"thinking": {"values": [False, True]}}):
            with self.subTest(metadata=metadata), stub_server(metadata=metadata) as (port, requests):
                note = organize(self.packet, "fixture:local", port=port)
                chat = next(body for path, body in requests if path == "/api/chat")
                self.assertIs(chat["think"], False)
                self.assertEqual(json.loads(chat["messages"][1]["content"])["original_request"], self.packet.original_request)
                self.assertEqual(note.label, "unverified_worker_interpretation")

    def test_incompatible_thinking_mode_abstains_without_dropping_exact_source(self):
        from shake_bake.briefing import build_brief
        with stub_server(metadata={"thinking": {"values": [True]}}) as (port, requests):
            brief = build_brief(self.root, "Inspect slice coverage.", model="fixture:local", port=port)
        self.assertEqual(brief.outcome, "ABSTAIN")
        self.assertEqual(brief.worker_error, "worker_thinking_mode_unsupported")
        self.assertIsNone(brief.worker)
        self.assertEqual(brief.search.original_request, "Inspect slice coverage.")
        self.assertEqual(brief.search.packet.evidence[0].text, (self.root / "sample.py").read_text())
        self.assertEqual([path for path, _ in requests], ["/api/show"])

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

    def test_oversized_source_gets_a_fitted_copy_and_the_model_cites_only_what_it_saw(self):
        selections = []
        for index in range(8):
            body = "".join(f"def coverage_step_{index}_{line}(value):  # slice coverage guard line {line}\n" for line in range(40))
            (self.root / f"module_{index}.py").write_text(body, encoding="utf-8")
            selections.append(Selection(f"module_{index}.py", 1, 40))
        packet = build_packet(self.root, "Inspect coverage", tuple(selections))
        self.assertGreater(len(json.dumps([r.text for r in packet.evidence]).encode()), 6000)
        with stub_server() as (port, requests):
            note = organize(packet, "fixture:local", port=port)
        payload = next(body for path, body in requests if path == "/api/chat")
        sent = json.loads(payload["messages"][1]["content"])
        self.assertLessEqual(len(payload["messages"][1]["content"].encode()), 6000)
        self.assertEqual(sent["original_request"], packet.original_request)
        shown = [item["id"] for item in sent["evidence"]]
        self.assertEqual(shown, [f"E{n}" for n in range(1, len(shown) + 1)], "records are left out from the end")
        self.assertGreater(len(shown), 1)
        self.assertEqual(sent["worker_view"]["omitted_evidence"], [f"E{n}" for n in range(len(shown) + 1, 9)])
        for item in sent["evidence"]:
            self.assertTrue(item["text_cut"])
            self.assertEqual(item["text"].count("\n"), 12)
            self.assertEqual(item["shown_end_line"], item["start_line"] + 11)
        enum = payload["format"]["properties"]["evidence_ids"]["items"]["enum"]
        self.assertEqual(enum, shown, "the model may cite only what it was shown")
        self.assertEqual(note.source_view, {"lines_per_excerpt": 12, "shown": shown, "cut": shown,
                                            "omitted": sent["worker_view"]["omitted_evidence"]})
        self.assertEqual(len(packet.evidence[0].text.splitlines()), 40, "exact evidence is unchanged")

    def test_source_that_fits_is_sent_whole(self):
        from dataclasses import asdict
        with stub_server() as (port, requests):
            note = organize(self.packet, "fixture:local", port=port, task_kind="code", collection_context={"scope": "fixture"})
        content = next(body for path, body in requests if path == "/api/chat")["messages"][1]["content"]
        earlier = {"original_request": self.packet.original_request, "snapshot_id": self.packet.snapshot_id, "collection": {"scope": "fixture"},
                   "evidence": [{"id": "E1", **asdict(self.packet.evidence[0])}], "task_kind": "code"}
        self.assertEqual(content, json.dumps(earlier, ensure_ascii=False), "a copy that fits is byte-identical to the earlier construction")
        sent = json.loads(content)
        self.assertNotIn("worker_view", sent)
        self.assertNotIn("text_cut", sent["evidence"][0])
        self.assertIsNone(note.source_view)

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

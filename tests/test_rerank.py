"""A synthetic loopback embedding server tests the rerank mechanism, not any model's quality."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from shake_bake.briefing import build_brief, render
from shake_bake.contracts import Refusal
from shake_bake.rerank import BATCH, MAX_POOL, MAX_WINDOW_BYTES, EmbeddingScorer
from shake_bake.search import SearchLimits, prepare
from shake_bake.worker import MAX_RESPONSE_BYTES


@contextmanager
def embed_server(*, marker="PARCEL_BACKEND", remote=False, model_name=None, broken=None,
                 query="Which backend override applies", dimensions=2, fail_batch=None,
                 delay=0, response_sizes=None, remote_embedding=False):
    """Vectors depend on each text, including the first candidate in later batches."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, payload))
            if self.path == "/api/show":
                result = {"model_info": {"general.architecture": "fixture"}}
                if remote:
                    result["remote_host"] = "https://example.invalid"
            else:
                texts = payload["input"]
                if delay:
                    time.sleep(delay)
                vectors = [[1.0] + [0.0] * (dimensions - 1) if text == query or marker in text
                           else [0.0] + [-0.12345678901234566] * (dimensions - 1) for text in texts]
                batch = sum(path == "/api/embed" for path, _ in requests)
                if broken == "count" or batch == fail_batch:
                    vectors = vectors[:-1]
                if broken == "dimensions":
                    vectors[-1] = [0.5]
                result = {"model": model_name or payload["model"], "embeddings": vectors, "prompt_eval_count": 7, "total_duration": 5}
                if remote_embedding:
                    result["remote_host"] = "https://example.invalid"
            raw = json.dumps(result).encode()
            if self.path == "/api/embed" and response_sizes is not None:
                response_sizes.append(len(raw))
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            requests.append((self.path, None))
            raw = json.dumps({"version": "0.0.0-test"}).encode()
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


class RerankAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Six files match "backend"; only one mentions PARCEL_BACKEND, and lexically it is last.
        for index in range(5):
            (self.root / f"a{index}.py").write_text(f"# backend note {index}\nbackend = {index}\n", encoding="utf-8")
        (self.root / "z_settings.py").write_text("def load_settings(environ):\n    return environ.get('PARCEL_BACKEND', 'local')  # backend\n", encoding="utf-8")
        self.task = "Which backend override applies"

    def test_rerank_reorders_lexical_candidates_without_adding_or_hiding_windows(self):
        lexical = prepare(self.root, self.task)
        self.assertNotIn("z_settings.py", [record.path for record in lexical.packet.evidence])
        self.assertIsNone(lexical.rerank)
        with embed_server() as (port, requests):
            result = prepare(self.root, self.task, None, EmbeddingScorer("fixture:embed", port=port))
        self.assertEqual(result.packet.evidence[0].path, "z_settings.py")
        self.assertEqual(len(result.packet.evidence), len(lexical.packet.evidence))
        self.assertEqual({r.path for r in result.packet.evidence} - {"z_settings.py"} <= {r.path for r in lexical.packet.evidence}, True)
        self.assertEqual([path for path, _ in requests], ["/api/show", "/api/version", "/api/embed"])
        embed = next(body for path, body in requests if path == "/api/embed")
        self.assertEqual(embed["input"][0], self.task)
        self.assertEqual(embed["keep_alive"], 0)
        self.assertEqual(len(embed["input"]) - 1, result.rerank["pool"])
        self.assertTrue(result.rerank["order_changed"])
        self.assertEqual(result.rerank["candidates"], 6)
        self.assertEqual(result.rerank["dimensions"], 2)
        self.assertEqual(result.rerank["local_server_reported_usage"], {"prompt_eval_count": 7, "total_duration": 5})
        self.assertTrue(result.rerank["selects_nothing_new"])
        self.assertEqual(result.rerank["similarities"].count(1.0), 1)
        # Half pool-normalized similarity, half pool-normalized lexical score; one batch, so no keep-alive.
        self.assertEqual(result.rerank["blend"], 0.5)
        self.assertEqual(len(result.rerank["blended"]), result.rerank["pool"])
        self.assertEqual(result.rerank["keep_alive_between_batches_seconds"], 0)
        for record in result.packet.evidence:
            self.assertEqual(record.text, "".join((self.root / record.path).read_text(encoding="utf-8").splitlines(keepends=True)[record.start_line - 1:record.end_line]))

    def test_refusals_fall_back_to_lexical_order_and_are_recorded(self):
        lexical = [(r.path, r.start_line) for r in prepare(self.root, self.task).packet.evidence]
        for kwargs, code in (({"remote": True}, "local_model_metadata_required"), ({"model_name": "other:embed"}, "embedding_model_mismatch"),
                             ({"broken": "count"}, "embedding_count_mismatch"), ({"broken": "dimensions"}, "embedding_invalid_vector")):
            with self.subTest(code=code), embed_server(**kwargs) as (port, _):
                result = prepare(self.root, self.task, None, EmbeddingScorer("fixture:embed", port=port))
            self.assertEqual([(r.path, r.start_line) for r in result.packet.evidence], lexical)
            self.assertEqual(result.rerank["error"], code)
            self.assertNotIn("rerank_pool_budget", result.cutoffs)

    def test_pool_is_bounded_and_disclosed(self):
        for index in range(MAX_POOL + 3):
            (self.root / f"p{index:02d}.py").write_text(f"# backend pool {index}\n", encoding="utf-8")
        with embed_server() as (port, requests):
            result = prepare(self.root, self.task, None, EmbeddingScorer("fixture:embed", port=port))
        embeds = [body for path, body in requests if path == "/api/embed"]
        self.assertEqual(sum(len(body["input"]) for body in embeds) - 1, MAX_POOL)
        self.assertEqual(len(embeds), -(-(MAX_POOL + 1) // BATCH))
        self.assertTrue(all(len(body["input"]) <= BATCH for body in embeds))
        self.assertEqual(embeds[0]["input"][0], self.task)
        self.assertEqual(result.rerank["embed_calls"], len(embeds))
        self.assertIn("rerank_pool_budget", result.cutoffs)
        self.assertEqual(result.rerank["pool"], MAX_POOL)

    def test_brief_records_the_rerank_as_a_scan_fact(self):
        with embed_server() as (port, _):
            brief = build_brief(self.root, self.task, rerank_model="fixture:embed", port=port)
        text = render(brief)
        self.assertIn("Rerank: local embedding model fixture:embed scored 6 of 6 candidate windows; order changed. A scan fact about ordering, not an interpretation; it added no window.", text)
        self.assertEqual(brief.search.rerank["model"], "fixture:embed")
        with embed_server(remote=True) as (port, _):
            refused = render(build_brief(self.root, self.task, rerank_model="fixture:embed", port=port))
        self.assertIn("Rerank: local embedding model fixture:embed refused (local_model_metadata_required); lexical order kept.", refused)
        with self.assertRaises(Refusal):
            EmbeddingScorer("fixture:embed", port=port)("request", [])
        # An oversized window is cut for scoring only, counted in the record; the excerpt itself is never changed.
        with embed_server() as (port, requests):
            scorer = EmbeddingScorer("fixture:embed", port=port)
            similarities = scorer("request", ["x" * 5000, "PARCEL_BACKEND"])
        sent = next(body for path, body in requests if path == "/api/embed")["input"]
        self.assertEqual(len(sent[1].encode()), 4096)
        self.assertEqual(scorer.record["truncated_windows"], 1)
        self.assertEqual(len(similarities), 2)

    def test_full_pool_stays_below_transport_cap_and_preserves_cross_batch_alignment(self):
        texts = ["plain"] * MAX_POOL
        for index in (7, 15, 23):
            texts[index] = "PARCEL_BACKEND"
        sizes = []
        with embed_server(query="query", dimensions=1024, response_sizes=sizes) as (port, requests):
            scorer = EmbeddingScorer("fixture:embed", port=port)
            scores = scorer("query", texts)
        embeds = [body for path, body in requests if path == "/api/embed"]
        self.assertEqual([len(body["input"]) for body in embeds], [8, 8, 8, 1])
        # The model stays loaded only between this preparation's batches; the last batch asks for release.
        self.assertEqual([body["keep_alive"] for body in embeds], [30, 30, 30, 0])
        self.assertEqual(scorer.record["keep_alive_between_batches_seconds"], 30)
        self.assertEqual([i for i, score in enumerate(scores) if score > .99], [7, 15, 23])
        self.assertTrue(all(size < MAX_RESPONSE_BYTES for size in sizes))
        self.assertEqual(scorer.record["embed_calls"], 4)
        self.assertEqual(scorer.record["embed_calls_completed"], 4)
        self.assertEqual(scorer.record["local_server_reported_usage"], {"prompt_eval_count": 28, "total_duration": 20})

    def test_scoring_truncation_preserves_unicode_excerpt_request_and_hashes(self):
        for path in self.root.iterdir():
            path.unlink()
        original = "# backend " + "x" * 4085 + "λ" * 600 + "\n"
        (self.root / "long.py").write_text(original, encoding="utf-8")
        request = "backend " + "λ" * 2100
        with embed_server() as (port, requests):
            brief = build_brief(self.root, request, rerank_model="fixture:embed", port=port)
        sent = next(body for path, body in requests if path == "/api/embed")["input"]
        self.assertTrue(all(len(text.encode("utf-8")) <= MAX_WINDOW_BYTES for text in sent))
        self.assertEqual(len(sent[1].encode("utf-8")), 4095)
        evidence = brief.search.packet.evidence[0]
        self.assertEqual(evidence.text, original)
        self.assertEqual(evidence.excerpt_sha256, hashlib.sha256(original.encode("utf-8")).hexdigest())
        self.assertEqual(brief.search.packet.original_request, request)
        self.assertEqual(brief.search.rerank["truncated_windows"], 1)
        self.assertTrue(brief.search.rerank["request_truncated"])
        self.assertIn("1 window(s) shortened; request shortened: yes", render(brief))

    def test_reused_scorer_timeout_cannot_inherit_success_measurements(self):
        with embed_server() as (port, _):
            scorer = EmbeddingScorer("fixture:embed", port=port)
            first = prepare(self.root, self.task, scorer=scorer)
            with patch("shake_bake.rerank.local_model_metadata", side_effect=Refusal("worker_timeout")):
                failed = prepare(self.root, self.task, scorer=scorer)
            recovered = prepare(self.root, self.task, scorer=scorer)
        self.assertEqual(first.rerank["windows_scored"], 6)
        self.assertEqual(failed.rerank["error"], "worker_timeout")
        self.assertEqual(failed.rerank["embed_calls"], 0)
        self.assertEqual(failed.rerank["embed_calls_completed"], 0)
        self.assertEqual(failed.rerank["windows_scored"], 0)
        self.assertEqual(failed.rerank["local_server_reported_usage"], {})
        self.assertNotIn("dimensions", failed.rerank)
        self.assertNotIn("observed_runtime_version", failed.rerank)
        self.assertGreaterEqual(failed.rerank["elapsed_seconds"], 0)
        self.assertEqual(first.rerank["embed_calls"], 1)
        self.assertNotIn("error", first.rerank)
        self.assertNotIn("error", recovered.rerank)
        self.assertEqual(recovered.rerank["windows_scored"], 6)

    def test_second_batch_failure_keeps_exact_lexical_packet_and_attempt_receipt(self):
        for index in range(MAX_POOL):
            (self.root / f"p{index:02d}.py").write_text(f"# backend pool {index}\n", encoding="utf-8")
        lexical = prepare(self.root, self.task)
        with embed_server(fail_batch=2) as (port, requests):
            brief = build_brief(self.root, self.task, rerank_model="fixture:embed", port=port)
        self.assertEqual(brief.search.packet, lexical.packet)
        self.assertEqual(sum(path == "/api/embed" for path, _ in requests), 2)
        self.assertEqual(brief.search.rerank["error"], "embedding_count_mismatch")
        self.assertEqual(brief.search.rerank["embed_calls"], 2)
        self.assertEqual(brief.search.rerank["embed_calls_completed"], 2)
        self.assertEqual(brief.search.rerank["windows_scored"], 0)
        self.assertEqual(brief.search.rerank["local_server_reported_usage"], {"prompt_eval_count": 7, "total_duration": 5})
        self.assertIn("refused (embedding_count_mismatch); lexical order kept", render(brief))
        self.assertIn("2 embedding request(s); 2 complete response(s)", render(brief))

    def test_batch_network_waiting_uses_one_deadline(self):
        with embed_server(query="query", delay=.09) as (port, requests):
            scorer = EmbeddingScorer("fixture:embed", port=port, seconds=.22)
            started = time.perf_counter()
            with self.assertRaisesRegex(Refusal, "worker_timeout"):
                scorer("query", ["plain"] * MAX_POOL)
            elapsed = time.perf_counter() - started
            attempts = sum(path == "/api/embed" for path, _ in requests)
        self.assertLess(attempts, 4)
        self.assertLess(elapsed, .6)
        self.assertEqual(scorer.record["error"], "worker_timeout")
        self.assertEqual(scorer.record["embed_calls"], attempts)
        self.assertLess(scorer.record["embed_calls_completed"], attempts)

    def test_higher_dimensional_response_fails_closed_with_visible_fallback(self):
        sizes = []
        lexical = prepare(self.root, self.task)
        with embed_server(dimensions=8192, response_sizes=sizes) as (port, _):
            brief = build_brief(self.root, self.task, rerank_model="fixture:embed", port=port)
        self.assertGreater(sizes[0], MAX_RESPONSE_BYTES)
        self.assertEqual(brief.search.packet, lexical.packet)
        self.assertEqual(brief.search.rerank["error"], "worker_response_too_large")
        self.assertEqual(brief.search.rerank["embed_calls"], 1)
        self.assertEqual(brief.search.rerank["embed_calls_completed"], 0)
        self.assertIn("refused (worker_response_too_large); lexical order kept", render(brief))

    def test_remote_embedding_reply_retains_lexical_packet_and_receipt(self):
        lexical = prepare(self.root, self.task)
        with embed_server(remote_embedding=True) as (port, _):
            brief = build_brief(self.root, self.task, rerank_model="fixture:embed", port=port)
        self.assertEqual(brief.search.packet, lexical.packet)
        self.assertEqual(brief.search.rerank["error"], "remote_embedding_response_refused")
        self.assertIn("lexical order kept", render(brief))

    def test_default_brief_never_constructs_an_embedding_scorer(self):
        with patch("shake_bake.rerank.EmbeddingScorer", side_effect=AssertionError("unexpected model use")):
            brief = build_brief(self.root, self.task)
        self.assertIsNone(brief.search.rerank)


if __name__ == "__main__":
    unittest.main()

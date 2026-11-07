"""A synthetic loopback embedding server tests the rerank mechanism, not any model's quality."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from shake_bake.briefing import build_brief, render
from shake_bake.contracts import Refusal
from shake_bake.rerank import BATCH, MAX_POOL, EmbeddingScorer
from shake_bake.search import SearchLimits, prepare


@contextmanager
def embed_server(*, marker="PARCEL_BACKEND", remote=False, model_name=None, broken=None):
    """Vectors point along [1, 0] when the text holds `marker`, else [0, 1]; the request is [1, 0]."""
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
                vectors = [[1.0, 0.0]] + [[1.0, 0.0] if marker in text else [0.0, 1.0] for text in texts[1:]]
                if broken == "count":
                    vectors = vectors[:-1]
                if broken == "dimensions":
                    vectors[-1] = [0.5]
                result = {"model": model_name or payload["model"], "embeddings": vectors, "prompt_eval_count": 7, "total_duration": 5}
            raw = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

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
        self.assertEqual(result.rerank["blend"], 0.5)
        self.assertEqual(len(result.rerank["blended"]), result.rerank["pool"])
        self.assertEqual(result.rerank["keep_alive_between_batches_seconds"], 0)
        self.assertEqual(embed["keep_alive"], 0)
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
        # The model stays loaded only between this preparation's batches; the last batch asks for release.
        self.assertEqual([body["keep_alive"] for body in embeds], [30] * (len(embeds) - 1) + [0])
        self.assertEqual(result.rerank["keep_alive_between_batches_seconds"], 30)
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


if __name__ == "__main__":
    unittest.main()

"""Optional local embedding rerank of candidate windows.

The scorer asks a loopback Ollama embedding model for vectors of the request
and of each candidate window, and returns cosine similarities. It orders
evidence that the lexical scan already found; it selects nothing new, cites
nothing, and its result is a scan fact recorded in the receipt, not an
interpretation. The same loopback, identity and budget rules as the worker
apply, and a refusal here never hides evidence: the caller falls back to the
lexical order and records the refusal code.
"""

import math
import time

from .contracts import Refusal
from .worker import _post, canonical_model, local_model_metadata, local_runtime, validate_settings

MAX_POOL = 24
MAX_WINDOW_BYTES = 4096
MAX_DIMENSIONS = 8192
BATCH = 8
KEEP_ALIVE_BETWEEN_BATCHES_SECONDS = 30


class EmbeddingScorer:
    """Callable(request, texts) -> similarities; fills `record` after each call."""

    def __init__(self, model: str, *, port: int = 11434, seconds: float = 20.0):
        validate_settings(model, port, seconds)
        self.model, self.port, self.seconds = model, port, seconds
        self.record: dict = {"model": model, "kind": "local_embedding_rerank", "selects_nothing_new": True}

    def __call__(self, request: str, texts: list[str]) -> list[float]:
        if not texts or len(texts) > MAX_POOL:
            raise Refusal("rerank_pool_not_allowed")
        # Only the ordering uses these copies, so an oversized window is cut for embedding
        # (counted in the record); the exact excerpt the host receives is untouched.
        truncated = 0
        scored_texts = []
        for text in texts:
            encoded = text.encode("utf-8")
            if len(encoded) > MAX_WINDOW_BYTES:
                truncated += 1
                text = encoded[:MAX_WINDOW_BYTES].decode("utf-8", errors="ignore")
            scored_texts.append(text)
        deadline = time.monotonic() + self.seconds
        started = time.perf_counter()
        local_model_metadata(self.model, self.port, deadline)
        runtime = local_runtime(self.port, deadline)
        # A 1,024-dimension vector is about 13 KB of JSON, so a full pool in one reply
        # would exceed the transport's response cap; embed in small batches under one deadline.
        inputs = [request.encode("utf-8")[:MAX_WINDOW_BYTES].decode("utf-8", errors="ignore"), *scored_texts]
        vectors: list[list[float]] = []
        usage: dict[str, int] = {}
        calls = 0
        for start in range(0, len(inputs), BATCH):
            batch = inputs[start:start + BATCH]
            # Keep the model loaded only between the batches of this one preparation (the
            # worker's unload-after-use rule still holds: the final batch asks for release).
            last = start + BATCH >= len(inputs)
            result = _post("/api/embed", {"model": self.model, "input": batch, "keep_alive": 0 if last else KEEP_ALIVE_BETWEEN_BATCHES_SECONDS,
                                          "truncate": False}, self.port, deadline)
            calls += 1
            if result.get("remote_host") or result.get("remote_model"):
                raise Refusal("remote_embedding_response_refused")
            if not isinstance(result.get("model"), str) or canonical_model(result["model"]) != canonical_model(self.model):
                raise Refusal("embedding_model_mismatch")
            got = result.get("embeddings")
            if not isinstance(got, list) or len(got) != len(batch):
                raise Refusal("embedding_count_mismatch")
            vectors.extend(got)
            for key in ("prompt_eval_count", "total_duration", "load_duration"):
                value = result.get(key)
                if value is not None:
                    if type(value) is not int or not 0 <= value <= 10**15:
                        raise Refusal("embedding_invalid_usage")
                    usage[key] = usage.get(key, 0) + value
        dimensions = None
        for vector in vectors:
            if not isinstance(vector, list) or not vector or len(vector) > MAX_DIMENSIONS:
                raise Refusal("embedding_invalid_vector")
            if dimensions is None:
                dimensions = len(vector)
            if len(vector) != dimensions or not all(type(value) in (int, float) and math.isfinite(value) for value in vector):
                raise Refusal("embedding_invalid_vector")
        norms = [math.sqrt(sum(value * value for value in vector)) for vector in vectors]
        if any(norm == 0 for norm in norms):
            raise Refusal("embedding_invalid_vector")
        query = vectors[0]
        similarities = [sum(a * b for a, b in zip(query, vector)) / (norms[0] * norm) for vector, norm in zip(vectors[1:], norms[1:])]
        self.record.update({"dimensions": dimensions, "windows_scored": len(texts), "truncated_windows": truncated, "embed_calls": calls,
                            "keep_alive_between_batches_seconds": KEEP_ALIVE_BETWEEN_BATCHES_SECONDS if calls > 1 else 0, "observed_runtime_version": runtime,
                            "local_server_reported_usage": usage, "elapsed_seconds": round(time.perf_counter() - started, 3)})
        return similarities

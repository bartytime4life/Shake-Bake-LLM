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
# Between the batches of one preparation the model stays loaded; the last batch asks for
# release, so the worker's unload-after-use rule still holds at the end. Measured on
# November 7: about 7 s per repository-sized case with a reload per batch, about 2 s without.
KEEP_ALIVE_BETWEEN_BATCHES_SECONDS = 30


def _unit_vector(vector: list[float]) -> list[float]:
    """Normalize after scaling: finite coordinates may still overflow when squared.

    At least one scaled coordinate has magnitude one, preventing a nonzero
    vector's norm from underflowing. The norm is at most sqrt(MAX_DIMENSIONS).
    Reject integers outside the finite float range as malformed model output.
    """
    try:
        if not all(type(value) in (int, float) and math.isfinite(value) for value in vector):
            raise Refusal("embedding_invalid_vector")
    except OverflowError:
        raise Refusal("embedding_invalid_vector") from None
    scale = max(abs(value) for value in vector)
    if scale == 0:
        raise Refusal("embedding_invalid_vector")
    scaled = [value / scale for value in vector]
    norm = math.hypot(*scaled)
    return [value / norm for value in scaled]


class EmbeddingScorer:
    """Callable(request, texts) -> similarities; fills `record` after each call."""

    def __init__(self, model: str, *, port: int = 11434, seconds: float = 20.0):
        validate_settings(model, port, seconds)
        self.model, self.port, self.seconds = model, port, seconds
        self.record: dict = {"model": model, "kind": "local_embedding_rerank", "selects_nothing_new": True}

    def __call__(self, request: str, texts: list[str]) -> list[float]:
        # A scorer can be reused across cases. Never let a failed invocation
        # inherit a previous case's successful dimensions, usage or timing.
        self.record = {"model": self.model, "kind": "local_embedding_rerank", "selects_nothing_new": True,
                       "windows_scored": 0, "truncated_windows": 0, "request_truncated": False,
                       "embed_calls": 0, "embed_calls_completed": 0, "local_server_reported_usage": {}}
        started = time.perf_counter()
        deadline = time.monotonic() + self.seconds
        try:
            return self._score(request, texts, deadline)
        except Refusal as refusal:
            self.record["error"] = refusal.code
            raise
        finally:
            self.record["elapsed_seconds"] = round(time.perf_counter() - started, 3)

    def _score(self, request: str, texts: list[str], deadline: float) -> list[float]:
        if not texts or len(texts) > MAX_POOL:
            raise Refusal("rerank_pool_not_allowed")
        # Only the ordering uses these copies, so an oversized window is cut for embedding
        # (counted in the record); the exact excerpt the host receives is untouched.
        scored_texts = []
        for text in texts:
            encoded = text.encode("utf-8")
            if len(encoded) > MAX_WINDOW_BYTES:
                self.record["truncated_windows"] += 1
                text = encoded[:MAX_WINDOW_BYTES].decode("utf-8", errors="ignore")
            scored_texts.append(text)
        encoded_request = request.encode("utf-8")
        self.record["request_truncated"] = len(encoded_request) > MAX_WINDOW_BYTES
        scored_request = encoded_request[:MAX_WINDOW_BYTES].decode("utf-8", errors="ignore")
        local_model_metadata(self.model, self.port, deadline)
        self.record["observed_runtime_version"] = local_runtime(self.port, deadline)
        # A 1,024-dimension vector is about 13 KB of JSON, so a full pool in one reply
        # would exceed the transport's response cap; embed in small batches under one deadline.
        inputs = [scored_request, *scored_texts]
        vectors: list[list[float]] = []
        for start in range(0, len(inputs), BATCH):
            batch = inputs[start:start + BATCH]
            self.record["embed_calls"] += 1
            last = start + BATCH >= len(inputs)
            result = _post("/api/embed", {"model": self.model, "input": batch, "keep_alive": 0 if last else KEEP_ALIVE_BETWEEN_BATCHES_SECONDS,
                                          "truncate": False}, self.port, deadline)
            # Complete means the transport returned a parsed JSON object,
            # not that its model, vector count or other contents were accepted.
            self.record["embed_calls_completed"] += 1
            if result.get("remote_host") or result.get("remote_model"):
                raise Refusal("remote_embedding_response_refused")
            if not isinstance(result.get("model"), str) or canonical_model(result["model"]) != canonical_model(self.model):
                raise Refusal("embedding_model_mismatch")
            got = result.get("embeddings")
            if not isinstance(got, list) or len(got) != len(batch):
                raise Refusal("embedding_count_mismatch")
            vectors.extend(got)
            batch_usage = {}
            for key in ("prompt_eval_count", "total_duration", "load_duration"):
                value = result.get(key)
                if value is not None:
                    if type(value) is not int or not 0 <= value <= 10**15:
                        raise Refusal("embedding_invalid_usage")
                    batch_usage[key] = value
            usage = self.record["local_server_reported_usage"]
            for key, value in batch_usage.items():
                usage[key] = usage.get(key, 0) + value
        dimensions = None
        units = []
        for vector in vectors:
            if not isinstance(vector, list) or not vector or len(vector) > MAX_DIMENSIONS:
                raise Refusal("embedding_invalid_vector")
            if dimensions is None:
                dimensions = len(vector)
            if len(vector) != dimensions:
                raise Refusal("embedding_invalid_vector")
            units.append(_unit_vector(vector))
        query = units[0]
        # fsum reduces cancellation error; clamp only final floating-point
        # roundoff at the mathematical cosine bounds.
        similarities = [max(-1.0, min(1.0, math.fsum(a * b for a, b in zip(query, vector)))) for vector in units[1:]]
        self.record.update({"dimensions": dimensions, "windows_scored": len(texts),
                            "keep_alive_between_batches_seconds": KEEP_ALIVE_BETWEEN_BATCHES_SECONDS if self.record["embed_calls"] > 1 else 0})
        return similarities

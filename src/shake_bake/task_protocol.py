"""Shared bounds for the owned runner's exact JSON transport."""

import json


MAX_TASK_INPUT_BYTES = 128 * 1024
MAX_TASK_RESULT_BYTES = 1024 * 1024
MAX_SHARED_RESPONSE_BYTES = MAX_TASK_RESULT_BYTES + 16 * 1024


def encode_result(result: dict) -> bytes:
    """Return one bounded JSON record, including its final newline.

    The result budget covers escaped requests, excerpts and bounded metadata.
    An unexpected overflow fails explicitly without truncating exact evidence.
    """
    try:
        raw = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
    except UnicodeEncodeError:
        return b'{"outcome":"ERROR","code":"task_result_utf8_required"}\n'
    if len(raw) > MAX_TASK_RESULT_BYTES:
        return b'{"outcome":"ERROR","code":"task_result_too_large"}\n'
    return raw

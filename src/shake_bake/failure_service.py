"""Owned, bounded source-location work; no inspected code is executed."""

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from .contracts import Refusal
from .failure_runner import MAX_FAILURE_INPUT_BYTES
from .task_protocol import MAX_TASK_RESULT_BYTES
from .worker import parse_json


def run_failure_location(root, error_output, command, *, working_directory="", scratch, timeout=5):
    if sys.platform != "linux":
        raise Refusal("linux_failure_locator_required")
    if not isinstance(error_output, str) or not error_output.strip() or not isinstance(command, str):
        raise Refusal("invalid_failure_request")
    if not isinstance(working_directory, str) or "\x00" in working_directory:
        raise Refusal("invalid_failure_working_directory")
    try:
        if len(working_directory.encode("utf-8")) > 4096:
            raise Refusal("invalid_failure_working_directory")
    except UnicodeEncodeError:
        raise Refusal("invalid_failure_working_directory") from None
    try:
        if len(error_output.encode("utf-8")) > 65536 or len(command.encode("utf-8")) > 4096:
            raise Refusal("failure_input_too_large")
        raw = json.dumps({"root": str(root), "error_output": error_output, "command": command,
                          "working_directory": working_directory},
                         ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        raise Refusal("failure_input_utf8_required") from None
    if len(raw) > MAX_FAILURE_INPUT_BYTES:
        raise Refusal("failure_input_too_large")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
    process = subprocess.Popen([sys.executable, "-B", "-P", "-S", "-m", "shake_bake.failure_runner", str(os.getpid())],
                               cwd=scratch, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        output, _ = process.communicate(raw, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise Refusal("failure_locator_timeout") from None
    if process.returncode != 0 or len(output) > MAX_TASK_RESULT_BYTES:
        raise Refusal("failure_locator_failed")
    try:
        result = parse_json(output.decode("utf-8"))
        if result.get("outcome") in ("DENY", "ERROR"):
            raise Refusal(result.get("code", "failure_locator_failed"))
        if (result.get("kind") != "failure_source_report" or result.get("error_output") != error_output
                or result.get("command") != command or result.get("working_directory") != working_directory
                or not isinstance(result.get("working_directory_path"), str)):
            raise Refusal("invalid_failure_result")
        for item in result.get("evidence", []):
            if hashlib.sha256(item["text"].encode("utf-8")).hexdigest() != item["excerpt_sha256"]:
                raise Refusal("invalid_failure_result")
        return result
    except Refusal:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, AttributeError):
        raise Refusal("invalid_failure_result") from None

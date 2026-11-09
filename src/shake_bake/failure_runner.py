"""Run only the trusted failure locator in a bounded Linux child."""

import ctypes
import json
import os
from pathlib import Path
import resource
import signal
import sys

from .contracts import Refusal
from .task_protocol import encode_result

MAX_FAILURE_INPUT_BYTES = 512 * 1024


def main():
    try:
        if sys.platform != "linux" or len(sys.argv) != 2:
            raise Refusal("linux_failure_locator_required")
        if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            raise Refusal("failure_locator_supervision_unavailable")
        if os.getppid() != int(sys.argv[1]):
            return 1
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
        signal.alarm(4)
        raw = sys.stdin.buffer.read(MAX_FAILURE_INPUT_BYTES + 1)
        if len(raw) > MAX_FAILURE_INPUT_BYTES:
            raise Refusal("failure_input_too_large")
        from .worker import parse_json
        from .troubleshoot import locate_failure
        request = parse_json(raw.decode("utf-8"))
        if not isinstance(request, dict) or set(request) != {"root", "error_output", "command"}:
            raise Refusal("invalid_failure_request")
        result = locate_failure(Path(request["root"]), request["error_output"], request["command"])
    except Refusal as error:
        result = {"outcome": "DENY", "code": error.code}
    except Exception:
        result = {"outcome": "ERROR", "code": "failure_locator_failed"}
    sys.stdout.buffer.write(encode_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

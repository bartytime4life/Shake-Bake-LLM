"""Execute only our trusted preparation code in a bounded Linux child."""

import ctypes
import json
import os
import resource
import signal
import sys


def main() -> int:
    try:
        if sys.platform != "linux" or len(sys.argv) != 2:
            raise RuntimeError("unsupported")
        expected_parent = int(sys.argv[1])
        # Arm before reading any task or source. Catch parent exit before arming.
        if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            raise RuntimeError("parent supervision unavailable")
        if os.getppid() != expected_parent:
            return 1
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024, 256 * 1024))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(45)
        raw = sys.stdin.buffer.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise RuntimeError("oversized request")
        from .briefing import build_brief
        from .contracts import Refusal
        from .worker import parse_json
        from pathlib import Path
        request = parse_json(raw.decode("utf-8"))
        base = {"root", "task", "model", "port"}
        routed = base | {"policy_path", "task_kind", "disabled"}
        if not isinstance(request, dict) or set(request) not in (base, routed, routed | {"candidate"}):
            raise RuntimeError("invalid request")
        try:
            if "candidate" in request:
                from .routing import candidate_trial
                decision, brief = candidate_trial(Path(request["root"]), request["task"], request["task_kind"],
                    request["candidate"], port=request["port"])
                result = brief.to_dict()
                result["routing"] = decision.to_dict()
            elif "policy_path" in request:
                from .routing import assist
                decision, brief = assist(Path(request["root"]), request["task"], request["task_kind"],
                                         policy_path=Path(request["policy_path"]), port=request["port"], disabled=request["disabled"])
                result = brief.to_dict()
                result["routing"] = decision.to_dict()
            else:
                result = build_brief(Path(request["root"]), request["task"], model=request["model"], port=request["port"]).to_dict()
        except Refusal as refusal:
            result = {"outcome": "DENY", "code": refusal.code}
        text = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(text) > 256 * 1024:
            raise RuntimeError("oversized result")
        sys.stdout.buffer.write(text + b"\n")
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        print('{"outcome":"ERROR","code":"runner_failed"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

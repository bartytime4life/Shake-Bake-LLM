"""Readiness checks; no downloads, generation, source collection or repairs."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import socket
import sys
import time

from . import __version__
from .contracts import Refusal
from .capabilities import computer_snapshot
from .worker import canonical_model, local_inventory, local_model_metadata, local_runtime, validate_settings, worker_configuration


def inspect_model(model, port=11434, *, expected_digest=None):
    validate_settings(model, port)
    if expected_digest is not None and (not isinstance(expected_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_digest)):
        raise Refusal("invalid_expected_digest")
    deadline = time.monotonic() + 5
    inventory = local_inventory(port, deadline)
    digest = inventory.get(canonical_model(model))
    if digest is None:
        raise Refusal("model_not_installed")
    if expected_digest is not None and digest != expected_digest:
        raise Refusal("qualified_model_digest_changed")
    runtime = local_runtime(port, deadline)
    metadata = local_model_metadata(model, port, deadline)
    if local_inventory(port, deadline).get(canonical_model(model)) != digest:
        raise Refusal("model_identity_changed_during_preflight")
    if local_runtime(port, deadline) != runtime:
        raise Refusal("worker_runtime_changed")
    # Do not copy arbitrary templates, licenses or model parameters into a receipt.
    details = metadata.get("details", {})
    details = details if isinstance(details, dict) else {}
    info = metadata["model_info"]
    context = info.get(str(info.get("general.architecture", "")) + ".context_length")
    context = context if type(context) is int and 1 <= context <= 2**31 else None
    capabilities = metadata.get("capabilities")
    capabilities = [x[:64] for x in capabilities[:16] if isinstance(x, str)] if isinstance(capabilities, list) else None
    thinking = metadata.get("thinking")
    values = thinking.get("values") if isinstance(thinking, dict) else None
    can_disable = any(value is False for value in values) if isinstance(values, list) else None
    return {"model": canonical_model(model), "reported_digest": digest, "runtime_version": runtime,
            "observed_at": datetime.now(timezone.utc).isoformat(), "reported_context_length": context,
            "reported_capabilities": capabilities, "reported_thinking_can_disable": can_disable,
            "requested_configuration": worker_configuration(), "accuracy_status": "unqualified",
            "reported_details": {key: details[key][:128] for key in ("format", "family", "parameter_size", "quantization_level")
                                 if isinstance(details.get(key), str)},
            "generation_requested": False, "source_sent": False,
            "weight_bytes_attested": False}


def inspect(*, gui_port=8421, check_ollama=False, model=None, ollama_port=11434):
    if type(gui_port) is not int or not 1 <= gui_port <= 65535:
        raise Refusal("invalid_gui_port")
    if type(ollama_port) is not int or not 1 <= ollama_port <= 65535:
        raise Refusal("invalid_worker_port")
    if model is not None and not check_ollama:
        raise Refusal("model_requires_explicit_ollama_check")
    root = Path(__file__).resolve().parent
    required = ("web/index.html", "web/styles.css", "web/app.js", "web/models.json", "default-policy.json", "demo/validator.py")
    missing = [name for name in required if not (root / name).is_file()]
    checks = [
        {"name": "Python 3.11 or newer", "status": "PASS" if sys.version_info >= (3, 11) else "FAIL"},
        {"name": "Linux process boundary", "status": "PASS" if sys.platform.startswith("linux") else "FAIL"},
        {"name": "Workbench package assets", "status": "FAIL" if missing else "PASS", "missing": missing},
    ]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", gui_port))
        checks.append({"name": "Workbench port", "status": "PASS", "port": gui_port})
    except OSError:
        checks.append({"name": "Workbench port", "status": "FAIL", "port": gui_port,
                       "action": "If the workbench is already open, use it; otherwise choose --port with another local port."})
    ollama = {"status": "NOT_CHECKED", "generation_requested": False, "source_sent": False}
    if check_ollama:
        try:
            if model is not None:
                ollama = {"status": "PASS", **inspect_model(model, ollama_port)}
            else:
                inventory = local_inventory(ollama_port, time.monotonic() + 5)
                ollama = {"status": "PASS", "installed_models": sorted(inventory),
                          "generation_requested": False, "source_sent": False,
                          "note": "Inventory only; select --model to inspect that model's local metadata."}
        except Refusal as error:
            ollama = {"status": "FAIL", "code": error.code, "generation_requested": False, "source_sent": False}
    computer = computer_snapshot()
    ready = all(check["status"] == "PASS" for check in checks)
    return {"kind": "local_readiness_report", "helper_version": __version__,
            "environment": {"system": platform.system(), "machine": platform.machine(),
                            "python": platform.python_version(), "physical_ram_bytes": computer["physical_ram_bytes"],
                            "gpu_vram_bytes": None, "gpu_throughput": None},
            "computer": computer,
            "gui_startup_checks_passed": ready, "checks": checks, "ollama": ollama,
            "model_accuracy": None, "cloud_savings": None,
            "limits": "Port availability is a point-in-time probe. No model ran; browser rendering and owner-PC behavior are not qualified."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8421, dest="gui_port")
    parser.add_argument("--check-ollama", action="store_true", help="Explicit metadata-only loopback check; no generation")
    parser.add_argument("--model", help="Exact installed model to inspect; requires --check-ollama")
    parser.add_argument("--ollama-port", type=int, default=11434)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect(gui_port=args.gui_port, check_ollama=args.check_ollama, model=args.model, ollama_port=args.ollama_port)
    except Refusal as error:
        print(json.dumps({"outcome": "DENY", "code": error.code}))
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Shake and Bake startup checks")
        for check in result["checks"]:
            print(f"{check['status']}: {check['name']}")
            if check.get("action"):
                print("  " + check["action"])
        print("Ollama: " + result["ollama"]["status"] + (" — " + result["ollama"]["code"] if result["ollama"].get("code") else ""))
        print("No model ran. Accuracy and savings remain unmeasured.")
    return 0 if result["gui_startup_checks_passed"] and result["ollama"]["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

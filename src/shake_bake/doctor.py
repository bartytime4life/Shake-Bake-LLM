"""Readiness checks; no downloads, generation, source collection or repairs."""

import argparse
import json
import os
from pathlib import Path
import platform
import socket
import sys
import time

from . import __version__
from .contracts import Refusal
from .worker import canonical_model, local_inventory, local_model_metadata, validate_settings


def inspect_model(model, port=11434):
    validate_settings(model, port)
    deadline = time.monotonic() + 5
    inventory = local_inventory(port, deadline)
    digest = inventory.get(canonical_model(model))
    if digest is None:
        raise Refusal("model_not_installed")
    metadata = local_model_metadata(model, port, deadline)
    if local_inventory(port, deadline).get(canonical_model(model)) != digest:
        raise Refusal("model_identity_changed_during_preflight")
    # Do not copy arbitrary templates, licenses or model parameters into a receipt.
    details = metadata.get("details", {})
    details = details if isinstance(details, dict) else {}
    return {"model": canonical_model(model), "reported_digest": digest,
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
    try:
        memory = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError, OSError):
        memory = None
    ready = all(check["status"] == "PASS" for check in checks)
    return {"kind": "local_readiness_report", "helper_version": __version__,
            "environment": {"system": platform.system(), "machine": platform.machine(),
                            "python": platform.python_version(), "physical_ram_bytes": memory,
                            "gpu_vram_bytes": None, "gpu_throughput": None},
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

"""Local terminal entry point. JSON is the default evidence handoff format."""

import argparse
from dataclasses import asdict
from importlib.resources import files
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
import tempfile

from . import __version__
from .config import Configuration, load_config
from .contracts import MAX_REQUEST_BYTES, Refusal, Selection
from .engine import Engine
from .policy import require_posix


def selection_argument(text: str):
    try:
        path, start, end = text.rsplit(":", 2)
        return asdict(Selection(path, int(start), int(end)))
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("Use a relative path followed by :first_line:last_line.") from None


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def demo():
    with tempfile.TemporaryDirectory(prefix="shake-bake-demo-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        (root / "example.txt").write_bytes(files("shake_bake").joinpath("fixtures/example.txt").read_bytes())
        config = Configuration(base / "state", {"demo": root})
        with Engine(config) as engine:
            job = engine.start_job("demo", "Prepare the exact failure evidence; leave diagnosis open.",
                                   [{"path": "example.txt", "start_line": 1, "end_line": 3}])
            emit(engine.wait("demo", job["job_id"]))
    return 0


def parser():
    root = argparse.ArgumentParser(description="Shake & Bake: prepare exact local evidence for an assistant.")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Run an offline synthetic task in a temporary workspace.")
    commands.add_parser("doctor", help="Check this runtime without inspecting a real project or contacting a service.")
    commands.add_parser("gui", help="Open the local workbench; gui --help lists launch options.")
    prepare = commands.add_parser("prepare", help="Capture explicitly selected source ranges.")
    prepare.add_argument("--config", required=True, type=Path)
    prepare.add_argument("--project", required=True)
    request = prepare.add_mutually_exclusive_group(required=True)
    request.add_argument("--request")
    request.add_argument("--request-file", type=Path)
    prepare.add_argument("--select", action="append", type=selection_argument, help="Omit for bounded lexical discovery.")
    prepare.add_argument("--task-kind", choices=("code", "troubleshoot", "documents", "search"), default="code")
    prepare.add_argument("--local-ai", choices=("off", "best", "trial"), default="off")
    prepare.add_argument("--model")
    prepare.add_argument("--digest")
    for command in ("models", "profile-info"):
        item = commands.add_parser(command)
        item.add_argument("--config", required=True, type=Path)
    for command in ("result", "evidence"):
        item = commands.add_parser(command, help="Read a captured receipt from an idle state store.")
        item.add_argument("--config", required=True, type=Path)
        item.add_argument("--project", required=True)
        item.add_argument("--job", required=True)
        if command == "evidence":
            item.add_argument("--id", required=True)
    return root


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "gui":
        from .gui import main as gui_main
        return gui_main(argv[1:])
    args = parser().parse_args(argv)
    try:
        require_posix()
        if args.command == "doctor":
            emit({"version": __version__, "python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
                  "posix_collector": True, "runtime_dependencies": [], "network_contacted": False,
                  "model_readiness": "not_checked", "native_host_integration": "unqualified"})
            return 0
        if args.command == "demo":
            return demo()
        config = load_config(args.config)
        with Engine(config) as engine:
            if args.command == "models":
                emit(engine.inventory())
                return 0
            if args.command == "profile-info":
                emit({"device_id": engine.device_id, "pipeline_sha256": engine.pipeline, "profiles": engine.profiles})
                return 0
            if args.command == "prepare":
                request = args.request
                if args.request_file is not None:
                    fd = os.open(args.request_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(fd, "rb") as handle:
                        metadata = os.fstat(handle.fileno())
                        if not stat.S_ISREG(metadata.st_mode):
                            raise Refusal("request_file_type", "The request file must be a regular UTF-8 file.")
                        raw = handle.read(MAX_REQUEST_BYTES + 1)
                    if len(raw) > MAX_REQUEST_BYTES:
                        raise Refusal("invalid_request", "The request file exceeds the request byte limit.")
                    request = raw.decode("utf-8")
                job = engine.start_job(args.project, request, args.select, task_kind=args.task_kind,
                                       ai_mode=args.local_ai, model=args.model, digest=args.digest)
                try:
                    result = engine.wait(args.project, job["job_id"])
                except KeyboardInterrupt:
                    engine.cancel_job(args.project, job["job_id"])
                    emit(engine.wait(args.project, job["job_id"]))
                    return 130
                emit(result)
                return 0 if result["status"] == "prepared" else 2
            if args.command == "evidence":
                emit(engine.fetch_evidence(args.project, args.job, args.id))
            else:
                emit(engine.get_result(args.project, args.job))
        return 0
    except Refusal as exc:
        emit({"status": "refused", "error": exc.to_dict()})
        return 2
    except (OSError, UnicodeError, sqlite3.Error):
        emit({"status": "failed", "error": {"code": "local_io", "message": "A local file or state operation failed. Check paths, permissions and available disk space."}})
        return 2

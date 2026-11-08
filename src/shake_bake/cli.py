"""Print a source packet to stdout; never write it into the selected project."""

import argparse
import json
from pathlib import Path
import sys

from .collector import build_packet
from .contracts import Refusal, Selection
from .briefing import build_brief, render, render_orientation


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "brief":
        return brief_main(argv[1:])
    if argv and argv[0] == "assist":
        return assist_main(argv[1:])
    if argv and argv[0] == "gui":
        from .gui import main as gui_main
        return gui_main(argv[1:])
    if argv and argv[0] == "doctor":
        from .doctor import main as doctor_main
        return doctor_main(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--start-line", required=True, type=int)
    parser.add_argument("--end-line", required=True, type=int)
    args = parser.parse_args(argv)
    try:
        packet = build_packet(args.root, args.task, (Selection(args.file, args.start_line, args.end_line),))
    except Refusal as refusal:
        print(json.dumps({"outcome": "DENY", "code": refusal.code}, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({"outcome": "ERROR", "code": "collection_failed"}, sort_keys=True))
        return 1
    print(json.dumps(packet.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def brief_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Select source and prepare a verifiable cloud handoff.")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--model", help="Explicitly enable an installed local Ollama model; no download is performed.")
    parser.add_argument("--task-kind", choices=("code", "troubleshoot", "documents", "search"), help="Optional hint for the local model's drafted prompt; collection is unchanged.")
    parser.add_argument("--ollama-port", type=int, default=11434)
    parser.add_argument("--rerank-model", help="Explicitly enable an installed local embedding model that reorders candidate windows; it adds no window and no download is performed.")
    parser.add_argument("--style", choices=("evidence", "orientation"), default="evidence",
                        help="Markdown layout: the evidence brief (default) or the candidate orientation brief.")
    args = parser.parse_args(argv)
    try:
        brief = build_brief(args.root, args.task, model=args.model, port=args.ollama_port, task_kind=args.task_kind, rerank_model=args.rerank_model)
    except Refusal as refusal:
        print(json.dumps({"outcome": "DENY", "code": refusal.code}, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({"outcome": "ERROR", "code": "preparation_failed"}, sort_keys=True))
        return 1
    print(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) if args.format == "json" else (render_orientation(brief) if args.style == "orientation" else render(brief)), end="\n" if args.format == "json" else "")
    return 0 if brief.outcome == "ANSWER" else 3


def assist_main(argv: list[str]) -> int:
    from .routing import TASK_KINDS, assist
    parser = argparse.ArgumentParser(description="Prepare evidence using an owner-reviewed task profile, with an explicit explanation.")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--task-kind", required=True, choices=TASK_KINDS)
    parser.add_argument("--policy", type=Path, help="Owner-controlled policy outside the inspected source root")
    parser.add_argument("--disable-local-ai", action="store_true", help="Skip all local-model and inventory calls; retain evidence")
    parser.add_argument("--ollama-port", type=int, default=11434)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    try:
        decision, brief = assist(args.root, args.task, args.task_kind, policy_path=args.policy,
                                 port=args.ollama_port, disabled=args.disable_local_ai)
    except Refusal as refusal:
        print(json.dumps({"outcome": "DENY", "code": refusal.code}))
        return 2
    except Exception:
        print(json.dumps({"outcome": "ERROR", "code": "assistance_failed"}))
        return 1
    if args.format == "json":
        print(json.dumps({"result_kind": "preparation_result", "final_answer_ready": False,
                          "requires_host_reasoning": True, "routing": decision.to_dict(), "brief": brief.to_dict()},
                         ensure_ascii=False, indent=2))
    else:
        print("# Why this model\n\n" + decision.why + "\n\nRouting status: " + decision.reason + "\n\n" + render(brief), end="")
    return 0 if brief.worker is not None else 3

"""File-level recall of the collector on externally authored localization cases.

Reads a JSON Lines case file whose rows name a local repository checkout, a
request and the files a real fix changed, runs the unchanged collector with
declared limits and reports how many changed files appear among the exact
excerpts and the path map. This is mechanical recall of the collector on cases
this project did not author; it is not answer accuracy, not a cloud-host
result, and public datasets may be inside a cloud model's training data.
"""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

from shake_bake import __version__
import shake_bake.search as search_module
from shake_bake.contracts import Refusal
from shake_bake.search import SearchLimits, prepare

MAX_CASES = 5000
WARNING = ("File recall is not answer accuracy. Cases were authored outside this project but may be public; "
           "they qualify the collector's recall, never a cloud host's answers or any model.")


def _load_cases(path: Path, repos: Path | None) -> tuple[list[dict], str]:
    rows = []
    digest = hashlib.sha256()
    seen = set()
    with path.open("rb") as handle:
        for number, raw in enumerate(handle, 1):
            digest.update(raw)
            if not raw.strip():
                continue
            if number > MAX_CASES:
                raise Refusal("case_budget")
            row = json.loads(raw.decode("utf-8"))
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("request"), str):
                raise Refusal("invalid_case")
            if not row["id"] or row["id"] in seen:
                raise Refusal("duplicate_or_empty_case_id")
            seen.add(row["id"])
            changed = row.get("changed_files")
            if not isinstance(changed, list) or not changed or not all(isinstance(item, str) and item for item in changed):
                raise Refusal("invalid_case")
            root = Path(row.get("root", ""))
            if not root.is_absolute():
                if repos is None:
                    raise Refusal("case_root_requires_repos_dir")
                root = repos / root
            rows.append({"id": row["id"], "root": root, "request": row["request"], "changed_files": sorted(set(changed))})
    if not rows:
        raise Refusal("no_cases")
    return rows, digest.hexdigest()


def load_cases(path: Path, repos: Path | None) -> list[dict]:
    return _load_cases(path, repos)[0]


def source_identity() -> dict:
    """On-disk benchmark/collector provenance, not loaded-code attestation."""
    package = Path(search_module.__file__).resolve().parent
    names = ("__init__.py", "contracts.py", "collector.py", "search.py", "rerank.py", "worker.py")
    return {"adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "collector_sources_sha256": {name: hashlib.sha256((package / name).read_bytes()).hexdigest()
                                         for name in names if (package / name).is_file()}}


def _hash_json(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _check_output(path: Path | None, cases: list[dict]) -> None:
    if path is None:
        return
    output = path.resolve()
    package = Path(search_module.__file__).resolve().parent
    collector_source = package.parent.parent if package.parent.name == "src" else package
    protected = [Path(__file__).resolve().parents[1], collector_source] + [case["root"].resolve() for case in cases]
    if any(output == root or root in output.parents for root in protected):
        raise Refusal("receipt_output_inside_source")
    if path.exists() or path.is_symlink():
        raise Refusal("receipt_output_exists")


def run(cases: list[dict], limits: SearchLimits, scorer=None) -> dict:
    repository = Path(__file__).resolve().parents[1]
    results = []
    for case in cases:
        root = case["root"]
        row = {"id": case["id"], "changed_files": len(case["changed_files"])}
        if not root.is_dir() or root.is_symlink() or root.resolve() == repository or repository in root.resolve().parents:
            row["refused"] = "case_root_not_allowed"
            results.append(row)
            continue
        started = time.perf_counter()
        try:
            result = prepare(root, case["request"], limits) if scorer is None else prepare(root, case["request"], limits, scorer)
        except Refusal as refusal:
            row["refused"] = refusal.code
            results.append(row)
            continue
        row["seconds"] = round(time.perf_counter() - started, 3)
        if getattr(result, "rerank", None) is not None:
            row["rerank"] = {key: result.rerank.get(key) for key in ("model", "pool", "candidates", "order_changed", "error", "elapsed_seconds", "embed_calls", "truncated_windows") if key in result.rerank}
        evidence = list(result.packet.evidence) if result.packet else []
        # Controlling context follows the actual primary windows, which may
        # number fewer than the four-window ceiling. Never count that context
        # as primary merely because it appears among the first four records.
        context_ids = {item["evidence_id"] for item in result.context}
        primary_evidence = [record for number, record in enumerate(evidence, 1)
                            if f"E{number}" not in context_ids]
        primary = {record.path for record in primary_evidence}
        excerpted = {record.path for record in evidence}
        mapped = {item["path"] for item in result.context_map}
        line_index = getattr(result, "line_index", ())
        indexed = {entry["path"] for entry in line_index}
        changed = set(case["changed_files"])
        row.update({
            "files_examined": result.files_examined, "matching_files": result.matching_files,
            "primary_excerpts": len(primary_evidence),
            "controlling_context_excerpts": len(evidence) - len(primary_evidence),
            "excerpts": len(evidence), "map_entries": len(result.context_map), "index_files": len(line_index),
            "cutoffs": list(result.cutoffs), "exclusions": dict(result.exclusions),
            "hits_primary": len(changed & primary), "hits_excerpted": len(changed & excerpted),
            "hits_with_map": len(changed & (excerpted | mapped)),
            "hits_with_index": len(changed & (excerpted | mapped | indexed)),
            "recall_primary": len(changed & primary) / len(changed),
            "recall_excerpted": len(changed & excerpted) / len(changed),
            "recall_with_map": len(changed & (excerpted | mapped)) / len(changed),
            "recall_with_index": len(changed & (excerpted | mapped | indexed)) / len(changed),
        })
        results.append(row)
    scored = [row for row in results if "refused" not in row]

    def mean(key):
        return round(sum(row[key] for row in scored) / len(scored), 4) if scored else None

    def any_hit(key):
        return round(sum(1 for row in scored if row[key] > 0) / len(scored), 4) if scored else None

    return {
        "kind": "external_file_recall", "helper_version": __version__, "limits": limits.__dict__,
        "case_count": len(results), "scored": len(scored), "refused": len(results) - len(scored),
        "mean_recall_primary": mean("recall_primary"), "mean_recall_excerpted": mean("recall_excerpted"),
        "mean_recall_with_map": mean("recall_with_map"), "mean_recall_with_index": mean("recall_with_index"),
        "cases_with_any_primary_hit": any_hit("hits_primary"), "cases_with_any_excerpted_hit": any_hit("hits_excerpted"),
        "cases_with_any_hit_including_map": any_hit("hits_with_map"), "cases_with_any_hit_including_index": any_hit("hits_with_index"),
        "cases_hitting_file_budget": sum(1 for row in scored if "file_budget" in row["cutoffs"]),
        "cases_hitting_time_budget": sum(1 for row in scored if "time_budget" in row["cutoffs"]),
        "cases": results, "warning": WARNING,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, required=True, help="JSON Lines: id, root, request, changed_files")
    parser.add_argument("--repos", type=Path, help="Directory that relative case roots are under")
    parser.add_argument("--max-files", type=int, default=SearchLimits().max_files)
    parser.add_argument("--max-entries", type=int, default=SearchLimits().max_entries)
    parser.add_argument("--max-depth", type=int, default=SearchLimits().max_depth)
    parser.add_argument("--seconds", type=float, default=SearchLimits().seconds)
    parser.add_argument("--excerpt-bytes", type=int, default=SearchLimits().excerpt_bytes)
    parser.add_argument("--context-bytes", type=int, default=SearchLimits().context_bytes)
    parser.add_argument("--limit", type=int, help="Score only the first N cases")
    parser.add_argument("--output", type=Path, help="Receipt path outside the checkout")
    parser.add_argument("--rerank-model", help="Explicit installed local embedding model that reorders candidate windows; no automatic downloads")
    parser.add_argument("--ollama-port", type=int, default=11434)
    args = parser.parse_args(argv)
    limits = SearchLimits(max_files=args.max_files, max_entries=args.max_entries, max_depth=args.max_depth,
                          seconds=args.seconds, excerpt_bytes=args.excerpt_bytes, context_bytes=args.context_bytes)
    limits.validate()
    if args.limit is not None and args.limit <= 0:
        raise Refusal("invalid_case_limit")
    cases, input_hash = _load_cases(args.cases, args.repos)
    if args.limit is not None:
        cases = cases[:args.limit]
    _check_output(args.output, cases)
    code_identity = source_identity()
    selection_hash = _hash_json([{"id": c["id"], "request": c["request"], "changed_files": c["changed_files"]} for c in cases])
    roots_hash = _hash_json([{ "id": c["id"], "root": str(c["root"].resolve())} for c in cases])
    scorer = None
    if args.rerank_model:
        from shake_bake.rerank import EmbeddingScorer
        scorer = EmbeddingScorer(args.rerank_model, port=args.ollama_port)
    report = run(cases, limits, scorer)
    if hashlib.sha256(args.cases.read_bytes()).hexdigest() != input_hash:
        raise Refusal("evaluation_cases_changed")
    if source_identity() != code_identity:
        raise Refusal("evaluation_code_changed")
    report["rerank_model"] = args.rerank_model
    report.update({"receipt_schema": 2, "cases_sha256": input_hash,
                   "selection_sha256": selection_hash, "case_root_locations_sha256": roots_hash,
                   "selected_case_ids": [case["id"] for case in cases], "source_identity": code_identity,
                   "python": sys.version, "platform": platform.platform(),
                   "corpus_content_immutability_verified": False,
                   "provenance_scope": "On-disk source hashes and declared case/root identities; no whole-corpus or loaded-code attestation.",
                   "timing_scope": "One untraced prepare call per case; excludes input/provenance hashing."})
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(json.dumps({key: report[key] for key in report if key != "cases"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

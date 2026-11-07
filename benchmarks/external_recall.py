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
import time

from shake_bake import __version__
from shake_bake.contracts import Refusal
from shake_bake.search import PRIMARY_FILES, SearchLimits, prepare

MAX_CASES = 5000
WARNING = ("File recall is not answer accuracy. Cases were authored outside this project but may be public; "
           "they qualify the collector's recall, never a cloud host's answers or any model.")


def load_cases(path: Path, repos: Path | None) -> list[dict]:
    rows = []
    with path.open("rb") as handle:
        for number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            if number > MAX_CASES:
                raise Refusal("case_budget")
            row = json.loads(raw.decode("utf-8"))
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("request"), str):
                raise Refusal("invalid_case")
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
    return rows


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
            result = prepare(root, case["request"], limits, scorer)
        except Refusal as refusal:
            row["refused"] = refusal.code
            results.append(row)
            continue
        row["seconds"] = round(time.perf_counter() - started, 3)
        if result.rerank is not None:
            row["rerank"] = {key: result.rerank.get(key) for key in ("model", "pool", "candidates", "order_changed", "error", "elapsed_seconds", "embed_calls", "truncated_windows") if key in result.rerank}
        evidence = list(result.packet.evidence) if result.packet else []
        primary = {record.path for record in evidence[:PRIMARY_FILES]}
        excerpted = {record.path for record in evidence}
        mapped = {item["path"] for item in result.context_map}
        indexed = {entry["path"] for entry in result.line_index}
        changed = set(case["changed_files"])
        row.update({
            "files_examined": result.files_examined, "matching_files": result.matching_files,
            "excerpts": len(evidence), "map_entries": len(result.context_map), "index_files": len(result.line_index),
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
    parser.add_argument("--seconds", type=float, default=SearchLimits().seconds)
    parser.add_argument("--context-bytes", type=int, default=SearchLimits().context_bytes)
    parser.add_argument("--limit", type=int, help="Score only the first N cases")
    parser.add_argument("--output", type=Path, help="Receipt path outside the checkout")
    parser.add_argument("--rerank-model", help="Explicit installed local embedding model that reorders candidate windows; no automatic downloads")
    parser.add_argument("--ollama-port", type=int, default=11434)
    args = parser.parse_args(argv)
    limits = SearchLimits(max_files=args.max_files, max_entries=args.max_entries, seconds=args.seconds, context_bytes=args.context_bytes)
    limits.validate()
    cases = load_cases(args.cases, args.repos)
    if args.limit:
        cases = cases[:args.limit]
    scorer = None
    if args.rerank_model:
        from shake_bake.rerank import EmbeddingScorer
        scorer = EmbeddingScorer(args.rerank_model, port=args.ollama_port)
    report = run(cases, limits, scorer)
    report["rerank_model"] = args.rerank_model
    report["cases_sha256"] = hashlib.sha256(args.cases.read_bytes()).hexdigest()
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key != "cases"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

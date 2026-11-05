"""Replay exposed development jobs; mechanical coverage is not model accuracy."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from shake_bake.briefing import build_brief
from shake_bake import __version__
from shake_bake.contracts import Refusal
from shake_bake.search import SearchLimits

LAB = Path(__file__).resolve().parent / "task-lab"


def tree_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def grade_coverage(brief, key):
    """Only source integrity, required spans and disclosed scan limits."""
    records = brief.search.packet.evidence if brief.search.packet else ()
    missing = [anchor for anchor in key["anchors"]
               if not any(record.path == anchor["path"] and anchor["contains"] in record.text for record in records)]
    hashes_valid = all(hashlib.sha256(record.text.encode()).hexdigest() == record.excerpt_sha256 for record in records)
    missing_cutoffs = sorted(set(key["required_cutoffs"]) - set(brief.search.cutoffs))
    return {"all_required_spans_present": not missing, "missing_required_spans": missing,
            "excerpt_hashes_valid": hashes_valid, "missing_expected_cutoffs": missing_cutoffs,
            "mechanical_pass": not missing and hashes_valid and not missing_cutoffs}


def run_cases(*, model=None, port=11434, case_ids=None, expected_digest=None):
    cases = json.loads((LAB / "manifest.json").read_text())["cases"]
    keys = json.loads((LAB / "grading-keys.json").read_text())["cases"]
    if case_ids and set(case_ids) - {case["id"] for case in cases}:
        raise ValueError("unknown_case")
    results = []
    for case in cases:
        if case_ids and case["id"] not in case_ids:
            continue
        root = LAB / "fixtures" / case["id"]
        before = tree_hash(root)
        started = time.monotonic()
        try:
            # Grading keys are never passed into build_brief or the worker packet.
            brief = build_brief(root, case["task"], model=model, port=port, limits=SearchLimits(**case["limits"]), expected_digest=expected_digest)
            coverage = grade_coverage(brief, keys[case["id"]])
            payload = brief.to_dict()
            error = None
        except Refusal as refusal:
            coverage = {"mechanical_pass": False}
            payload = None
            error = refusal.code
        unchanged = tree_hash(root) == before
        results.append({"id": case["id"], "task": case["task"], "elapsed_seconds": round(time.monotonic()-started, 6),
                        "fixture_unchanged": unchanged, "fixture_sha256": before, "coverage": coverage,
                        "brief": payload, "error": error,
                        "semantic_review": {"status": "PENDING", "critical_misses": None,
                                            "unsupported_claims": None, "useful_abstention": None}})
    worker_errors = sum(bool(r["error"] or (r["brief"] or {}).get("worker_error")) for r in results)
    return {"kind": "exposed_development_task_lab", "helper_version": __version__, "model": model,
            "case_manifest_sha256": hashlib.sha256((LAB / "manifest.json").read_bytes()).hexdigest(),
            "grading_keys_sha256": hashlib.sha256((LAB / "grading-keys.json").read_bytes()).hexdigest(),
            "mode": "ollama_candidate" if model else "evidence_only_diagnostic",
            "cases": results, "mechanical_passes": sum(r["coverage"]["mechanical_pass"] and r["fixture_unchanged"] for r in results),
            "case_count": len(results), "semantic_model_accuracy": None,
            "worker_errors": worker_errors,
            "actual_model_calls_requested": model is not None, "cloud_usage_measured": False,
            "warning": "Span coverage is not semantic accuracy. All model interpretations require separate review."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--model", help="Explicit installed local model; no automatic downloads")
    mode.add_argument("--evidence-only", action="store_true")
    parser.add_argument("--ollama-port", type=int, default=11434)
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--output", type=Path, help="Optional receipt path outside the fixture roots")
    args = parser.parse_args(argv)
    if args.output and (LAB / "fixtures").resolve() in (args.output.resolve(), *args.output.resolve().parents):
        parser.error("output must be outside fixture roots")
    try:
        result = run_cases(model=args.model, port=args.ollama_port, case_ids=args.case_ids)
    except ValueError as error:
        parser.error(str(error))
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(json.dumps({key: result[key] for key in ("kind", "mode", "case_count", "mechanical_passes", "semantic_model_accuracy")}))
    else:
        print(output, end="")
    return 0 if result["mechanical_passes"] == result["case_count"] and not result["worker_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

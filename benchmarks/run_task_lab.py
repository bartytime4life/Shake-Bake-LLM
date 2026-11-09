"""Replay exposed development jobs; mechanical coverage is not model accuracy."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

from shake_bake.briefing import build_brief
from shake_bake import __version__
from shake_bake.contracts import Refusal
from shake_bake.collector import MAX_REQUEST_CHARS, _parts, _read
from shake_bake.search import SearchLimits
from shake_bake import worker as worker_module
from shake_bake.worker import parse_json

LAB = Path(__file__).resolve().parent / "task-lab"


def tree_hash(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise Refusal("invalid_dataset_fixture")
    digest = hashlib.sha256()
    entries, total_bytes = 0, 0
    def unavailable(error):
        raise Refusal("dataset_fixture_unavailable") from error
    for directory, directories, files in os.walk(root, followlinks=False, onerror=unavailable):
        directories.sort()
        for name in sorted(directories + files):
            path = Path(directory) / name
            info = path.lstat()
            entries += 1
            if entries > 4000:
                raise Refusal("dataset_fixture_budget")
            if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise Refusal("dataset_links_or_special_files_refused")
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink != 1:
                    raise Refusal("dataset_links_or_special_files_refused")
                relative = path.relative_to(root).as_posix()
                data = _read(root, relative)
                total_bytes += len(data)
                if total_bytes > 32 * 1024 * 1024:
                    raise Refusal("dataset_fixture_budget")
                digest.update(relative.encode())
                digest.update(b"\0" + data + b"\0")
    return digest.hexdigest()


def load_dataset(dataset=None):
    """An external split label is an owner declaration, never qualification."""
    root = Path(dataset if dataset is not None else LAB).resolve(strict=True)
    manifest_bytes = _read(root, "manifest.json")
    keys_bytes = _read(root, "grading-keys.json")
    manifest, key_document = parse_json(manifest_bytes.decode()), parse_json(keys_bytes.decode())
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "1" or not isinstance(key_document, dict):
        raise Refusal("invalid_dataset")
    if dataset is None or root == LAB.resolve():
        dataset_id, split = "bundled-task-lab-v1", "development"
    else:
        dataset_id, split = manifest.get("dataset_id"), manifest.get("split")
        if not isinstance(dataset_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", dataset_id) or split not in ("development", "held_out"):
            raise Refusal("invalid_dataset_identity")
        repository = Path(__file__).resolve().parents[1]
        if split == "held_out" and (root == repository or repository in root.parents):
            raise Refusal("held_out_dataset_must_be_outside_checkout")
    cases, keys = manifest.get("cases"), key_document.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 1000 or not isinstance(keys, dict):
        raise Refusal("invalid_dataset_cases")
    seen = set()
    fixtures = root / "fixtures"
    if fixtures.is_symlink() or not fixtures.is_dir():
        raise Refusal("invalid_dataset_fixture")
    for case in cases:
        if not isinstance(case, dict):
            raise Refusal("invalid_dataset_case")
        identifier, task, limits = case.get("id"), case.get("task"), case.get("limits")
        if (not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", identifier) or identifier in seen or
                not isinstance(task, str) or not task.strip() or len(task) > MAX_REQUEST_CHARS or not isinstance(limits, dict)):
            raise Refusal("invalid_dataset_case")
        seen.add(identifier)
        if set(limits) - set(SearchLimits.__dataclass_fields__):
            raise Refusal("invalid_search_limits")
        SearchLimits(**limits).validate()
        fixture = fixtures / identifier
        if fixture.is_symlink() or not fixture.is_dir():
            raise Refusal("invalid_dataset_fixture")
        key = keys.get(identifier)
        if not isinstance(key, dict) or not isinstance(key.get("anchors"), list) or len(key["anchors"]) > 32 or not isinstance(key.get("required_cutoffs"), list):
            raise Refusal("invalid_dataset_grading_key")
        for anchor in key["anchors"]:
            if (not isinstance(anchor, dict) or set(anchor) != {"path", "contains"} or
                    not isinstance(anchor["contains"], str) or not 1 <= len(anchor["contains"]) <= 4096):
                raise Refusal("invalid_dataset_grading_key")
            _parts(anchor["path"])
        if len(key["required_cutoffs"]) > 16 or any(not isinstance(item, str) or len(item) > 64 for item in key["required_cutoffs"]):
            raise Refusal("invalid_dataset_grading_key")
    if set(keys) != seen:
        raise Refusal("dataset_grading_case_mismatch")
    identity = {"dataset_id": dataset_id, "split": split, "split_is_owner_declared": True,
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "grading_keys_sha256": hashlib.sha256(keys_bytes).hexdigest()}
    return root, cases, keys, identity


def dataset_matches(root, identity):
    try:
        return all(hashlib.sha256(_read(root, name)).hexdigest() == identity[field]
                   for name, field in (("manifest.json", "manifest_sha256"), ("grading-keys.json", "grading_keys_sha256")))
    except (Refusal, OSError):
        return False


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


def run_cases(*, model=None, port=11434, case_ids=None, expected_digest=None, expected_runtime=None, dataset=None, rerank_model=None):
    dataset_root, cases, keys, identity = load_dataset(dataset)
    if case_ids and set(case_ids) - {case["id"] for case in cases}:
        raise ValueError("unknown_case")
    results = []
    for case in cases:
        if case_ids and case["id"] not in case_ids:
            continue
        root = dataset_root / "fixtures" / case["id"]
        before = tree_hash(root)
        started = time.monotonic()
        try:
            # Grading keys are never passed into build_brief or the worker packet.
            brief = build_brief(root, case["task"], model=model, port=port, limits=SearchLimits(**case["limits"]), expected_digest=expected_digest, expected_runtime=expected_runtime, rerank_model=rerank_model)
            coverage = grade_coverage(brief, keys[case["id"]])
            payload = brief.to_dict()
            error = None
        except Refusal as refusal:
            coverage = {"mechanical_pass": False}
            payload = None
            error = refusal.code
        unchanged = tree_hash(root) == before
        results.append({"id": case["id"], "task": case["task"], "elapsed_seconds": round(time.monotonic()-started, 6),
                        "dataset_unchanged": dataset_matches(dataset_root, identity),
                        "fixture_unchanged": unchanged, "fixture_sha256": before, "coverage": coverage,
                        "brief": payload, "error": error,
                        "semantic_review": {"status": "PENDING", "critical_misses": None,
                                            "unsupported_claims": None, "useful_abstention": None}})
    worker_errors = sum(bool(r["error"] or (r["brief"] or {}).get("worker_error")) for r in results)
    return {"kind": "external_dataset_task_lab" if dataset is not None else "exposed_development_task_lab", "helper_version": __version__, "model": model,
            "dataset": identity,
            "case_manifest_sha256": identity["manifest_sha256"],
            "grading_keys_sha256": identity["grading_keys_sha256"],
            "mode": "ollama_candidate" if model else "evidence_only_diagnostic",
            "datamark_source": worker_module.DATAMARK_SOURCE, "rerank_model": rerank_model,
            "cases": results, "mechanical_passes": sum(r["coverage"]["mechanical_pass"] and r["fixture_unchanged"] and r["dataset_unchanged"] for r in results),
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
    parser.add_argument("--dataset", type=Path, help="Owner-selected private dataset directory; see docs/held-out-evaluation.md")
    parser.add_argument("--output", type=Path, help="Optional receipt path outside the fixture roots")
    parser.add_argument("--datamark", action="store_true", help="Experiment: datamark the worker's copy of excerpt text; recorded in the receipt")
    parser.add_argument("--rerank-model", help="Explicit installed local embedding model that reorders candidate windows; no automatic downloads")
    args = parser.parse_args(argv)
    if args.datamark:
        if not args.model:
            parser.error("--datamark needs --model")
        worker_module.DATAMARK_SOURCE = True
    try:
        dataset_root, _, _, _ = load_dataset(args.dataset)
        if args.output and dataset_root in (args.output.resolve(), *args.output.resolve().parents):
            parser.error("output must be outside the dataset")
        result = run_cases(model=args.model, port=args.ollama_port, case_ids=args.case_ids, dataset=args.dataset, rerank_model=args.rerank_model)
    except ValueError as error:
        parser.error(str(error))
    except (Refusal, OSError, UnicodeError) as error:
        print(json.dumps({"outcome": "DENY", "code": error.code if isinstance(error, Refusal) else "dataset_file_error"}))
        return 2
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output)
        print(json.dumps({key: result[key] for key in ("kind", "mode", "case_count", "mechanical_passes", "semantic_model_accuracy")}))
    else:
        print(output, end="")
    return 0 if result["mechanical_passes"] == result["case_count"] and not result["worker_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

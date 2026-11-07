"""Compare paired file-recall receipts; no collection, model calls or downloads."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

MAX_RECEIPT_BYTES = 16 * 1024 * 1024
LEVELS = ("primary", "excerpted", "with_map", "with_index")
WARNING = ("This compares declared inputs and measured file recall, not corpus immutability, "
           "answer accuracy, cloud usage or costs. On-disk source hashes are not loaded-code attestation.")


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _validate(receipt):
    _require(isinstance(receipt, dict) and receipt.get("kind") == "external_file_recall", "invalid_recall_receipt")
    _require(receipt.get("receipt_schema") == 2, "receipt_provenance_required")
    _require(all(isinstance(receipt.get(key), str) and bool(receipt[key]) for key in ("python", "platform", "timing_scope")), "receipt_runtime_identity_required")
    _require("rerank_model" in receipt and receipt["rerank_model"] is None, "lexical_comparison_requires_no_rerank")
    for key in ("cases_sha256", "selection_sha256", "case_root_locations_sha256"):
        _require(_digest(receipt.get(key)), "receipt_provenance_required")
    identity = receipt.get("source_identity", {})
    _require(isinstance(identity, dict) and _digest(identity.get("adapter_sha256")), "receipt_source_identity_required")
    sources = identity.get("collector_sources_sha256", {})
    _require(isinstance(sources, dict) and {"__init__.py", "contracts.py", "collector.py", "search.py"} <= sources.keys()
             and all(_digest(value) for value in sources.values()), "receipt_source_identity_required")
    limits = receipt.get("limits")
    _require(isinstance(limits, dict) and set(limits) == {"max_files", "max_entries", "max_depth", "seconds", "excerpt_bytes", "context_bytes"}, "invalid_receipt_limits")
    for key, ceiling in (("max_files", 1000), ("max_entries", 10000), ("max_depth", 16), ("excerpt_bytes", 65536), ("context_bytes", 16384)):
        floor = 0 if key == "context_bytes" else 1
        _require(type(limits[key]) is int and floor <= limits[key] <= ceiling, "invalid_receipt_limits")
    _require(type(limits["seconds"]) in (int, float) and math.isfinite(limits["seconds"]) and 0 < limits["seconds"] <= 30, "invalid_receipt_limits")
    rows = receipt.get("cases")
    _require(isinstance(rows, list) and 1 <= len(rows) <= 5000, "invalid_receipt_cases")
    ids = []
    for row in rows:
        _require(isinstance(row, dict) and isinstance(row.get("id"), str) and bool(row["id"]), "invalid_receipt_case")
        ids.append(row["id"])
        gold = row.get("changed_files")
        _require(type(gold) is int and gold > 0, "invalid_receipt_gold_count")
        if "refused" in row:
            _require(isinstance(row["refused"], str) and bool(row["refused"]), "invalid_receipt_refusal")
            continue
        previous = 0
        for level in LEVELS:
            hits = row.get("hits_" + level)
            _require(type(hits) is int and previous <= hits <= gold, "invalid_receipt_hit_count")
            claimed = row.get("recall_" + level)
            _require(type(claimed) in (int, float) and math.isfinite(claimed) and math.isclose(claimed, hits / gold), "receipt_recall_inconsistent")
            previous = hits
        _require(type(row.get("seconds")) in (int, float) and math.isfinite(row["seconds"]) and row["seconds"] >= 0, "invalid_receipt_timing")
        _require(isinstance(row.get("cutoffs"), list) and all(isinstance(x, str) for x in row["cutoffs"]), "invalid_receipt_cutoffs")
        _require(isinstance(row.get("exclusions"), dict) and all(isinstance(k, str) and type(v) is int and v >= 0 for k, v in row["exclusions"].items()), "invalid_receipt_exclusions")
    _require(len(ids) == len(set(ids)), "duplicate_receipt_case_id")
    _require(type(receipt.get("case_count")) is int and receipt.get("selected_case_ids") == ids and receipt["case_count"] == len(ids), "receipt_selection_inconsistent")
    scored = sum("refused" not in row for row in rows)
    _require(type(receipt.get("scored")) is int and type(receipt.get("refused")) is int and receipt["scored"] == scored and receipt["refused"] == len(rows) - scored, "receipt_case_counts_inconsistent")
    return {row["id"]: row for row in rows}


def compare(before, after):
    old, new = _validate(before), _validate(after)
    for key in ("cases_sha256", "selection_sha256", "case_root_locations_sha256", "limits", "rerank_model", "python", "platform", "timing_scope"):
        _require(before.get(key) == after.get(key), "comparison_input_mismatch:" + key)
    _require(before["source_identity"]["adapter_sha256"] == after["source_identity"]["adapter_sha256"], "comparison_adapter_mismatch")
    _require(set(old) == set(new), "comparison_case_ids_mismatch")
    pairs, excluded = [], []
    for case_id in before["selected_case_ids"]:
        a, b = old[case_id], new[case_id]
        _require(a["changed_files"] == b["changed_files"], "comparison_gold_counts_mismatch")
        if "refused" in a or "refused" in b:
            excluded.append({"id": case_id, "before_refused": a.get("refused"), "after_refused": b.get("refused")})
            continue
        pairs.append((a, b))
    gold = sum(a["changed_files"] for a, _ in pairs)
    metrics = {}
    for level in LEVELS:
        deltas = [(b["hits_" + level] - a["hits_" + level]) / a["changed_files"] for a, b in pairs]
        metrics[level] = {
            "mean_recall_before": statistics.mean(a["hits_" + level] / a["changed_files"] for a, _ in pairs) if pairs else None,
            "mean_recall_after": statistics.mean(b["hits_" + level] / b["changed_files"] for _, b in pairs) if pairs else None,
            "hits_before": sum(a["hits_" + level] for a, _ in pairs),
            "hits_after": sum(b["hits_" + level] for _, b in pairs), "gold_files": gold,
            "micro_recall_before": sum(a["hits_" + level] for a, _ in pairs) / gold if gold else None,
            "micro_recall_after": sum(b["hits_" + level] for _, b in pairs) / gold if gold else None,
            "wins": sum(x > 0 for x in deltas), "ties": sum(x == 0 for x in deltas), "losses": sum(x < 0 for x in deltas)}
    scans = {}
    for label, index in (("before", 0), ("after", 1)):
        rows = [pair[index] for pair in pairs]
        cutoffs = Counter(c for row in rows for c in set(row["cutoffs"]))
        exclusions = Counter()
        for row in rows:
            exclusions.update(row["exclusions"])
        scans[label] = {"cutoff_case_counts": dict(sorted(cutoffs.items())), "exclusion_counts": dict(sorted(exclusions.items())),
                        "median_case_seconds": statistics.median(row["seconds"] for row in rows) if rows else None}
    return {"kind": "paired_external_recall_comparison", "selected_cases": len(old), "paired_scored_cases": len(pairs),
            "excluded_pairs": excluded, "limits": before["limits"],
            "source_identity_before": before["source_identity"], "source_identity_after": after["source_identity"],
            "cases_sha256": before["cases_sha256"], "selection_sha256": before["selection_sha256"],
            "case_root_locations_sha256": before["case_root_locations_sha256"],
            "python": before["python"], "platform": before["platform"], "timing_scope": before["timing_scope"],
            "metrics": metrics, "scans": scans, "corpus_immutability_established": False, "warning": WARNING}


def _read(path):
    with path.open("rb") as handle:
        raw = handle.read(MAX_RECEIPT_BYTES + 1)
    _require(len(raw) <= MAX_RECEIPT_BYTES, "receipt_byte_budget")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)
    output = args.output.resolve()
    repository = Path(__file__).resolve().parents[1]
    _require(output != repository and repository not in output.parents, "comparison_output_inside_checkout")
    _require(not args.output.exists() and not args.output.is_symlink(), "comparison_output_exists")
    before, old_hash = _read(args.before)
    after, new_hash = _read(args.after)
    result = compare(before, after)
    result.update({"before_receipt_sha256": old_hash, "after_receipt_sha256": new_hash,
                   "comparison_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"paired_scored_cases": result["paired_scored_cases"], "excluded_pairs": len(result["excluded_pairs"]),
                      "primary": result["metrics"]["primary"], "with_map": result["metrics"]["with_map"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()

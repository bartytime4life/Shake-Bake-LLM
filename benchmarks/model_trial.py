"""Reproducible local development trials and separately reviewed accuracy.

No policy promotion or cloud client. Each finished attempt is checkpointed.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import sys
import time
import uuid

import run_task_lab as lab
from shake_bake import __version__
from shake_bake.capabilities import computer_snapshot
from shake_bake.contracts import Refusal
from shake_bake.doctor import inspect_model
from shake_bake.routing import pipeline_id
from shake_bake.worker import worker_configuration, parse_json

REVIEW_FIELDS = ("supported_handoff", "critical_misses", "unsupported_claims", "unsupported_critical_claims", "useful_abstention")


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, value):
    with path.open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def review_sheet(receipt_bytes, attempts):
    return {"schema_version": "1", "trial_sha256": sha(receipt_bytes), "reviewer": "",
            "warning": "Review against grading-keys.json outside fixture roots. Split labels are owner-declared; this handoff review alone cannot qualify an auto-picked model.",
            "entries": [{"attempt_id": a["attempt_id"], "case_id": a["id"],
                         **{field: None for field in REVIEW_FIELDS}, "notes": ""} for a in attempts]}


def run_trial(output_dir, *, model=None, evidence_only=False, port=11434, repeats=1, case_ids=None, seed=0, dataset=None):
    if (model is None) == (not evidence_only):
        raise Refusal("choose_model_or_evidence_only")
    if type(repeats) is not int or not 1 <= repeats <= 3:
        raise Refusal("trial_repeat_limit")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise Refusal("invalid_trial_seed")
    dataset_root, cases, _, identity = lab.load_dataset(dataset)
    available = {case["id"] for case in cases}
    selected = sorted(available if case_ids is None else case_ids)
    if not selected or len(set(selected)) != len(selected) or set(selected) - available:
        raise Refusal("invalid_trial_cases")
    output_dir = Path(output_dir).resolve()
    protected = dataset_root
    if output_dir == protected or protected in output_dir.parents:
        raise Refusal("trial_output_inside_dataset")
    # Refuse to overwrite previous runs, even if the directory is empty.
    output_dir.mkdir(parents=True, exist_ok=False)
    plan = [{"attempt_id": f"{round_number}:{case_id}", "round": round_number, "case_id": case_id}
            for round_number in range(1, repeats + 1) for case_id in selected]
    random.Random(seed).shuffle(plan)
    fixture_hashes = {case_id: lab.tree_hash(dataset_root / "fixtures" / case_id) for case_id in selected}
    started = time.monotonic()
    receipt = {"schema_version": "1", "kind": "external_dataset_model_trial" if dataset is not None else "exposed_development_model_trial", "trial_id": str(uuid.uuid4()),
               "created_utc": datetime.now(timezone.utc).isoformat(), "helper_version": __version__,
               "pipeline_id": pipeline_id(), "trial_runner_sha256": sha(Path(__file__).read_bytes()),
               "task_runner_sha256": sha(Path(lab.__file__).read_bytes()),
               "dataset": identity,
               "manifest_sha256": identity["manifest_sha256"],
               "grading_keys_sha256": identity["grading_keys_sha256"],
               "fixture_sha256": fixture_hashes, "unique_case_count": len(selected), "repeats": repeats,
               "planned_attempts": plan, "order_seed": seed,
               "mode": "evidence_only" if evidence_only else "local_model_candidate",
               "requested_model": model, "model_preflight": None,
               "environment": {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version(),
                               "model_load_state": "uncontrolled", "gpu_throughput": None, "computer": computer_snapshot()},
               "requested_worker_settings": worker_configuration(),
               "attempts": [], "status": "RUNNING", "stop_reason": None,
               "semantic_model_accuracy": None, "cloud_usage_measured": False, "native_host_baseline": None,
               "auto_promotion_allowed": False,
               "warning": "The bundled lab is exposed development data; external split labels are owner-declared. No paired native-host qualification. Repetitions are not independent cases. Missing usage is unknown, not zero. No cold-start or GPU-speed claim."}
    write_new(output_dir / "plan.json", receipt)
    try:
        if model:
            receipt["model_preflight"] = inspect_model(model, port)
        digest = (receipt["model_preflight"] or {}).get("reported_digest")
        with (output_dir / "attempts.jsonl").open("xb") as checkpoint:
            for item in plan:
                case_id = item["case_id"]
                if lab.tree_hash(dataset_root / "fixtures" / case_id) != fixture_hashes[case_id]:
                    receipt["stop_reason"] = "fixture_changed"
                    break
                if (pipeline_id() != receipt["pipeline_id"] or
                    lab.load_dataset(dataset)[3] != identity):
                    receipt["stop_reason"] = "trial_inputs_changed"
                    break
                result = lab.run_cases(model=model, port=port, case_ids=[case_id], expected_digest=digest,
                    expected_runtime=(receipt["model_preflight"] or {}).get("runtime_version"),
                    **({"dataset": dataset} if dataset is not None else {}))
                attempt = {**result["cases"][0], "attempt_id": item["attempt_id"], "round": item["round"]}
                attempt["fixture_matches_trial_start"] = attempt["fixture_sha256"] == fixture_hashes[case_id]
                receipt["attempts"].append(attempt)
                checkpoint.write(json.dumps(attempt, ensure_ascii=False, allow_nan=False).encode() + b"\n")
                checkpoint.flush(); os.fsync(checkpoint.fileno())
                error = attempt["error"] or (attempt["brief"] or {}).get("worker_error")
                if not attempt["dataset_unchanged"] or result["dataset"] != identity or not lab.dataset_matches(dataset_root, identity):
                    receipt["stop_reason"] = "trial_inputs_changed"
                    break
                if not attempt["fixture_unchanged"] or not attempt["fixture_matches_trial_start"]:
                    receipt["stop_reason"] = "fixture_changed"
                    break
                if error in ("qualified_model_digest_changed", "local_model_metadata_required", "worker_model_mismatch", "remote_worker_response_refused",
                             "worker_timeout", "worker_transport_failed", "worker_runtime_changed", "invalid_local_runtime"):
                    receipt["stop_reason"] = error
                    break
        receipt["status"] = "STOPPED" if receipt["stop_reason"] else "FINISHED"
    except Refusal as error:
        receipt["status"], receipt["stop_reason"] = "BLOCKED", error.code
    except KeyboardInterrupt:
        receipt["status"], receipt["stop_reason"] = "INTERRUPTED", "user_interrupt"
    except Exception:
        receipt["status"], receipt["stop_reason"] = "ERROR", "trial_failed"
    receipt["elapsed_seconds"] = round(time.monotonic() - started, 6)
    receipt["completed_attempt_count"] = len(receipt["attempts"])
    receipt["failed_attempt_count"] = sum(bool(a["error"] or (a["brief"] or {}).get("worker_error") or
        not a["coverage"].get("mechanical_pass") or not a["fixture_unchanged"] or not a["fixture_matches_trial_start"] or not a.get("dataset_unchanged", True))
        for a in receipt["attempts"])
    receipt_bytes = encoded(receipt)
    write_new(output_dir / "trial.json", receipt)
    write_new(output_dir / "reviews.json", review_sheet(receipt_bytes, receipt["attempts"]))
    return receipt


def score(receipt_bytes, reviews):
    receipt = parse_json(receipt_bytes.decode())
    if not isinstance(receipt, dict) or receipt.get("kind") not in ("exposed_development_model_trial", "external_dataset_model_trial"):
        raise Refusal("invalid_trial_receipt")
    if not isinstance(reviews, dict) or reviews.get("schema_version") != "1" or reviews.get("trial_sha256") != sha(receipt_bytes):
        raise Refusal("review_receipt_mismatch")
    attempts, entries = receipt["attempts"], reviews.get("entries")
    if not isinstance(entries, list) or len(entries) != len(attempts):
        raise Refusal("incomplete_review_entries")
    by_id = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("attempt_id"), str) or entry["attempt_id"] in by_id:
            raise Refusal("invalid_review_entries")
        by_id[entry["attempt_id"]] = entry
    if set(by_id) != {attempt["attempt_id"] for attempt in attempts}:
        raise Refusal("review_attempt_mismatch")
    reviewed, correct, critical, unsupported, unsupported_critical = 0, 0, 0, 0, 0
    failure_reasons = {}
    mechanical = 0
    known_usage, missing_usage, usage_sums = 0, 0, {}
    for attempt in attempts:
        entry = by_id[attempt["attempt_id"]]
        if entry.get("case_id") != attempt["id"]:
            raise Refusal("review_case_mismatch")
        good_evidence = bool(attempt["coverage"].get("mechanical_pass") and attempt["fixture_unchanged"] and attempt["fixture_matches_trial_start"] and attempt.get("dataset_unchanged", True))
        mechanical += good_evidence
        worker = (attempt["brief"] or {}).get("worker")
        error = attempt["error"] or (attempt["brief"] or {}).get("worker_error")
        if error:
            failure_reasons[error] = failure_reasons.get(error, 0) + 1
        if not good_evidence:
            failure_reasons["evidence_check_failed"] = failure_reasons.get("evidence_check_failed", 0) + 1
        usage = (worker or {}).get("usage", {})
        if usage:
            known_usage += 1
            for key, value in usage.items():
                usage_sums[key] = usage_sums.get(key, 0) + value
        else:
            missing_usage += 1
        for field in REVIEW_FIELDS:
            value = entry.get(field)
            if value is None:
                continue
            if field in ("supported_handoff", "useful_abstention"):
                if type(value) is not bool:
                    raise Refusal("invalid_review_value")
            elif type(value) is not int or not 0 <= value <= 100000:
                raise Refusal("invalid_review_value")
        if any(entry.get(field) is None for field in REVIEW_FIELDS):
            continue
        if not isinstance(entry.get("notes"), str) or not entry["notes"].strip():
            raise Refusal("review_requires_evidence_notes")
        if entry["unsupported_critical_claims"] > entry["unsupported_claims"]:
            raise Refusal("inconsistent_review_counts")
        model_ok = receipt["mode"] == "evidence_only" or (worker is not None and not attempt["error"] and not (attempt["brief"] or {}).get("worker_error"))
        if entry["supported_handoff"] and not (good_evidence and model_ok):
            raise Refusal("failed_attempt_cannot_be_correct")
        if entry["supported_handoff"] and (entry["critical_misses"] or entry["unsupported_claims"]):
            raise Refusal("inconsistent_supported_handoff")
        reviewed += 1
        correct += bool(entry["supported_handoff"] and good_evidence and model_ok)
        critical += entry["critical_misses"]
        unsupported += entry["unsupported_claims"]
        unsupported_critical += entry["unsupported_critical_claims"]
    complete = receipt["status"] == "FINISHED" and len(attempts) == len(receipt["planned_attempts"])
    fully_reviewed = complete and bool(attempts) and reviewed == len(attempts)
    if fully_reviewed and (not isinstance(reviews.get("reviewer"), str) or not reviews["reviewer"].strip()):
        raise Refusal("reviewer_required")
    return {"kind": "external_dataset_trial_review" if receipt["kind"] == "external_dataset_model_trial" else "development_trial_review", "trial_sha256": sha(receipt_bytes),
            "dataset": receipt.get("dataset"),
            "trial_status": receipt["status"], "completed_attempts": len(attempts), "planned_attempts": len(receipt["planned_attempts"]),
            "unique_cases": receipt["unique_case_count"], "mechanical_passes": mechanical,
            "failure_reasons": failure_reasons,
            "reviewed_attempts": reviewed, "review_status": "REVIEWED" if fully_reviewed else "PENDING",
            "reviewer_record_is_self_asserted": True,
            "reviewed_handoff_accuracy": correct / len(attempts) if fully_reviewed else None,
            "semantic_model_accuracy": correct / len(attempts) if fully_reviewed and receipt["mode"] != "evidence_only" else None,
            "critical_misses": critical if fully_reviewed else None,
            "unsupported_claims": unsupported if fully_reviewed else None,
            "unsupported_critical_claims": unsupported_critical if fully_reviewed else None,
            "usage": {"scope": "successful_validated_worker_responses_only", "reported_sums": usage_sums,
                      "attempts_with_any_usage": known_usage, "attempts_without_usage": missing_usage,
                      "full_task_total_known": False,
                      "warning": "Missing or rejected-response usage is unknown; sums can undercount failed work."},
            "cloud_savings": None, "auto_promotion_allowed": False,
            "warning": "Local handoff review only; split labels are owner-declared. No native-host comparison, independent-case confidence interval or auto-routing qualification."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    mode = run.add_mutually_exclusive_group(required=True)
    mode.add_argument("--model")
    mode.add_argument("--evidence-only", action="store_true")
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--ollama-port", type=int, default=11434)
    run.add_argument("--repeat", type=int, default=1, dest="repeats")
    run.add_argument("--case", action="append", dest="case_ids")
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--dataset", type=Path, help="Owner-selected external dataset; never auto-promotes a profile")
    review = commands.add_parser("score")
    review.add_argument("--trial", required=True, type=Path)
    review.add_argument("--reviews", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            result = run_trial(args.output, model=args.model, evidence_only=args.evidence_only, port=args.ollama_port,
                               repeats=args.repeats, case_ids=args.case_ids, seed=args.seed, dataset=args.dataset)
            print(json.dumps({key: result[key] for key in ("status", "stop_reason", "completed_attempt_count", "failed_attempt_count", "semantic_model_accuracy", "auto_promotion_allowed")}))
            return 0 if result["status"] == "FINISHED" else 1
        result = score(args.trial.read_bytes(), parse_json(args.reviews.read_text()))
        print(json.dumps(result, indent=2))
        return 0 if result["review_status"] == "REVIEWED" else 3
    except (Refusal, OSError, UnicodeError) as error:
        print(json.dumps({"outcome": "DENY", "code": error.code if isinstance(error, Refusal) else "trial_file_error"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

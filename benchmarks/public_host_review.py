"""Offline, receipt-bound review of the public change-review host runner.

Reads only the selected private receipt, derived answer files and review sheet.
Does not run a host, inspect fixture source, grade answers or promote a route.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat


MAX_DOCUMENT = 16 * 1024 * 1024
MAX_ANSWER = 1024 * 1024
MAX_ATTEMPTS = 1000
STATES = {"PREFLIGHT", "PREFLIGHT_FAILED", "RUNNING", "INPUT_DRIFT",
          "STOPPED_AFTER_ATTEMPT_FAILURE", "FINISHED_UNGRADED"}
COUNTERS = ("input_tokens", "cached_input_tokens", "output_tokens")
JUDGMENTS = ("reference_matches", "unsupported_claims", "critical_misses", "supported_outcome")
IDENTIFIER = re.compile(r"[a-z][a-z0-9_-]{0,79}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def refuse(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_file(path, limit=MAX_DOCUMENT, *, dir_fd=None):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    try:
        info = os.fstat(descriptor)
        refuse(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "regular_single_link_input_required")
        refuse(info.st_size <= limit, "input_budget_exceeded")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        refuse(len(data) <= limit, "input_budget_exceeded")
        return data
    finally:
        os.close(descriptor)


def document(data):
    def pairs(items):
        result = {}
        for key, value in items:
            refuse(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("nonfinite_json_value")

    result = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    refuse(isinstance(result, dict), "json_object_required")
    return result


def number(value):
    return (type(value) is int and 0 <= value <= 10**12 or
            type(value) is float and math.isfinite(value) and 0 <= value <= 10**12)


def identity(row):
    refuse(isinstance(row, dict), "invalid_attempt_identity")
    case, arm, round_number = row.get("case_id"), row.get("arm"), row.get("round")
    refuse(isinstance(case, str) and IDENTIFIER.fullmatch(case), "invalid_case_id")
    refuse(arm in ("native", "prepared") and type(round_number) is int and 1 <= round_number <= 1000,
           "invalid_attempt_identity")
    expected = f"{round_number}:{case}:{arm}"
    refuse(row.get("attempt_id") == expected, "invalid_attempt_id")
    return expected


def binding(receipt_bytes, attempt_id):
    # An opaque receipt/attempt identity, not authentication or proof of masking.
    return sha(receipt_bytes + b"\0" + attempt_id.encode("utf-8"))


def load_trial(receipt_path):
    receipt_path = Path(receipt_path)
    receipt_bytes = read_file(receipt_path)
    receipt = document(receipt_bytes)
    refuse(receipt.get("kind") == "public_change_review_development_trial", "unsupported_receipt_kind")
    refuse(isinstance(receipt.get("status"), str) and receipt["status"] in STATES, "invalid_trial_status")
    plan, attempts = receipt.get("attempt_plan"), receipt.get("attempts")
    refuse(isinstance(plan, list) and 1 <= len(plan) <= MAX_ATTEMPTS, "invalid_attempt_plan")
    planned = [identity(row) for row in plan]
    refuse(len(set(planned)) == len(planned), "duplicate_planned_attempt")
    refuse(isinstance(attempts, list) and len(attempts) <= len(plan), "invalid_attempts")
    answers, answer_bytes = {}, 0
    parent = os.open(receipt_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, attempt in enumerate(attempts, 1):
            refuse(identity(attempt) == planned[index - 1] and type(attempt.get("index")) is int
                   and attempt["index"] == index, "attempt_plan_mismatch")
            digest = attempt.get("answer_sha256")
            refuse(digest is None or isinstance(digest, str) and DIGEST.fullmatch(digest), "invalid_answer_hash")
            if digest is not None:
                folder = f"{index:02d}-{attempt['case_id']}-{attempt['arm']}"
                folder_fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                try:
                    raw = read_file("answer.md", MAX_ANSWER, dir_fd=folder_fd)
                finally:
                    os.close(folder_fd)
                answer_bytes += len(raw)
                refuse(answer_bytes <= MAX_DOCUMENT, "answer_budget_exceeded")
                refuse(sha(raw) == digest, "answer_identity_mismatch")
                answers[attempt["attempt_id"]] = raw.decode("utf-8")
            else:
                answers[attempt["attempt_id"]] = None
            for field in ("host_seconds", "preparation_seconds"):
                refuse(field not in attempt or number(attempt[field]), "invalid_attempt_timing")
            for field in ("error", "audit_error"):
                refuse(attempt.get(field) is None or isinstance(attempt[field], str), "invalid_attempt_error")
            refuse("exit_code" not in attempt or type(attempt["exit_code"]) is int, "invalid_attempt_exit")
            refuse("fixture_unchanged" not in attempt or type(attempt["fixture_unchanged"]) is bool,
                   "invalid_fixture_status")
            usage = attempt.get("usage")
            refuse(usage is None or isinstance(usage, dict), "invalid_usage")
            for value in (usage or {}).values():
                refuse(type(value) is int and value >= 0, "invalid_usage")
            if usage and "cached_input_tokens" in usage and "input_tokens" in usage:
                refuse(usage["cached_input_tokens"] <= usage["input_tokens"], "invalid_cached_usage")
    finally:
        os.close(parent)
    return receipt_bytes, receipt, answers


def failure_reasons(attempt):
    reasons = []
    if attempt.get("exit_code") != 0:
        reasons.append("host_not_successful")
    for field in ("error", "audit_error"):
        if attempt.get(field):
            reasons.append(field)
    if not attempt.get("answer_sha256"):
        reasons.append("answer_not_recorded")
    if attempt.get("fixture_unchanged") is not True:
        reasons.append("source_identity_not_confirmed")
    if "host_seconds" not in attempt:
        reasons.append("host_timing_missing")
    return reasons


def prepare(receipt_path):
    raw, receipt, answers = load_trial(receipt_path)
    entries = []
    for index, attempt in enumerate(receipt["attempts"], 1):
        entries.append({"review_label": f"R{index:02d}", "case_id": attempt["case_id"],
                        "round": attempt["round"], "answer_sha256": attempt.get("answer_sha256"),
                        "review_binding": binding(raw, attempt["attempt_id"]),
                        "answer": answers[attempt["attempt_id"]],
                        **{field: None for field in JUDGMENTS}, "review_notes": ""})
    return {"receipt_sha256": sha(raw), "reviewer": "", "reviewer_kind": "", "entries": entries,
            "warning": "Review against pinned source/references. Labels do not prove blindness; identity and reviewer kind are self-declared. No qualification or promotion."}


def score(receipt_path, review_path):
    receipt_raw, receipt, answers = load_trial(receipt_path)
    review_raw = read_file(review_path)
    review = document(review_raw)
    refuse(review.get("receipt_sha256") == sha(receipt_raw), "review_receipt_mismatch")
    entries = review.get("entries")
    refuse(isinstance(entries, list) and len(entries) == len(receipt["attempts"]), "incomplete_review_entries")
    by_id, labels, legacy, bound = {}, set(), {}, {}
    for attempt in receipt["attempts"]:
        key = (attempt["case_id"], attempt["round"], attempt.get("answer_sha256"))
        legacy.setdefault(key, []).append(attempt["attempt_id"])
        bound[binding(receipt_raw, attempt["attempt_id"])] = (attempt["attempt_id"], key)
    for entry in entries:
        refuse(isinstance(entry, dict), "invalid_review_entry")
        label = entry.get("review_label")
        refuse(isinstance(label, str) and re.fullmatch(r"R[0-9]{2,4}", label) and label not in labels,
               "duplicate_or_invalid_review_label")
        labels.add(label)
        refuse(isinstance(entry.get("case_id"), str) and type(entry.get("round")) is int
               and (entry.get("answer_sha256") is None or isinstance(entry["answer_sha256"], str)),
               "invalid_review_identity")
        key = (entry["case_id"], entry["round"], entry.get("answer_sha256"))
        if "review_binding" in entry:
            token = entry["review_binding"]
            refuse(isinstance(token, str) and token in bound, "review_binding_mismatch")
            attempt_id, expected_key = bound[token]
            refuse(key == expected_key, "review_attempt_mismatch")
        else:
            refuse(key in legacy, "review_attempt_mismatch")
            refuse(len(legacy[key]) == 1, "ambiguous_review_identity")
            attempt_id = legacy[key][0]
        refuse(attempt_id not in by_id, "review_attempt_mismatch")
        refuse(entry.get("answer") == answers[attempt_id], "review_answer_mismatch")
        for field in ("unsupported_claims", "critical_misses"):
            value = entry.get(field)
            refuse(value is None or type(value) is int and 0 <= value <= 100000, "invalid_review_count")
        value = entry.get("supported_outcome")
        refuse(value is None or type(value) is bool, "invalid_supported_outcome")
        matches = entry.get("reference_matches")
        refuse(matches is None or isinstance(matches, list) and all(type(v) is int and v > 0 for v in matches)
               and len(matches) == len(set(matches)), "invalid_reference_matches")
        refuse(isinstance(entry.get("review_notes"), str), "invalid_review_notes")
        if all(entry.get(field) is not None for field in JUDGMENTS):
            refuse(bool(entry["review_notes"].strip()), "review_evidence_notes_required")
            refuse(not entry["supported_outcome"] or not (entry["unsupported_claims"] or entry["critical_misses"]),
                   "inconsistent_supported_outcome")
        by_id[attempt_id] = entry
    refuse(set(by_id) == set(answers), "review_attempt_mismatch")
    reviewer, reviewer_kind = review.get("reviewer"), review.get("reviewer_kind", "")
    refuse(isinstance(reviewer, str) and isinstance(reviewer_kind, str), "invalid_reviewer")
    refuse(reviewer_kind in ("", "human", "ai"), "invalid_reviewer_kind")
    arm_totals, details = {}, []
    for arm in ("native", "prepared"):
        planned = sum(row["arm"] == arm for row in receipt["attempt_plan"])
        arm_totals[arm] = {"planned_attempts": planned, "started_attempts": 0, "completed_attempts": 0,
                           "reviewed_attempts": 0, "supported_outcomes": 0, "critical_misses": 0,
                           "unsupported_claims": 0, "reported_usage_sums": {key: 0 for key in COUNTERS},
                           "usage_missing_attempts": {key: 0 for key in COUNTERS},
                           "reported_host_seconds_sum": 0, "reported_preparation_seconds_sum": 0,
                           "timing_missing_attempts": 0}
    for attempt in receipt["attempts"]:
        entry, totals = by_id[attempt["attempt_id"]], arm_totals[attempt["arm"]]
        reasons = failure_reasons(attempt)
        reviewed = all(entry.get(field) is not None for field in JUDGMENTS)
        refuse(not entry.get("supported_outcome") or not reasons, "failed_attempt_cannot_be_supported")
        totals["started_attempts"] += 1
        totals["completed_attempts"] += not reasons
        totals["reviewed_attempts"] += reviewed
        if reviewed:
            totals["supported_outcomes"] += entry["supported_outcome"]
            for field in ("critical_misses", "unsupported_claims"):
                totals[field] += entry[field]
        for field in COUNTERS:
            usage = attempt.get("usage") or {}
            if field in usage:
                totals["reported_usage_sums"][field] += usage[field]
            else:
                totals["usage_missing_attempts"][field] += 1
        for field in ("host_seconds", "preparation_seconds"):
            if field in attempt:
                totals[f"reported_{field}_sum"] += attempt[field]
        totals["timing_missing_attempts"] += any(field not in attempt for field in ("host_seconds", "preparation_seconds"))
        details.append({"attempt_id": attempt["attempt_id"], "completed": not reasons,
                        "failure_reasons": reasons, "reviewed": reviewed,
                        "supported_outcome": entry["supported_outcome"] if reviewed else None})
    fully_reviewed = bool(details) and all(row["reviewed"] for row in details)
    if fully_reviewed:
        refuse(bool(reviewer.strip()), "reviewer_required")
        refuse(reviewer_kind in ("human", "ai"), "reviewer_kind_required")
    complete = (receipt["status"] == "FINISHED_UNGRADED" and len(details) == len(receipt["attempt_plan"])
                and all(row["completed"] for row in details))
    for totals in arm_totals.values():
        totals["unstarted_attempts"] = totals["planned_attempts"] - totals["started_attempts"]
        totals["supported_outcomes_per_planned_attempt"] = (totals["supported_outcomes"] / totals["planned_attempts"]
            if fully_reviewed and complete and totals["planned_attempts"] else None)
        if totals["reviewed_attempts"] != totals["started_attempts"] or not totals["started_attempts"]:
            for field in ("supported_outcomes", "critical_misses", "unsupported_claims"):
                totals[field] = None
    return {"kind": "public_change_review_host_review", "receipt_sha256": sha(receipt_raw),
            "reviews_sha256": sha(review_raw), "trial_status": receipt["status"], "trial_complete": complete,
            "planned_attempts": len(receipt["attempt_plan"]), "started_attempts": len(details),
            "review_status": "REVIEWED" if fully_reviewed else "PENDING", "reviewer": reviewer,
            "reviewer_kind": reviewer_kind or None, "reviewer_identity_is_self_declared": True,
            "arm_totals": arm_totals, "attempts": details, "auto_promotion_allowed": False,
            "cloud_savings": None, "independent_human_qualification": None,
            "limits": ["Counts are reviewer declarations, not machine-verified answer correctness.",
                       "Public cases are exposed development material; repetitions are not independent cases.",
                       "Input includes its cached subset. Missing usage is unknown; sums include recorded failed attempts.",
                       "Preflights, prior runs, correction work, billing and whole-task benefit are not measured here.",
                       "Receipt and answer hashes bind selected local bytes; they do not authenticate their author or host execution."]}


def write_new(path, value):
    # Review sheets contain answers; keep both sheets and reports outside checkout.
    path = Path(path).absolute()
    resolved = path.resolve()
    source = Path(__file__).resolve().parents[1]
    refuse(resolved != source and source not in resolved.parents, "review_output_in_checkout")
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "score"):
        command = commands.add_parser(name)
        command.add_argument("--receipt", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "score":
            command.add_argument("--reviews", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare(args.receipt) if args.command == "prepare" else score(args.receipt, args.reviews)
        write_new(args.output, result)
    except (ValueError, TypeError, OSError, UnicodeError, RecursionError) as error:
        parser.exit(2, f"Review refused: {error}\n")
    print("Review sheet saved." if args.command == "prepare" else f"Review report saved: {result['review_status']}.")


if __name__ == "__main__":
    main()

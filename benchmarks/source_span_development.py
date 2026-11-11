"""Generate and audit six exposed synthetic source-selection development cases.

Use run_task_lab.py --evidence-only to collect each arm. This standard-library
tool neither imports a collector nor invokes a model or executes fixture source.
It checks these fixed cases, not arbitrary datasets or semantic answer quality.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path


DATASET_ID = "source-span-development-20261111-v1"
# Explicit common profile: no dependence on changing collector defaults.
LIMITS = {"max_files": 1000, "max_entries": 10000, "max_depth": 8,
          "seconds": 5.0, "excerpt_bytes": 16384, "context_bytes": 2048}
MAX_RECEIPT_BYTES = 16 * 1024 * 1024
WARNING = ("Exposed, authored synthetic development cases tailored to known mechanisms. "
           "Span/file coverage is not semantic accuracy, unseen qualification or workflow savings. "
           "Collector revision and execution provenance must be recorded separately.")


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _cases():
    """Keys live outside fixture roots; generated source is inert inspection data."""
    clustered = ["# filler\n"] * 50
    for index in (0, 20, 40, 41, 42, 43, 44):
        clustered[index] = f"# policy marker_{index + 1:02d}\n"
    worker = ["# filler\n"] * 100
    worker[:4] = ["def cancel_task(worker, job):\n", "    if worker.busy:\n",
                  "        return False\n", "    return True\n"]
    for index in (*range(40, 45), *range(80, 85)):
        worker[index] = "# cancel_task worker job audit comment\n"
    return [
        ("clustered-policy", "Inspect policy", {"policy.py": "".join(clustered)},
         [("policy.py", f"# policy marker_{line:02d}\n") for line in (1, 41, 42, 43, 44, 45)], []),
        ("overlapping-policy", "Inspect policy",
         {"policy.py": "# policy α\r\n" + "# filler\r\n" * 3 + "# policy β\r\n" + "# filler\r\n" * 3},
         [("policy.py", "# policy α\r\n"), ("policy.py", "# policy β\r\n")], []),
        ("large-neighbor", "Inspect bounded_policy",
         {"rules.py": "# padding " + "x" * 20000 + "\ndef bounded_policy(value):\n    return value <= 7\n"},
         [("rules.py", "def bounded_policy(value):\n    return value <= 7\n")], ["excerpt_budget"]),
        ("four-file-guard", "Inspect cancel_task worker job",
         {"a_worker.py": "".join(worker),
          **{name: f"# cancel_task worker job {marker}\n" for name, marker in
             (("b_api.py", "api_anchor"), ("c_queue.py", "queue_anchor"), ("d_route.py", "route_anchor"))}},
         [("a_worker.py", "    if worker.busy:\n        return False\n"),
          ("b_api.py", "api_anchor"), ("c_queue.py", "queue_anchor"), ("d_route.py", "route_anchor")], []),
        ("oversized-anchor", "Inspect policy_guard guard",
         {"rules.py": "# policy_guard guard " + "x" * 20000 + "\n# guard\n"},
         [("rules.py", "# policy_guard guard ")], ["excerpt_budget"]),
        ("definition-control", "Inspect publish_job",
         {"main.py": "def publish_job(payload):\n    return read_config(payload)\n",
          "settings.py": "def read_config(payload):\n    return {'accepted': payload}\n",
          "queue.py": "def enqueue(payload):\n    return publish_job(payload)\n",
          "tests/test_publish_job.py": "def test_publish_job():\n    assert publish_job('sample') == {'accepted': 'sample'}\n"},
         [("main.py", "return read_config(payload)"), ("settings.py", "def read_config(payload):"),
          ("queue.py", "return publish_job(payload)"), ("tests/test_publish_job.py", "assert publish_job('sample')")], []),
    ]


def documents():
    """Location-independent bytes, including exact tasks, budgets and grading keys."""
    cases, keys, files = [], {}, {}
    for identifier, task, sources, anchors, cutoffs in _cases():
        cases.append({"id": identifier, "task": task, "limits": dict(LIMITS)})
        keys[identifier] = {"anchors": [{"path": path, "contains": text} for path, text in anchors],
                            "required_cutoffs": cutoffs}
        for name, text in sources.items():
            files[f"fixtures/{identifier}/{name}"] = text.encode("utf-8")
    files["manifest.json"] = encoded({"schema_version": "1", "dataset_id": DATASET_ID,
                                      "split": "development", "warning": WARNING, "cases": cases})
    files["grading-keys.json"] = encoded({"schema_version": "1", "never_send_to_worker": True, "cases": keys})
    return files


def identities(files):
    return {name: sha(data) for name, data in sorted(files.items())}


def generate(destination):
    destination = Path(destination)
    resolved = destination.resolve()
    repository = Path(__file__).resolve().parents[1]
    if resolved == repository or repository in resolved.parents:
        raise ValueError("dataset_output_inside_checkout")
    # Refuse existing directories and dangling links; never rewrite a prior run.
    if destination.exists() or destination.is_symlink():
        raise ValueError("dataset_output_exists")
    files = documents()
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in sorted(files.items()):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    return identities(files)


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _dataset_files(root):
    root = Path(root)
    _require(root.is_dir() and not root.is_symlink(), "invalid_dataset_root")
    expected = documents()
    directories = {parent.as_posix() for name in expected for parent in Path(name).parents if parent != Path(".")}
    files = {}
    for path in root.rglob("*"):
        name = path.relative_to(root).as_posix()
        _require(not path.is_symlink(), "dataset_link_refused")
        if path.is_dir():
            _require(name in directories, "development_dataset_changed")
            continue
        _require(path.is_file() and path.stat().st_nlink == 1, "dataset_special_file_refused")
        _require(name in expected and path.stat().st_size == len(expected[name]), "development_dataset_changed")
        files[name] = path.read_bytes()
    _require(files == expected, "development_dataset_changed")
    return files


def _fixture_hash(root):
    # Independent readback of the Task Lab's path-NUL-bytes-NUL fixture identity.
    digest = hashlib.sha256()
    for directory, directories, names in os.walk(root):
        directories.sort()
        for name in sorted(names):
            path = Path(directory) / name
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def audit(dataset, receipt):
    """Recompute counts from exact packet text, never from claimed coverage totals.

    A required span must be contained in ONE exact excerpt of its declared file.
    File hits count distinct required paths, even when their required spans are
    missing. Duplicate lines count occurrences beyond the first (path, line).
    Missing spans, including the oversized-line control, stay in the denominator.
    """
    files = _dataset_files(dataset)
    manifest = json.loads(files["manifest.json"])
    keys = json.loads(files["grading-keys.json"])["cases"]
    identity = {"dataset_id": DATASET_ID, "split": "development", "split_is_owner_declared": True,
                "manifest_sha256": sha(files["manifest.json"]), "grading_keys_sha256": sha(files["grading-keys.json"])}
    _require(receipt.get("dataset") == identity, "receipt_dataset_mismatch")
    _require(receipt.get("mode") == "evidence_only_diagnostic" and receipt.get("model") is None
             and receipt.get("rerank_model") is None and receipt.get("actual_model_calls_requested") is False
             and receipt.get("semantic_model_accuracy") is None and receipt.get("worker_errors") == 0,
             "receipt_requires_model_free_completion")
    rows = receipt.get("cases", [])
    _require([row["id"] for row in rows] == [case["id"] for case in manifest["cases"]]
             and receipt.get("case_count") == len(rows), "receipt_case_selection_mismatch")
    results = []
    for case, row in zip(manifest["cases"], rows):
        identifier = case["id"]
        _require(row.get("task") == case["task"] and row.get("error") is None
                 and row.get("fixture_unchanged") is True and row.get("dataset_unchanged") is True
                 and row.get("fixture_sha256") == _fixture_hash(Path(dataset) / "fixtures" / identifier),
                 "receipt_case_inputs_mismatch")
        brief = row["brief"]
        search = brief["search"]
        _require(brief.get("worker") is None and brief.get("worker_error") is None
                 and search.get("rerank") is None and search["original_request"] == case["task"],
                 "receipt_case_mode_mismatch")
        _require(not {"time_budget", "file_budget", "entry_budget", "depth_budget"} & set(search["cutoffs"]),
                 "development_scan_incomplete")
        packet = search["packet"]
        records = packet["evidence"] if packet else []
        if packet:
            _require(packet["original_request"] == case["task"], "receipt_request_mismatch")
        occurrences, byte_count = [], 0
        for record in records:
            source = files.get(f"fixtures/{identifier}/{record['path']}")
            _require(source is not None, "receipt_source_path_mismatch")
            lines = source.splitlines(keepends=True)
            start, end = record["start_line"], record["end_line"]
            _require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines), "receipt_range_invalid")
            exact = b"".join(lines[start - 1:end])
            _require(record["text"].encode("utf-8") == exact and record["file_sha256"] == sha(source)
                     and record["excerpt_sha256"] == sha(exact) and record["size_bytes"] == len(source),
                     "receipt_source_integrity_mismatch")
            byte_count += len(exact)
            occurrences.extend((record["path"], line) for line in range(start, end + 1))
        _require(byte_count == search["selected_excerpt_bytes"] and byte_count <= LIMITS["excerpt_bytes"], "receipt_byte_count_mismatch")
        key = keys[identifier]
        missing = [anchor for anchor in key["anchors"] if not any(
            record["path"] == anchor["path"] and anchor["contains"] in record["text"] for record in records)]
        missing_cutoffs = sorted(set(key["required_cutoffs"]) - set(search["cutoffs"]))
        passed = not missing and not missing_cutoffs
        independent_grade = {"all_required_spans_present": not missing, "missing_required_spans": missing,
                             "excerpt_hashes_valid": True, "missing_expected_cutoffs": missing_cutoffs,
                             "mechanical_pass": passed}
        _require(row["coverage"] == independent_grade, "receipt_coverage_disagrees")
        required_paths = {anchor["path"] for anchor in key["anchors"]}
        results.append({"id": identifier, "required_spans": len(key["anchors"]),
                        "span_hits": len(key["anchors"]) - len(missing),
                        "required_files": len(required_paths),
                        "file_hits": len(required_paths & {record["path"] for record in records}),
                        "duplicate_line_occurrences": len(occurrences) - len(set(occurrences)),
                        "mechanical_pass": passed, "cutoffs": search["cutoffs"]})
    passes = sum(row["mechanical_pass"] for row in results)
    _require(receipt["mechanical_passes"] == passes, "receipt_pass_count_disagrees")
    totals = {name: sum(row[name] for row in results) for name in
              ("required_spans", "span_hits", "required_files", "file_hits", "duplicate_line_occurrences")}
    return {"kind": "source_span_development_audit", "dataset": identity,
            "dataset_files_sha256": identities(files), "limits": dict(LIMITS),
            "case_count": len(results), "mechanical_passes": passes, "totals": totals,
            "cases": results, "semantic_model_accuracy": None, "warning": WARNING}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("generate")
    create.add_argument("--output", type=Path, required=True, help="New dataset directory outside this checkout")
    check = commands.add_parser("audit")
    check.add_argument("--dataset", type=Path, required=True)
    check.add_argument("--receipt", type=Path, required=True, help="run_task_lab.py --evidence-only JSON")
    check.add_argument("--output", type=Path, required=True, help="New audit JSON outside the dataset and checkout")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            result = {"dataset_files_sha256": generate(args.output)}
        else:
            output = args.output.resolve()
            for protected in (args.dataset.resolve(), Path(__file__).resolve().parents[1]):
                _require(output != protected and protected not in output.parents, "audit_output_inside_source")
            _require(not args.output.exists() and not args.output.is_symlink(), "audit_output_exists")
            with args.receipt.open("rb") as stream:
                data = stream.read(MAX_RECEIPT_BYTES + 1)
            _require(len(data) <= MAX_RECEIPT_BYTES, "receipt_byte_budget")
            result = audit(args.dataset, json.loads(data))
            result["receipt_sha256"] = sha(data)
            result["auditor_sha256"] = sha(Path(__file__).read_bytes())
            with args.output.open("xb") as stream:
                stream.write(encoded(result))
            result = {key: result[key] for key in ("case_count", "mechanical_passes", "totals")}
    except (ValueError, OSError, KeyError, TypeError, AttributeError, UnicodeError) as error:
        parser.exit(2, f"Source-span development check refused: {error}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

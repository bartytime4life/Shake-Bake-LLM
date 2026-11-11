"""Synthetic diagnostic contracts: file hits cannot stand in for exact spans."""

import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "benchmarks" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


span = load("source_span_development")
lab = load("run_task_lab")


class SourceSpanDevelopment(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.dataset = self.parent / "dataset"
        self.identities = span.generate(self.dataset)

    def receipt(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("fixture execution")):
            return json.loads(span.encoded(lab.run_cases(dataset=self.dataset)))

    def test_generation_is_location_independent_and_keys_stay_outside_inspected_roots(self):
        other = self.parent / "other"
        self.assertEqual(span.generate(other), self.identities)
        root, cases, keys, identity = lab.load_dataset(self.dataset)
        self.assertEqual(identity["split"], "development")
        self.assertEqual(identity["dataset_id"], span.DATASET_ID)
        self.assertEqual(len(cases), 6)
        self.assertEqual(sum(len(key["anchors"]) for key in keys.values()), 18)
        for case in cases:
            self.assertEqual(case["limits"], span.LIMITS)
            self.assertFalse(any(path.name in ("manifest.json", "grading-keys.json")
                                 for path in (root / "fixtures" / case["id"]).rglob("*")))
        self.assertEqual(span.identities(span._dataset_files(self.dataset)), self.identities)

    def test_existing_outputs_and_symlinks_are_refused_without_mutation(self):
        with self.assertRaisesRegex(ValueError, "dataset_output_exists"):
            span.generate(self.dataset)
        link = self.parent / "link"
        link.symlink_to(self.dataset, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "dataset_output_exists"):
            span.generate(link)
        dangling = self.parent / "dangling"
        dangling.symlink_to(self.parent / "absent")
        with self.assertRaisesRegex(ValueError, "dataset_output_exists"):
            span.generate(dangling)
        self.assertEqual(span.identities(span._dataset_files(self.dataset)), self.identities)

    def test_output_inside_checkout_is_refused_before_creation(self):
        with self.assertRaisesRegex(ValueError, "dataset_output_inside_checkout"):
            span.generate(ROOT / "benchmarks" / "must-not-be-created")
        self.assertFalse((ROOT / "benchmarks" / "must-not-be-created").exists())

    def test_model_free_current_collector_keeps_the_known_miss_in_its_denominator(self):
        receipt = self.receipt()
        result = span.audit(self.dataset, receipt)
        self.assertEqual(result["case_count"], 6)
        self.assertEqual(result["mechanical_passes"], 5)
        self.assertEqual(result["totals"], {"required_spans": 18, "span_hits": 17,
                                          "required_files": 12, "file_hits": 11,
                                          "duplicate_line_occurrences": 0})
        control = next(row for row in result["cases"] if row["id"] == "oversized-anchor")
        self.assertEqual(control["required_spans"], 1)
        self.assertEqual(control["span_hits"], 0)
        self.assertFalse(control["mechanical_pass"])
        self.assertIsNone(result["semantic_model_accuracy"])
        self.assertTrue(all(row["semantic_review"]["status"] == "PENDING" for row in receipt["cases"]))
        self.assertEqual(span.identities(span._dataset_files(self.dataset)), self.identities)

    def test_forged_coverage_and_model_or_input_changes_are_refused(self):
        original = self.receipt()
        mutations = [
            (lambda r: r.update(mechanical_passes=6), "receipt_pass_count_disagrees"),
            (lambda r: r["cases"][0]["coverage"].update(mechanical_pass=False), "receipt_coverage_disagrees"),
            (lambda r: r.update(model="unrequested-model"), "receipt_requires_model_free_completion"),
            (lambda r: r.update(rerank_model="unrequested-rerank"), "receipt_requires_model_free_completion"),
            (lambda r: r["dataset"].update(grading_keys_sha256="0" * 64), "receipt_dataset_mismatch"),
            (lambda r: r["cases"][0].update(task="changed request"), "receipt_case_inputs_mismatch"),
            (lambda r: r["cases"][0].update(fixture_sha256="0" * 64), "receipt_case_inputs_mismatch"),
            (lambda r: r["cases"][0]["brief"]["search"]["cutoffs"].append("time_budget"), "development_scan_incomplete"),
            (lambda r: r["cases"].reverse(), "receipt_case_selection_mismatch"),
        ]
        for mutate, error in mutations:
            with self.subTest(error=error):
                changed = copy.deepcopy(original)
                mutate(changed)
                with self.assertRaisesRegex(ValueError, error):
                    span.audit(self.dataset, changed)

    def test_rehashed_altered_text_and_wrong_ranges_or_byte_counts_are_refused(self):
        original = self.receipt()
        for field in ("text", "range", "bytes", "file_hash"):
            changed = copy.deepcopy(original)
            search = changed["cases"][0]["brief"]["search"]
            record = search["packet"]["evidence"][0]
            if field == "text":
                record["text"] = record["text"].replace("policy", "forged")
                record["excerpt_sha256"] = hashlib.sha256(record["text"].encode()).hexdigest()
            elif field == "range":
                record["start_line"] = 0
            elif field == "bytes":
                search["selected_excerpt_bytes"] += 1
            else:
                record["file_sha256"] = "0" * 64
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "receipt_(source_integrity|range_invalid|byte_count)"):
                span.audit(self.dataset, changed)

    def test_missing_cluster_can_keep_its_file_hit_while_losing_five_required_spans(self):
        changed = self.receipt()
        row = changed["cases"][0]
        search = row["brief"]["search"]
        omitted = search["packet"]["evidence"].pop()
        search["selected_excerpt_bytes"] -= len(omitted["text"].encode())
        missing = json.loads((self.dataset / "grading-keys.json").read_bytes())["cases"]["clustered-policy"]["anchors"][1:]
        row["coverage"].update(all_required_spans_present=False, missing_required_spans=missing, mechanical_pass=False)
        changed["mechanical_passes"] -= 1
        result = span.audit(self.dataset, changed)
        self.assertEqual(result["cases"][0]["file_hits"], 1)
        self.assertEqual(result["cases"][0]["span_hits"], 1)
        self.assertEqual(result["totals"]["file_hits"], 11)
        self.assertEqual(result["totals"]["span_hits"], 12)

    def test_repeated_exact_record_counts_only_additional_line_occurrences(self):
        changed = self.receipt()
        search = changed["cases"][1]["brief"]["search"]
        duplicate = copy.deepcopy(search["packet"]["evidence"][0])
        search["packet"]["evidence"].append(duplicate)
        search["selected_excerpt_bytes"] += len(duplicate["text"].encode())
        result = span.audit(self.dataset, changed)
        self.assertEqual(result["cases"][1]["duplicate_line_occurrences"], duplicate["end_line"] - duplicate["start_line"] + 1)
        self.assertEqual(result["totals"]["span_hits"], 17)
        self.assertEqual(result["totals"]["file_hits"], 11)

    def test_dataset_byte_changes_and_extra_files_are_refused(self):
        receipt = self.receipt()
        source = self.dataset / "fixtures/clustered-policy/policy.py"
        exact = source.read_bytes()
        source.write_bytes(exact.replace(b"policy", b"xxxxxx", 1))
        with self.assertRaisesRegex(ValueError, "development_dataset_changed"):
            span.audit(self.dataset, receipt)
        source.write_bytes(exact)
        (self.dataset / "fixtures/clustered-policy/extra.py").write_text("# extra\n")
        with self.assertRaisesRegex(ValueError, "development_dataset_changed"):
            span.audit(self.dataset, receipt)

    def test_cli_audit_binds_receipt_bytes_and_never_overwrites_inputs_or_outputs(self):
        receipt = self.parent / "receipt.json"
        exact = span.encoded(self.receipt())
        receipt.write_bytes(exact)
        output = self.parent / "audit.json"
        args = ["audit", "--dataset", str(self.dataset), "--receipt", str(receipt), "--output", str(output)]
        completed = subprocess.run([sys.executable, "-I", str(Path(span.__file__)), *args],
                                   capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["mechanical_passes"], 5)
        result = json.loads(output.read_bytes())
        self.assertEqual(result["receipt_sha256"], hashlib.sha256(exact).hexdigest())
        self.assertEqual(result["auditor_sha256"], hashlib.sha256(Path(span.__file__).read_bytes()).hexdigest())
        for destination in (output, receipt, self.dataset / "audit.json", ROOT / "audit-must-not-exist.json"):
            with self.subTest(destination=destination), patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit) as stopped:
                span.main(args[:-1] + [str(destination)])
            self.assertEqual(stopped.exception.code, 2)
        self.assertEqual(receipt.read_bytes(), exact)
        self.assertFalse((self.dataset / "audit.json").exists())
        self.assertFalse((ROOT / "audit-must-not-exist.json").exists())


if __name__ == "__main__":
    unittest.main()

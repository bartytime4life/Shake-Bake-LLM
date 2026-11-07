"""Synthetic paired receipts test comparison methodology, never model accuracy."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
import compare_recall_receipts as paired


def case(identifier, gold, hits):
    row = {"id": identifier, "changed_files": gold, "seconds": .01, "cutoffs": ["file_budget"], "exclusions": {"low_signal_match": 2}}
    for level in paired.LEVELS:
        row["hits_" + level] = hits
        row["recall_" + level] = hits / gold
    return row


def receipt(rows):
    return {"kind": "external_file_recall", "receipt_schema": 2, "cases_sha256": "a" * 64,
            "python": "synthetic-python", "platform": "synthetic-platform", "timing_scope": "synthetic-single-call",
            "selection_sha256": "b" * 64, "case_root_locations_sha256": "c" * 64,
            "source_identity": {"adapter_sha256": "d" * 64, "collector_sources_sha256": {
                name: "e" * 64 for name in ("__init__.py", "contracts.py", "collector.py", "search.py")}},
            "limits": {"max_files": 200, "max_entries": 4000, "max_depth": 8, "seconds": 5.0,
                       "excerpt_bytes": 16384, "context_bytes": 2048},
            "rerank_model": None, "selected_case_ids": [row["id"] for row in rows], "case_count": len(rows),
            "scored": sum("refused" not in row for row in rows), "refused": sum("refused" in row for row in rows), "cases": rows}


class PairedRecallTests(unittest.TestCase):
    def test_macro_gain_does_not_hide_unchanged_total_hits_or_a_regression(self):
        before = receipt([case("single", 1, 0), case("multiple", 3, 1)])
        after = receipt([case("single", 1, 1), case("multiple", 3, 0)])
        after["source_identity"]["collector_sources_sha256"]["search.py"] = "f" * 64
        report = paired.compare(before, after)
        primary = report["metrics"]["primary"]
        self.assertAlmostEqual(primary["mean_recall_before"], 1 / 6)
        self.assertEqual(primary["mean_recall_after"], .5)
        self.assertEqual((primary["hits_before"], primary["hits_after"], primary["gold_files"]), (1, 1, 4))
        self.assertEqual((primary["wins"], primary["losses"]), (1, 1))
        self.assertEqual(primary["micro_recall_before"], primary["micro_recall_after"])
        self.assertFalse(report["corpus_immutability_established"])

    def test_one_sided_refusals_are_explicit_and_removed_from_both_means(self):
        before = receipt([case("scored", 1, 0), case("refused-later", 2, 2)])
        after = receipt([case("scored", 1, 1), {"id": "refused-later", "changed_files": 2, "refused": "source_unavailable"}])
        report = paired.compare(before, after)
        self.assertEqual(report["paired_scored_cases"], 1)
        self.assertEqual(report["metrics"]["primary"]["gold_files"], 1)
        self.assertEqual(report["excluded_pairs"][0]["id"], "refused-later")
        self.assertEqual(report["metrics"]["primary"]["mean_recall_before"], 0)

    def test_budget_cases_subset_root_or_adapter_mismatches_refuse(self):
        before = receipt([case("one", 1, 0)])
        for field in ("limits", "cases_sha256", "selection_sha256", "case_root_locations_sha256", "adapter", "python", "platform"):
            after = copy.deepcopy(before)
            if field == "limits":
                after[field]["max_files"] = 1000
            elif field == "adapter":
                after["source_identity"]["adapter_sha256"] = "f" * 64
            else:
                after[field] = "f" * 64
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "mismatch"):
                paired.compare(before, after)

    def test_legacy_receipts_and_inconsistent_or_duplicate_rows_refuse(self):
        good = receipt([case("one", 1, 0)])
        bad = copy.deepcopy(good); bad.pop("receipt_schema")
        with self.assertRaisesRegex(ValueError, "receipt_provenance_required"):
            paired.compare(bad, good)
        bad = copy.deepcopy(good); bad["cases"][0]["recall_primary"] = 1
        with self.assertRaisesRegex(ValueError, "receipt_recall_inconsistent"):
            paired.compare(bad, good)
        duplicate = receipt([case("one", 1, 0), case("one", 1, 0)])
        with self.assertRaisesRegex(ValueError, "duplicate_receipt_case_id"):
            paired.compare(duplicate, duplicate)

    def test_no_scored_pairs_reports_unknown_means(self):
        refused = receipt([{"id": "one", "changed_files": 1, "refused": "not_available"}])
        report = paired.compare(refused, refused)
        self.assertEqual(report["paired_scored_cases"], 0)
        self.assertIsNone(report["metrics"]["primary"]["mean_recall_before"])

    def test_model_tags_do_not_substitute_for_a_frozen_model_identity(self):
        tagged = receipt([case("one", 1, 1)])
        tagged["rerank_model"] = "synthetic:mutable-tag"
        with self.assertRaisesRegex(ValueError, "lexical_comparison_requires_no_rerank"):
            paired.compare(tagged, tagged)

    def test_cli_binds_exact_receipt_bytes_and_never_overwrites_results(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            before, after, output = [base / name for name in ("before.json", "after.json", "paired.json")]
            before.write_text(json.dumps(receipt([case("one", 1, 0)])))
            after.write_text(json.dumps(receipt([case("one", 1, 1)])))
            with contextlib.redirect_stdout(io.StringIO()):
                paired.main(["--before", str(before), "--after", str(after), "--output", str(output)])
            report = json.loads(output.read_text())
            self.assertEqual(len(report["before_receipt_sha256"]), 64)
            original = output.read_bytes()
            with self.assertRaisesRegex(ValueError, "comparison_output_exists"):
                paired.main(["--before", str(before), "--after", str(after), "--output", str(output)])
            self.assertEqual(original, output.read_bytes())


if __name__ == "__main__":
    unittest.main()

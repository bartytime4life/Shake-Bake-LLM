"""Synthetic cases test the external file-recall mechanism, not any dataset result."""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.search import SearchLimits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
import external_recall as recall


class ExternalRecallAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        repo = self.base / "repos" / "parcel"
        (repo / "app").mkdir(parents=True)
        (repo / "tests").mkdir()
        (repo / "app" / "submit.py").write_text("from app.settings import load_settings\n\ndef submit_job(payload, environ):\n    return load_settings(environ)\n", encoding="utf-8")
        (repo / "app" / "settings.py").write_text("DEFAULT_BACKEND = 'local'\n\ndef load_settings(environ):\n    return environ.get('PARCEL_BACKEND', DEFAULT_BACKEND)\n", encoding="utf-8")
        (repo / "app" / "unrelated.py").write_text("rainbow = 42\n", encoding="utf-8")
        (repo / "tests" / "test_submit.py").write_text("from app.submit import submit_job\n\ndef test_default():\n    assert submit_job({}, {}) == 'local'\n", encoding="utf-8")
        self.cases = self.base / "cases.jsonl"
        self.cases.write_text(json.dumps({"id": "parcel#1", "root": "parcel", "request": "submit_job ignores PARCEL_BACKEND override",
                                          "changed_files": ["app/settings.py", "app/submit.py", "docs/missing.md"]}) + "\n"
                              + json.dumps({"id": "parcel#2", "root": "absent", "request": "submit_job", "changed_files": ["x.py"]}) + "\n",
                              encoding="utf-8")

    def test_recall_levels_refusals_and_receipt_are_reported(self):
        report = recall.run(recall.load_cases(self.cases, self.base / "repos"), SearchLimits())
        self.assertEqual((report["case_count"], report["scored"], report["refused"]), (2, 1, 1))
        case = report["cases"][0]
        self.assertEqual(case["changed_files"], 3)
        self.assertEqual(case["hits_excerpted"], 2)
        self.assertAlmostEqual(case["recall_excerpted"], 2 / 3)
        self.assertGreaterEqual(case["recall_excerpted"], case["recall_primary"])
        self.assertGreaterEqual(case["recall_with_map"], case["recall_excerpted"])
        self.assertGreaterEqual(case["recall_with_index"], case["recall_with_map"])
        self.assertIn("mean_recall_with_index", report)
        self.assertEqual(report["cases"][1]["refused"], "case_root_not_allowed")
        self.assertEqual(report["cases_with_any_excerpted_hit"], 1.0)
        self.assertEqual(report["cases_hitting_file_budget"], 0)
        self.assertIn("not answer accuracy", report["warning"])

    def test_cli_writes_receipt_outside_checkout_and_prints_summary(self):
        output = self.base / "receipt.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = recall.main(["--cases", str(self.cases), "--repos", str(self.base / "repos"), "--limit", "1", "--max-files", "3", "--max-depth", "3", "--excerpt-bytes", "4096", "--output", str(output)])
        self.assertEqual(code, 0)
        summary = json.loads(stdout.getvalue())
        receipt = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(summary["case_count"], 1)
        self.assertNotIn("cases", summary)
        self.assertEqual(receipt["limits"]["max_files"], 3)
        self.assertEqual(receipt["limits"]["max_depth"], 3)
        self.assertEqual(receipt["limits"]["excerpt_bytes"], 4096)
        self.assertEqual(receipt["cases_hitting_file_budget"], 1)
        self.assertIn("file_budget", receipt["cases"][0]["cutoffs"])
        self.assertEqual(len(receipt["cases_sha256"]), 64)

    def test_controlling_context_does_not_fill_unused_primary_slots(self):
        repo = self.base / "repos" / "context_only"
        repo.mkdir()
        (repo / "main.py").write_text("needle = resolve_setting()\n", encoding="utf-8")
        (repo / "helper.py").write_text("def resolve_setting():\n    return 'local'\n", encoding="utf-8")
        cases = [{"id": "synthetic-context", "root": repo, "request": "needle", "changed_files": ["helper.py"]}]
        report = recall.run(cases, SearchLimits())
        case = report["cases"][0]
        self.assertEqual(case["hits_excerpted"], 1)
        self.assertEqual(case["hits_primary"], 0)
        self.assertEqual(case["recall_primary"], 0.0)
        self.assertEqual(case["primary_excerpts"], 1)
        self.assertEqual(case["controlling_context_excerpts"], 1)
        self.assertEqual(case["excerpts"], 2)
        cases[0]["changed_files"] = ["main.py", "helper.py"]
        both = recall.run(cases, SearchLimits())["cases"][0]
        self.assertEqual(both["hits_primary"], 1)
        self.assertEqual(both["recall_primary"], 0.5)
        self.assertEqual(both["recall_excerpted"], 1.0)

    def test_primary_excerpt_counts_are_zero_when_nothing_matches(self):
        repo = self.base / "repos" / "no_match"
        repo.mkdir()
        (repo / "ordinary.py").write_text("ordinary = 1\n", encoding="utf-8")
        report = recall.run([{"id": "synthetic-no-match", "root": repo, "request": "needle", "changed_files": ["ordinary.py"]}], SearchLimits())
        case = report["cases"][0]
        self.assertEqual(case["primary_excerpts"], 0)
        self.assertEqual(case["controlling_context_excerpts"], 0)
        self.assertEqual(case["hits_primary"], 0)
        self.assertEqual(case["hits_excerpted"], 0)

    def test_case_roots_inside_the_checkout_and_invalid_rows_are_refused(self):
        inside = self.base / "inside.jsonl"
        inside.write_text(json.dumps({"id": "self", "root": str(ROOT), "request": "search", "changed_files": ["a.py"]}) + "\n", encoding="utf-8")
        report = recall.run(recall.load_cases(inside, None), SearchLimits())
        self.assertEqual(report["cases"][0]["refused"], "case_root_not_allowed")
        bad = self.base / "bad.jsonl"
        bad.write_text(json.dumps({"id": "x", "root": "parcel", "request": "r", "changed_files": []}) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(Refusal, "invalid_case"):
            recall.load_cases(bad, self.base / "repos")
        with self.assertRaisesRegex(Refusal, "case_root_requires_repos_dir"):
            recall.load_cases(self.cases, None)

    def test_receipt_binds_selected_subset_sources_and_runtime(self):
        outputs = []
        for limit in (1, 2):
            output = self.base / f"limit-{limit}.json"
            with contextlib.redirect_stdout(io.StringIO()):
                recall.main(["--cases", str(self.cases), "--repos", str(self.base / "repos"), "--limit", str(limit), "--output", str(output)])
            outputs.append(json.loads(output.read_text()))
        self.assertEqual(outputs[0]["cases_sha256"], outputs[1]["cases_sha256"])
        self.assertNotEqual(outputs[0]["selection_sha256"], outputs[1]["selection_sha256"])
        self.assertEqual(outputs[0]["selected_case_ids"], ["parcel#1"])
        self.assertEqual(outputs[0]["receipt_schema"], 2)
        self.assertEqual(len(outputs[0]["source_identity"]["collector_sources_sha256"]["search.py"]), 64)
        self.assertIn("python", outputs[0])
        self.assertFalse(outputs[0]["corpus_content_immutability_verified"])

    def test_changed_case_input_is_refused_without_writing_receipt(self):
        output = self.base / "changed.json"
        original = recall.run
        def mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            self.cases.write_text("changed after collection\n")
            return result
        with patch.object(recall, "run", side_effect=mutate), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(Refusal, "evaluation_cases_changed"):
                recall.main(["--cases", str(self.cases), "--repos", str(self.base / "repos"), "--output", str(output)])
        self.assertFalse(output.exists())

    def test_changed_collector_identity_is_refused_without_writing_receipt(self):
        output = self.base / "changed-code.json"
        with patch.object(recall, "source_identity", side_effect=[{"code": "before"}, {"code": "after"}]), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(Refusal, "evaluation_code_changed"):
                recall.main(["--cases", str(self.cases), "--repos", str(self.base / "repos"), "--output", str(output)])
        self.assertFalse(output.exists())

    def test_existing_receipts_and_source_outputs_are_refused_before_collection(self):
        output = self.base / "existing.json"
        output.write_text("preserved receipt")
        protected = self.base / "repos" / "parcel" / "new-receipt.json"
        with patch.object(recall, "run", side_effect=AssertionError("collection started")):
            for path, code in ((output, "receipt_output_exists"), (protected, "receipt_output_inside_source")):
                with self.assertRaisesRegex(Refusal, code):
                    recall.main(["--cases", str(self.cases), "--repos", str(self.base / "repos"), "--output", str(path)])
        self.assertEqual(output.read_text(), "preserved receipt")
        self.assertFalse(protected.exists())

    def test_duplicate_ids_and_nonpositive_selection_limits_are_refused(self):
        raw = self.cases.read_text().splitlines()[0]
        self.cases.write_text(raw + "\n" + raw + "\n")
        with self.assertRaisesRegex(Refusal, "duplicate_or_empty_case_id"):
            recall.load_cases(self.cases, self.base / "repos")
        for limit in ("0", "-1"):
            with self.assertRaisesRegex(Refusal, "invalid_case_limit"):
                recall.main(["--cases", str(self.cases), "--limit", limit])


if __name__ == "__main__":
    unittest.main()

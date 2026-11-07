"""Synthetic cases test the external file-recall mechanism, not any dataset result."""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

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
            code = recall.main(["--cases", str(self.cases), "--repos", str(self.base / "repos"), "--limit", "1", "--max-files", "3", "--output", str(output)])
        self.assertEqual(code, 0)
        summary = json.loads(stdout.getvalue())
        receipt = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(summary["case_count"], 1)
        self.assertNotIn("cases", summary)
        self.assertEqual(receipt["limits"]["max_files"], 3)
        self.assertEqual(receipt["cases_hitting_file_budget"], 1)
        self.assertIn("file_budget", receipt["cases"][0]["cutoffs"])
        self.assertEqual(len(receipt["cases_sha256"]), 64)

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


if __name__ == "__main__":
    unittest.main()

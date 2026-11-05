import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_task_lab", ROOT / "benchmarks/run_task_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class TaskLabAcceptance(unittest.TestCase):
    def test_all_exposed_jobs_retain_required_spans_without_model_or_execution(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("process")):
            result = lab.run_cases()
        self.assertEqual(result["case_count"], 10)
        self.assertEqual(result["mechanical_passes"], 10)
        self.assertIsNone(result["semantic_model_accuracy"])
        self.assertTrue(all(c["fixture_unchanged"] for c in result["cases"]))
        self.assertTrue(all(c["semantic_review"]["status"] == "PENDING" for c in result["cases"]))

    def test_missing_span_fails_even_when_file_selected_and_hash_valid(self):
        brief = lab.build_brief(lab.LAB / "fixtures/boundary", "marker position contains")
        key = {"anchors": [{"path": "ranges.py", "contains": "nonexistent-branch"}], "required_cutoffs": []}
        result = lab.grade_coverage(brief, key)
        self.assertTrue(result["excerpt_hashes_valid"])
        self.assertFalse(result["mechanical_pass"])

    def test_grading_keys_never_enter_worker_preparation(self):
        original = lab.build_brief
        captured = []
        def observe(root, task, **kwargs):
            captured.append((root, task, kwargs))
            return original(root, task, **kwargs)
        with patch.object(lab, "build_brief", side_effect=observe):
            lab.run_cases(case_ids=["injection"])
        root, task, kwargs = captured[0]
        self.assertEqual(root, lab.LAB / "fixtures/injection")
        self.assertNotIn("grading-keys", task + json.dumps(kwargs, default=str))
        self.assertFalse(any(path.name == "grading-keys.json" for path in root.rglob("*")))


if __name__ == "__main__":
    unittest.main()

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
import public_host_review as review


class PublicHostReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.receipt_path = self.root / "receipt.json"
        self.review_path = self.root / "reviews.json"
        plan = [{"attempt_id": f"1:synthetic-case:{arm}", "round": 1,
                 "case_id": "synthetic-case", "arm": arm} for arm in ("native", "prepared")]
        attempts = []
        for index, planned in enumerate(plan, 1):
            answer = f"Synthetic answer {index}: exact source required.\n".encode()
            folder = self.root / f"{index:02d}-synthetic-case-{planned['arm']}"
            folder.mkdir()
            (folder / "answer.md").write_bytes(answer)
            attempts.append({**planned, "index": index, "answer_sha256": review.sha(answer),
                             "exit_code": 0, "error": None, "fixture_unchanged": True,
                             "host_seconds": index + 0.5, "preparation_seconds": 0.01 * (index - 1),
                             "usage": {"input_tokens": 100 * index, "cached_input_tokens": 80 * index,
                                       "output_tokens": 10 * index}})
        self.receipt = {"kind": "public_change_review_development_trial", "status": "FINISHED_UNGRADED",
                        "attempt_plan": plan, "attempts": attempts}
        self.save_receipt()

    def save_receipt(self):
        self.receipt_path.write_text(json.dumps(self.receipt) + "\n")

    def sheet(self, complete=True):
        document = review.prepare(self.receipt_path)
        if complete:
            document.update(reviewer="Synthetic reviewer", reviewer_kind="ai")
            for entry in document["entries"]:
                entry.update(reference_matches=[], unsupported_claims=0, critical_misses=0,
                             supported_outcome=True, review_notes="Synthetic exact source was compared.")
        self.review_path.write_text(json.dumps(document) + "\n")
        return document

    def save_review(self, document):
        self.review_path.write_text(json.dumps(document) + "\n")

    def test_current_runner_sheet_fields_are_receipt_bound(self):
        sheet = self.sheet()
        # The current runner's packet has no schema_version or explicit attempt ID.
        self.assertNotIn("schema_version", sheet)
        self.assertNotIn("attempt_id", sheet["entries"][0])
        for entry in sheet["entries"]:
            del entry["review_binding"]  # The existing runner has no opaque binding.
        sheet["entries"].reverse()  # Review labels/order do not choose an arm.
        self.save_review(sheet)
        result = review.score(self.receipt_path, self.review_path)
        self.assertEqual(result["review_status"], "REVIEWED")
        self.assertTrue(result["trial_complete"])
        self.assertEqual(result["arm_totals"]["native"]["supported_outcomes_per_planned_attempt"], 1)
        self.assertEqual(result["arm_totals"]["prepared"]["reported_usage_sums"]["input_tokens"], 200)
        self.assertEqual(result["arm_totals"]["prepared"]["reported_usage_sums"]["cached_input_tokens"], 160)
        self.assertTrue(result["reviewer_identity_is_self_declared"])
        self.assertFalse(result["auto_promotion_allowed"])
        self.assertIsNone(result["cloud_savings"])
        self.assertIsNone(result["independent_human_qualification"])
        self.assertNotIn("Synthetic answer", json.dumps(result))
        self.assertNotIn("Synthetic exact source", json.dumps(result))

    def test_partial_and_current_unannotated_packet_stays_pending(self):
        sheet = self.sheet(complete=False)
        del sheet["reviewer_kind"]  # The runner emits no kind; blank sheets remain readable.
        self.save_review(sheet)
        result = review.score(self.receipt_path, self.review_path)
        self.assertEqual(result["review_status"], "PENDING")
        self.assertIsNone(result["arm_totals"]["native"]["supported_outcomes"])
        self.assertIsNone(result["arm_totals"]["native"]["supported_outcomes_per_planned_attempt"])

    def test_receipt_and_raw_answer_tampering_refused(self):
        self.sheet()
        self.receipt["status"] = "RUNNING"
        self.save_receipt()
        with self.assertRaisesRegex(ValueError, "review_receipt_mismatch"):
            review.score(self.receipt_path, self.review_path)
        self.receipt["status"] = "FINISHED_UNGRADED"
        self.save_receipt()
        (self.root / "01-synthetic-case-native" / "answer.md").write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "answer_identity_mismatch"):
            review.score(self.receipt_path, self.review_path)

    def test_embedded_answer_tampering_refused(self):
        sheet = self.sheet()
        sheet["entries"][0]["answer"] += "invented text"
        self.save_review(sheet)
        with self.assertRaisesRegex(ValueError, "review_answer_mismatch"):
            review.score(self.receipt_path, self.review_path)

    def test_duplicate_missing_and_wrong_case_entries_refused(self):
        original = self.sheet()
        for change, reason in ((lambda s: s["entries"].pop(), "incomplete_review_entries"),
                               (lambda s: s["entries"].__setitem__(1, copy.deepcopy(s["entries"][0])),
                                "duplicate_or_invalid_review_label"),
                               (lambda s: s["entries"][0].update(case_id="other"), "review_attempt_mismatch")):
            with self.subTest(reason=reason):
                sheet = copy.deepcopy(original)
                change(sheet)
                self.save_review(sheet)
                with self.assertRaisesRegex(ValueError, reason):
                    review.score(self.receipt_path, self.review_path)

    def test_invalid_and_inconsistent_judgments_refused(self):
        original = self.sheet()
        for update, reason in (({"unsupported_claims": True}, "invalid_review_count"),
                               ({"critical_misses": -1}, "invalid_review_count"),
                               ({"supported_outcome": 1}, "invalid_supported_outcome"),
                               ({"reference_matches": [1, 1]}, "invalid_reference_matches"),
                               ({"reference_matches": [True]}, "invalid_reference_matches"),
                               ({"critical_misses": 1}, "inconsistent_supported_outcome"),
                               ({"review_notes": " "}, "review_evidence_notes_required")):
            with self.subTest(update=update):
                sheet = copy.deepcopy(original)
                sheet["entries"][0].update(update)
                self.save_review(sheet)
                with self.assertRaisesRegex(ValueError, reason):
                    review.score(self.receipt_path, self.review_path)

    def test_reviewer_kind_required_and_is_not_identity_authentication(self):
        sheet = self.sheet()
        for kind in ("", "independent-human"):
            sheet["reviewer_kind"] = kind
            self.save_review(sheet)
            with self.assertRaisesRegex(ValueError, "reviewer_kind_required|invalid_reviewer_kind"):
                review.score(self.receipt_path, self.review_path)
        sheet["reviewer_kind"] = "human"
        self.save_review(sheet)
        result = review.score(self.receipt_path, self.review_path)
        self.assertIsNone(result["independent_human_qualification"])
        self.assertTrue(result["reviewer_identity_is_self_declared"])

    def test_failed_and_unstarted_attempts_remain_visible(self):
        self.receipt["status"] = "STOPPED_AFTER_ATTEMPT_FAILURE"
        self.receipt["attempts"] = self.receipt["attempts"][:1]
        self.receipt["attempts"][0].update(exit_code=1, error="host_deadline", usage=None)
        self.save_receipt()
        sheet = self.sheet()
        with self.assertRaisesRegex(ValueError, "failed_attempt_cannot_be_supported"):
            review.score(self.receipt_path, self.review_path)
        sheet["entries"][0]["supported_outcome"] = False
        self.save_review(sheet)
        result = review.score(self.receipt_path, self.review_path)
        self.assertFalse(result["trial_complete"])
        self.assertEqual(result["planned_attempts"], 2)
        self.assertEqual(result["started_attempts"], 1)
        self.assertEqual(result["arm_totals"]["native"]["supported_outcomes"], 0)
        self.assertEqual(result["arm_totals"]["prepared"]["unstarted_attempts"], 1)
        self.assertIsNone(result["arm_totals"]["native"]["supported_outcomes_per_planned_attempt"])
        self.assertEqual(result["arm_totals"]["native"]["usage_missing_attempts"]["input_tokens"], 1)
        self.assertIn("host_not_successful", result["attempts"][0]["failure_reasons"])

    def test_failed_attempt_with_no_answer_can_be_reviewed_without_fabrication(self):
        attempt = self.receipt["attempts"][0]
        attempt.update(answer_sha256=None, exit_code=1, error="host_deadline")
        self.receipt["status"] = "STOPPED_AFTER_ATTEMPT_FAILURE"
        self.receipt["attempts"] = [attempt]
        self.save_receipt()
        sheet = self.sheet(complete=False)
        self.assertIsNone(sheet["entries"][0]["answer"])
        result = review.score(self.receipt_path, self.review_path)
        self.assertEqual(result["review_status"], "PENDING")
        self.assertFalse(result["attempts"][0]["completed"])

    def test_plan_drift_path_injection_and_invalid_usage_refused(self):
        original = copy.deepcopy(self.receipt)
        for update, reason in (({"case_id": "../outside"}, "invalid_case_id"),
                               ({"attempt_id": "wrong"}, "invalid_attempt_id"),
                               ({"index": 3}, "attempt_plan_mismatch"),
                               ({"usage": {"input_tokens": 1, "cached_input_tokens": 2}}, "invalid_cached_usage")):
            with self.subTest(update=update):
                self.receipt = copy.deepcopy(original)
                self.receipt["attempts"][0].update(update)
                self.save_receipt()
                with self.assertRaisesRegex(ValueError, reason):
                    review.prepare(self.receipt_path)

    def test_identical_answers_use_opaque_per_attempt_bindings(self):
        answer = (self.root / "01-synthetic-case-native" / "answer.md").read_bytes()
        (self.root / "02-synthetic-case-prepared" / "answer.md").write_bytes(answer)
        self.receipt["attempts"][1]["answer_sha256"] = review.sha(answer)
        self.save_receipt()
        sheet = self.sheet()
        self.assertEqual(sheet["entries"][0]["answer_sha256"], sheet["entries"][1]["answer_sha256"])
        self.assertNotEqual(sheet["entries"][0]["review_binding"], sheet["entries"][1]["review_binding"])
        result = review.score(self.receipt_path, self.review_path)
        self.assertEqual(result["review_status"], "REVIEWED")
        self.assertEqual(result["arm_totals"]["native"]["supported_outcomes"], 1)
        self.assertEqual(result["arm_totals"]["prepared"]["supported_outcomes"], 1)
        # Legacy packets cannot safely assign two identical same-case/round
        # answers to arms; a new prepare sheet supplies the missing binding.
        for entry in sheet["entries"]:
            del entry["review_binding"]
        self.save_review(sheet)
        with self.assertRaisesRegex(ValueError, "ambiguous_review_identity"):
            review.score(self.receipt_path, self.review_path)

    def test_tampered_or_swapped_bindings_are_refused(self):
        sheet = self.sheet()
        original = sheet["entries"][0]["review_binding"]
        sheet["entries"][0]["review_binding"] = "0" * 64
        self.save_review(sheet)
        with self.assertRaisesRegex(ValueError, "review_binding_mismatch"):
            review.score(self.receipt_path, self.review_path)
        sheet["entries"][0]["review_binding"] = sheet["entries"][1]["review_binding"]
        self.save_review(sheet)
        with self.assertRaisesRegex(ValueError, "review_attempt_mismatch"):
            review.score(self.receipt_path, self.review_path)
        sheet["entries"][0]["review_binding"] = original
        self.save_review(sheet)
        self.assertEqual(review.score(self.receipt_path, self.review_path)["review_status"], "REVIEWED")

    def test_symlinked_answer_or_folder_refused(self):
        answer = self.root / "01-synthetic-case-native" / "answer.md"
        original = answer.read_bytes()
        target = self.root / "other-answer.md"
        target.write_bytes(original)
        answer.unlink()
        answer.symlink_to(target)
        with self.assertRaises(OSError):
            review.prepare(self.receipt_path)
        answer.unlink()
        answer.write_bytes(original)
        folder = answer.parent
        moved = self.root / "moved"
        folder.rename(moved)
        folder.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(OSError):
            review.prepare(self.receipt_path)

    def test_duplicate_json_keys_and_nonfinite_numbers_refused(self):
        for data, reason in ((b'{"status":1,"status":2}', "duplicate_json_key"),
                             (b'{"seconds":NaN}', "nonfinite_json_value")):
            with self.assertRaisesRegex(ValueError, reason):
                review.document(data)

    def test_output_must_be_new_and_outside_checkout(self):
        output = self.root / "report.json"
        previous_mask = os.umask(0o022)
        try:
            review.write_new(output, {"safe": True})
        finally:
            os.umask(previous_mask)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            review.write_new(output, {"safe": False})
        checkout = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "review_output_in_checkout"):
            review.write_new(checkout / "do-not-create.json", {})
        target = self.root / "must-not-create.json"
        link = self.root / "output-link.json"
        link.symlink_to(target)
        with self.assertRaises(FileExistsError):
            review.write_new(link, {})
        self.assertFalse(target.exists())

    def test_malformed_top_level_fields_are_refused(self):
        for status in ({}, [], True):
            self.receipt["status"] = status
            self.save_receipt()
            with self.assertRaisesRegex(ValueError, "invalid_trial_status"):
                review.prepare(self.receipt_path)


if __name__ == "__main__":
    unittest.main()

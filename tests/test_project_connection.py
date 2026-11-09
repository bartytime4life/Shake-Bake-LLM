"""Owner-only folder connection boundaries, using disposable source fixtures."""

import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from shake_bake.contracts import Refusal
from shake_bake.helper import HelperSession


@unittest.skipUnless(sys.platform == "linux", "Linux task-supervision profile")
class ProjectConnectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.original = self.folder("original")
        self.additional = self.folder("additional")
        (self.original / "app.py").write_text("def original_value():\n    return 17\n", encoding="utf-8")
        (self.additional / "app.py").write_text("def additional_value():\n    return 29\n", encoding="utf-8")

    def folder(self, name):
        folder = self.base / name
        folder.mkdir()
        return folder

    def session(self, **options):
        helper = HelperSession({"original": self.original}, **(options or {"evidence_only": True}))
        self.addCleanup(helper.close)
        return helper

    def finished(self, helper, identifier):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            result = helper.get_result(identifier)
            if result["state"] != "RUNNING":
                self.assertEqual(result["state"], "DONE", result)
                return result
            time.sleep(0.005)
        self.fail("fixture task did not finish")

    def test_new_folder_is_usable_without_losing_original_jobs_or_scope(self):
        helper = self.session()
        old_id = helper.start_task("original", "Find original_value")["task_id"]
        old_result = self.finished(helper, old_id)
        old_evidence = helper.fetch_evidence(old_id, "E1")

        connected = helper.add_project("additional", self.additional)

        self.assertEqual(connected, {"id": "additional", "path": str(self.additional.resolve())})
        self.assertEqual(helper.list_projects()["projects"], ["additional", "original"])
        self.assertNotIn(str(self.base), json.dumps(helper.list_projects()))
        self.assertEqual(helper.get_result(old_id), old_result)
        self.assertEqual(helper.fetch_evidence(old_id, "E1"), old_evidence)
        new_id = helper.start_task("additional", "Find additional_value")["task_id"]
        self.finished(helper, new_id)
        self.assertIn("return 29", helper.fetch_evidence(new_id, "E1")["text"])
        self.assertEqual(helper.fetch_evidence(old_id, "E1"), old_evidence)
        with self.assertRaisesRegex(Refusal, "project_not_allowed"):
            helper.start_task("unconnected", "Find original_value")

    def test_invalid_ids_and_nonabsolute_or_unavailable_roots_do_not_connect(self):
        helper = self.session()
        for project_id in ("", "UPPER", "../outside", "two words", None, "a" * 49):
            with self.subTest(project_id=project_id), self.assertRaisesRegex(Refusal, "invalid_project_id"):
                helper.add_project(project_id, self.additional)
        for path in ("relative", Path("."), self.base / "missing", self.original / "app.py", None, "\x00"):
            with self.subTest(path=path), self.assertRaisesRegex(Refusal, "invalid_project_root"):
                helper.add_project("additional", path)
        self.assertEqual(helper.list_projects()["projects"], ["original"])
        self.assertEqual(helper._jobs, {})

    def test_configuration_and_owner_connection_share_absolute_root_validation(self):
        with self.assertRaisesRegex(Refusal, "invalid_project_root"):
            HelperSession({"relative": Path(".")}, evidence_only=True)

    def test_id_cannot_be_reassigned_and_resolved_folder_cannot_be_connected_twice(self):
        helper = self.session()
        with self.assertRaisesRegex(Refusal, "duplicate_project_id"):
            helper.add_project("original", self.additional)
        alias = self.base / "alias"
        alias.symlink_to(self.original, target_is_directory=True)
        for path in (self.original, alias, self.original / ".." / "original"):
            with self.subTest(path=path), self.assertRaisesRegex(Refusal, "duplicate_project_root"):
                helper.add_project("alias", path)
        self.assertEqual(helper._projects, {"original": self.original.resolve()})

    def test_filesystem_root_and_owner_home_are_too_broad(self):
        helper = self.session()
        with self.assertRaisesRegex(Refusal, "project_root_too_broad"):
            helper.add_project("whole-disk", Path("/"))
        with patch("shake_bake.helper.Path.home", return_value=self.additional):
            with self.assertRaisesRegex(Refusal, "project_root_too_broad"):
                helper.add_project("whole-home", self.additional)
        self.assertEqual(helper.list_projects()["projects"], ["original"])

    def test_folder_containing_task_io_is_rejected_without_moving_task_storage(self):
        scratch = self.folder("scratch")
        with patch("shake_bake.helper.tempfile.gettempdir", return_value=str(scratch)):
            helper = self.session()
        self.assertEqual(helper._scratch, scratch)
        for root in (scratch, self.base):
            with self.subTest(root=root), self.assertRaisesRegex(Refusal, "external_task_scratch_required"):
                helper.add_project("task-io", root)
        self.assertEqual(helper._scratch, scratch)
        self.assertEqual(helper.list_projects()["projects"], ["original"])

    def test_folder_containing_routing_policy_is_rejected_before_reading_policy(self):
        policy = self.additional / "policy.json"
        policy.write_text("not read during connection", encoding="utf-8")
        helper = self.session(policy_path=policy)
        with self.assertRaisesRegex(Refusal, "routing_policy_inside_source"):
            helper.add_project("policy-source", self.additional)
        self.assertEqual(policy.read_text(encoding="utf-8"), "not read during connection")
        self.assertEqual(helper.list_projects()["projects"], ["original"])

    def test_alias_changed_after_caller_precheck_cannot_register_protected_owner_paths(self):
        helper = self.session()
        private = self.folder("private-state")
        connection = private / "connection.json"
        connection.write_text('{"fixture": "owner-only"}', encoding="utf-8")
        alias = self.base / "selected-folder"
        resolve = Path.resolve

        def changed_alias(path, *args, **kwargs):
            if path == alias and kwargs.get("strict"):
                alias.unlink()
                alias.symlink_to(private, target_is_directory=True)
            return resolve(path, *args, **kwargs)

        for protected in (private, connection):
            with self.subTest(protected=protected):
                if alias.is_symlink():
                    alias.unlink()
                alias.symlink_to(self.additional, target_is_directory=True)
                self.assertEqual(alias.resolve(strict=True), self.additional)
                with patch("shake_bake.helper.Path.resolve", changed_alias):
                    with self.assertRaisesRegex(Refusal, "project_contains_private_settings"):
                        helper.add_project("selected", alias, protected_paths=(protected,))
                self.assertEqual(alias.resolve(strict=True), private)
                self.assertEqual(helper.list_projects()["projects"], ["original"])

    def test_eight_folder_limit_keeps_existing_connections(self):
        helper = self.session()
        for index in range(7):
            helper.add_project("project-" + str(index), self.folder("project-" + str(index)))
        before = helper.list_projects()
        with self.assertRaisesRegex(Refusal, "project_limit_reached"):
            helper.add_project("ninth", self.additional)
        self.assertEqual(helper.list_projects(), before)

    def test_active_task_prevents_connection_without_cancelling_or_replacing_it(self):
        helper = self.session()
        process = Mock()
        process.poll.return_value = None
        with patch("shake_bake.helper.subprocess.Popen", return_value=process):
            identifier = helper.start_task("original", "Find original_value")["task_id"]
        job = helper._jobs[identifier]
        with self.assertRaisesRegex(Refusal, "helper_busy"):
            helper.add_project("additional", self.additional)
        self.assertIs(helper._jobs[identifier], job)
        self.assertEqual(job.state, "RUNNING")
        self.assertEqual(helper.list_projects()["projects"], ["original"])
        process.terminate.assert_not_called()

    def test_closed_session_cannot_gain_project_access(self):
        helper = self.session()
        helper.close()
        with self.assertRaisesRegex(Refusal, "helper_closed"):
            helper.add_project("additional", self.additional)
        self.assertEqual(helper.list_projects()["projects"], ["original"])


if __name__ == "__main__":
    unittest.main()

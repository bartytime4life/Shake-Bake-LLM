"""Synthetic settings, real restarts and source-boundary regressions."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.gui import Controller, DEMO
from shake_bake.preferences import LocalPreferences, default_state_directory


class PreferenceAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.state = self.base / "state"

    def controller(self):
        return Controller({"starter-demo": DEMO}, state_directory=self.state)

    def test_first_launch_paused_and_explicit_on_then_off_survive_restarts(self):
        controller = self.controller()
        try:
            self.assertFalse(controller.call("state")["local_ai_enabled"])
            self.assertTrue(controller.call("settings", {"enabled": True})["persisted"])
        finally:
            controller.close()
        controller = self.controller()
        try:
            self.assertTrue(controller.call("state")["local_ai_enabled"])
            controller.call("settings", {"enabled": False})
        finally:
            controller.close()
        controller = self.controller()
        try:
            state = controller.call("state")
            self.assertFalse(state["local_ai_enabled"])
            self.assertTrue(state["local_ai_preference_persistent"])
            with patch("shake_bake.gui.local_inventory", side_effect=AssertionError("model contacted")):
                self.assertEqual(controller.call("inventory")["state"], "paused")
            self.assertTrue(controller.call("adapter", {"method": "list_projects", "arguments": {},
                                                       "projects": ("starter-demo",)})["local_ai_paused"])
            self.assertEqual(state["recent"], [])
        finally:
            controller.close()
        self.assertEqual(json.loads((self.state / "preferences.json").read_text()),
                         {"schema_version": "1", "local_ai_enabled": False})
        self.assertEqual((self.state.stat().st_mode & 0o777), 0o700)
        self.assertEqual(((self.state / "preferences.json").stat().st_mode & 0o777), 0o600)

    def test_failed_save_pauses_and_reports_failure_instead_of_acknowledging_persistence(self):
        controller = self.controller()
        try:
            controller.call("settings", {"enabled": True})
            with patch.object(controller._preferences, "save", side_effect=Refusal("preferences_not_saved_local_ai_paused")):
                with self.assertRaisesRegex(Refusal, "preferences_not_saved_local_ai_paused"):
                    controller.call("settings", {"enabled": True})
            self.assertFalse(controller.call("state")["local_ai_enabled"])
        finally:
            controller.close()

    def test_atomic_save_failure_preserves_previous_file_and_cleans_temporary_file(self):
        preferences = LocalPreferences(self.state, [DEMO])
        self.addCleanup(preferences.close)
        preferences.save(False)
        before = (self.state / "preferences.json").read_bytes()
        with patch("shake_bake.preferences.os.replace", side_effect=OSError("synthetic failure")):
            with self.assertRaisesRegex(Refusal, "preferences_not_saved"):
                preferences.save(True)
        self.assertEqual((self.state / "preferences.json").read_bytes(), before)
        self.assertFalse(list(self.state.glob(".preferences-*")))

    def test_second_service_cannot_overwrite_the_first_services_choice(self):
        preferences = LocalPreferences(self.state, [DEMO])
        self.addCleanup(preferences.close)
        preferences.save(False)
        with self.assertRaisesRegex(Refusal, "preferences_already_in_use"):
            LocalPreferences(self.state, [DEMO])

    def test_corrupt_or_insecure_saved_state_never_starts_enabled(self):
        preferences = LocalPreferences(self.state, [DEMO])
        preferences.save(False)
        preferences.close()
        for raw in ('{"schema_version":"1","local_ai_enabled":"yes"}',
                    '{"schema_version":"1","local_ai_enabled":false,"local_ai_enabled":true}', 'broken'):
            (self.state / "preferences.json").write_text(raw)
            with self.subTest(raw=raw), self.assertRaises(Refusal):
                self.controller()
        (self.state / "preferences.json").write_text('{"schema_version":"1","local_ai_enabled":true}')
        (self.state / "preferences.json").chmod(0o644)
        with self.assertRaisesRegex(Refusal, "private_0600"):
            self.controller()

    def test_source_directory_and_symlink_targets_are_not_written(self):
        project = self.base / "project"
        project.mkdir()
        with self.assertRaisesRegex(Refusal, "preferences_inside_source"):
            LocalPreferences(project / "state", [project])
        self.assertFalse((project / "state").exists())
        target = self.base / "target"
        target.mkdir(mode=0o700)
        self.state.symlink_to(target, target_is_directory=True)
        with self.assertRaises(Refusal):
            LocalPreferences(self.state, [DEMO])
        self.assertEqual(list(target.iterdir()), [])
        self.state.unlink()
        self.state.mkdir(mode=0o700)
        outside = self.base / "outside.json"
        outside.write_text("owner file")
        (self.state / "preferences.json").symlink_to(outside)
        with self.assertRaises(Refusal):
            LocalPreferences(self.state, [DEMO])
        self.assertEqual(outside.read_text(), "owner file")

    def test_relative_xdg_path_is_refused(self):
        with patch.dict(os.environ, {"XDG_STATE_HOME": "relative"}):
            with self.assertRaisesRegex(Refusal, "absolute_state_directory_required"):
                default_state_directory()


if __name__ == "__main__":
    unittest.main()

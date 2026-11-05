import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from shake_bake.cli import main
from shake_bake.config import Configuration, load_config
from shake_bake.contracts import Refusal


class ConfigAndCliTests(unittest.TestCase):
    def test_offline_demo_and_doctor_are_machine_readable(self):
        for command in ("demo", "doctor"):
            with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main([command]), 0)
                result = json.loads(out.getvalue())
                if command == "demo":
                    self.assertEqual(result["status"], "prepared")
                else:
                    self.assertFalse(result["network_contacted"])

    def test_config_roots_cannot_overlap_state_or_each_other(self):
        for state, projects in (
            ("/tmp/project/state", {"alpha": Path("/tmp/project")}),
            ("/tmp/state", {"alpha": Path("/tmp/state/project")}),
            ("/tmp/state", {"alpha": Path("/tmp/a"), "beta": Path("/tmp/a/b")}),
            ("/tmp/state", {"alpha": Path("/tmp/a"), "beta": Path("/tmp/a")}),
        ):
            with self.subTest(projects=projects), self.assertRaises(Refusal):
                Configuration(Path(state), projects)

    def test_config_unknown_fields_and_parent_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.toml"
            for text in (
                'schema_version = 2\nstate_dir = "state"\n[projects.alpha]\nroot = "project"\n',
                'schema_version = 1\nstate_dir = "state"\nunknown = true\n[projects.alpha]\nroot = "project"\n',
                'schema_version = 1\nstate_dir = "state"\n[projects.alpha]\nroot = "../project"\n',
            ):
                path.write_text(text)
                with self.assertRaises(Refusal):
                    load_config(path)

    def test_cli_prepare_preserves_request_file_and_replays_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "project").mkdir()
            (base / "project" / "file.txt").write_bytes(b"exact\r\n")
            request = base / "request.txt"
            request.write_bytes(b"  exact request\r\n")
            config = base / "config.toml"
            config.write_text('schema_version = 1\nstate_dir = "state"\n[projects.alpha]\nroot = "project"\n')
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = main(["prepare", "--config", str(config), "--project", "alpha", "--request-file", str(request), "--select", "file.txt:1:1"])
            self.assertEqual(code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["packet"]["original_request"], "  exact request\r\n")
            with contextlib.redirect_stdout(io.StringIO()) as replay:
                self.assertEqual(main(["result", "--config", str(config), "--project", "alpha", "--job", result["job_id"]]), 0)
            self.assertEqual(json.loads(replay.getvalue()), result)

    def test_group_readable_state_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "project").mkdir()
            (base / "state").mkdir(mode=0o755)
            config = base / "config.toml"
            config.write_text('schema_version = 1\nstate_dir = "state"\n[projects.alpha]\nroot = "project"\n')
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["result", "--config", str(config), "--project", "alpha", "--job", "missing"]), 2)
            self.assertEqual(json.loads(out.getvalue())["error"]["code"], "state_permissions")

    def test_cli_request_fifo_is_refused_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "project").mkdir()
            os.mkfifo(base / "request")
            config = base / "config.toml"
            config.write_text('schema_version = 1\nstate_dir = "state"\n[projects.alpha]\nroot = "project"\n')
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["prepare", "--config", str(config), "--project", "alpha", "--request-file", str(base / "request"), "--select", "file.txt:1:1"]), 2)
            self.assertEqual(json.loads(out.getvalue())["error"]["code"], "request_file_type")

    def test_symlinked_state_and_state_file_are_refused(self):
        from shake_bake.engine import Engine
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "project").mkdir()
            (base / "target").mkdir(mode=0o700)
            (base / "state").symlink_to(base / "target", target_is_directory=True)
            with self.assertRaises(Refusal):
                Engine(Configuration(base / "state", {"alpha": base / "project"}))
            (base / "state").unlink()
            (base / "state").mkdir(mode=0o700)
            outside = base / "outside"
            outside.write_text("unchanged")
            (base / "state" / "jobs.sqlite3").symlink_to(outside)
            with self.assertRaises(Refusal):
                Engine(Configuration(base / "state", {"alpha": base / "project"}))
            self.assertEqual(outside.read_text(), "unchanged")


if __name__ == "__main__":
    unittest.main()

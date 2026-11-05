import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from shake_bake.cli import main
from shake_bake.collector import MAX_FILE_BYTES, build_packet
from shake_bake.contracts import Refusal, Selection


class BoundaryAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sample.py").write_bytes(b"first\nsecond\n")

    def collect(self, path="sample.py", start=1, end=2):
        return build_packet(self.root, "Inspect selected evidence", (Selection(path, start, end),))

    def test_refuses_absolute_and_parent_paths(self):
        for path in ("../outside.py", str(self.root / "sample.py"), "C:\\secret.txt"):
            with self.subTest(path=path), self.assertRaises(Refusal):
                self.collect(path)

    def test_refuses_secret_paths(self):
        for name in (".env", ".env.production"):
            (self.root / name).write_text("secret", encoding="utf-8")
            with self.subTest(name=name), self.assertRaises(Refusal):
                self.collect(name, end=1)

    def test_refuses_symlink_file_and_directory(self):
        (self.root / "link.py").symlink_to(self.root / "sample.py")
        (self.root / "linkdir").symlink_to(self.root, target_is_directory=True)
        for name in ("link.py", "linkdir/sample.py"):
            with self.subTest(name=name), self.assertRaises(Refusal):
                self.collect(name)

    def test_refuses_oversized_binary_and_invalid_utf8(self):
        for raw in (b"x" * (MAX_FILE_BYTES + 1), b"hello\x00world", b"\xff"):
            (self.root / "input.dat").write_bytes(raw)
            with self.subTest(length=len(raw)), self.assertRaises(Refusal):
                self.collect("input.dat", end=1)

    def test_refuses_unavailable_lines(self):
        for start, end in ((0, 1), (2, 1), (1, 3), (True, 1)):
            with self.subTest(start=start, end=end), self.assertRaises(Refusal):
                self.collect(start=start, end=end)

    def test_changed_source_changes_evidence_identity(self):
        before = self.collect()
        (self.root / "sample.py").write_bytes(b"first\nchanged\n")
        after = self.collect()
        self.assertNotEqual(before.snapshot_id, after.snapshot_id)
        self.assertNotEqual(before.evidence[0].file_sha256, after.evidence[0].file_sha256)

    def test_cli_refuses_without_leaking_host_paths(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--root", str(self.root), "--task", "Inspect", "--file", "../outside", "--start-line", "1", "--end-line", "1"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue()), {"outcome": "DENY", "code": "path_not_allowed"})


if __name__ == "__main__":
    unittest.main()

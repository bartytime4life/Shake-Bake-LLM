"""The first acceptance gate: exact evidence, unchanged intent, no side effects."""

import hashlib
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.collector import build_packet
from shake_bake.contracts import Selection


def content_snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): (p.stat().st_mode, hashlib.sha256(p.read_bytes()).hexdigest())
            for p in root.rglob("*") if p.is_file()}


class FirstAcceptance(unittest.TestCase):
    def test_prepares_exact_evidence_offline_without_touching_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src" / "coverage.py"
            source.parent.mkdir()
            # Inert synthetic review fixture created for this acceptance test.
            raw = b"def validate_structure(slices, detected):\r\n    return len(slices) <= detected\r\n"
            source.write_bytes(raw)
            original = " Review coverage.\nPreserve uncertainty; do not declare this code safe. "
            before = content_snapshot(root)
            with patch.object(socket.socket, "connect", side_effect=AssertionError("network attempted")) as connect, \
                 patch.object(socket.socket, "connect_ex", side_effect=AssertionError("network attempted")) as connect_ex, \
                 patch.object(socket, "create_connection", side_effect=AssertionError("network attempted")) as connection, \
                 patch.object(subprocess, "Popen", side_effect=AssertionError("process attempted")) as process:
                packet = build_packet(root, original, (Selection("src/coverage.py", 1, 2),))
                again = build_packet(root, original, (Selection("src/coverage.py", 1, 2),))
            self.assertEqual(packet.original_request, original)
            self.assertEqual(packet.evidence[0].text.encode("utf-8"), raw)
            self.assertEqual(packet.evidence[0].file_sha256, hashlib.sha256(raw).hexdigest())
            self.assertEqual(packet.evidence[0].path, "src/coverage.py")
            self.assertEqual((packet.evidence[0].start_line, packet.evidence[0].end_line), (1, 2))
            self.assertEqual(packet.snapshot_scope, "selected-files-only")
            self.assertEqual(packet.kind, "source_excerpt_packet")
            self.assertEqual(packet, again)
            self.assertEqual(content_snapshot(root), before)
            self.assertTrue(any("no code-review" in s for s in packet.limitations))
            for mocked in (connect, connect_ex, connection, process):
                mocked.assert_not_called()


if __name__ == "__main__":
    unittest.main()

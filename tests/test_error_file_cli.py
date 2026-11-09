"""A selected error file must not turn a read-only CLI check into a pipe wait."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ErrorFileCLITests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX named pipe required")
    def test_named_pipe_is_refused_without_waiting_for_a_writer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pipe = root / "error.log"
            os.mkfifo(pipe)
            result = subprocess.run([sys.executable, "-B", "-m", "shake_bake", "diagnose",
                                     "--root", str(root), "--error-file", str(pipe)],
                                    capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["code"], "regular_error_file_required")


if __name__ == "__main__":
    unittest.main()

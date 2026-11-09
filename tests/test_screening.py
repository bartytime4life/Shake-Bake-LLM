import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from shake_bake.cli import main
from shake_bake.screening import scan, warning_lines
from shake_bake.search import prepare

# Synthetic credential shapes, assembled at runtime so no file holds a literal token.
AWS = "AKIA" + "Q7" * 8
GITHUB = "gh" + "p_" + "a1B2" * 9
SLACK = "xo" + "xb-" + "1234567890-abcdefghij"
GOOGLE = "AI" + "za" + "S" * 35
STRIPE = "sk" + "_live_" + "4eC39HqLyjWDarjtT1zdp7dc"
ANTHROPIC = "sk-" + "ant-" + "api03-" + "x" * 30
JWT = "ey" + "JhbGciOiJIUzI1NiJ9" + "." + "ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0" + "." + "dozjgNryP4J3jVmNHl0w5N"
KEY = "-----BEGIN " + "RSA PRIVATE KEY-----"


class Patterns(unittest.TestCase):
    def test_credential_shapes_are_found_with_masked_previews(self):
        text = "\n".join([f"aws = '{AWS}'", f"token: {GITHUB}", SLACK, GOOGLE, STRIPE, ANTHROPIC, JWT, KEY,
                          'DB_PASSWORD = "hunter2-correct-horse"'])
        found = scan(text)
        self.assertEqual([kind for kind, _, _ in found], ["private key", "AWS access key ID", "GitHub token", "Slack token",
                                                         "Google API key", "Stripe live key", "Anthropic API key",
                                                         "JSON web token", "password or secret literal"])
        self.assertEqual([line for _, line, _ in found], [8, 1, 2, 3, 4, 5, 6, 7, 9])
        for secret in (AWS, GITHUB, SLACK, GOOGLE, STRIPE, ANTHROPIC, JWT, "hunter2-correct-horse"):
            self.assertFalse(any(secret in preview for _, _, preview in found), "a preview never holds the secret")
        self.assertIn(("AWS access key ID", 1, AWS[:4] + "… (20 characters)"), found)

    def test_placeholders_and_ordinary_code_are_not_flagged(self):
        text = "\n".join(['password = "changeme"', 'api_key = "${API_KEY}"', "secret = '<your secret here>'",
                          'password = "xxxxxxxx"', "token = get_token(user)", "import sklearn  # sk-learn",
                          'client_secret = "example-value"', "AKIA is the prefix of an AWS key ID"])
        self.assertEqual(scan(text), [])

    def test_warning_lines_name_the_place_and_are_empty_without_findings(self):
        self.assertEqual(warning_lines([]), [])
        lines = warning_lines([{"kind": "GitHub token", "where": "E2", "path": "app/settings.py", "line": 14, "preview": "ghp_… (40 characters)"}])
        self.assertIn("(1 found)", lines[0])
        self.assertEqual(lines[1], "- GitHub token in E2 app/settings.py line 14: ghp_… (40 characters)")


class Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = f"# deploy settings\n\nDEPLOY_REGION = 'eu'\nDEPLOY_KEY_ID = '{AWS}'\n"
        (self.root / "deploy_settings.py").write_text(self.source, encoding="utf-8")
        self.task = "Why does DEPLOY_REGION default to eu?"

    def test_prepare_reports_findings_and_keeps_the_exact_source(self):
        result = prepare(self.root, self.task)
        self.assertEqual(result.packet.evidence[0].text, self.source, "exact evidence is unchanged")
        self.assertEqual(list(result.screening), [{"kind": "AWS access key ID", "where": "E1", "path": "deploy_settings.py",
                                                   "line": 4, "preview": AWS[:4] + "… (20 characters)"}])
        self.assertEqual(prepare(self.root, "Why does DEPLOY_REGION default to eu? " + AWS).screening[0]["where"], "request")

    def test_cli_warns_on_stderr_and_leaves_the_brief_untouched(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["brief", "--root", str(self.root), "--task", self.task])
        self.assertEqual(code, 0)
        self.assertIn(AWS, out.getvalue(), "the brief keeps the exact source")
        self.assertNotIn("Possible credentials", out.getvalue())
        self.assertIn("Possible credentials in what this brief would share (1 found)", err.getvalue())
        self.assertIn("- AWS access key ID in E1 deploy_settings.py line 4:", err.getvalue())
        self.assertNotIn(AWS, err.getvalue())

    def test_clean_source_produces_no_warning(self):
        (self.root / "deploy_settings.py").write_text("DEPLOY_REGION = 'eu'\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            main(["brief", "--root", str(self.root), "--task", self.task])
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(prepare(self.root, self.task).screening, ())


class FailureReports(unittest.TestCase):
    def test_failure_reports_carry_masked_findings_and_keep_exact_text(self):
        from shake_bake.troubleshoot import locate_failure
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = f"import os\nTOKEN = '{GITHUB}'\nraise SystemExit(os.environ['MISSING'])\n"
            (root / "app.py").write_text(source, encoding="utf-8")
            error = ('Traceback (most recent call last):\n  File "app.py", line 3, in <module>\n'
                     "    raise SystemExit(os.environ['MISSING'])\nKeyError: 'MISSING'\n"
                     f"request failed: https://api.example.invalid/v1?key={GOOGLE}\n")
            report = locate_failure(root, error, f"STRIPE={STRIPE} python3 app.py")
            self.assertEqual(report["error_output"], error, "the pasted output is unchanged")
            self.assertEqual([(f["kind"], f["where"], f["path"], f["line"]) for f in report["screening"]],
                             [("Stripe live key", "recorded command", None, 1), ("Google API key", "original error output", None, 5),
                              ("GitHub token", "E1", "app.py", 2)])
            self.assertNotIn(GITHUB, json.dumps(report["screening"]))
            (root / "err.txt").write_text(error, encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                main(["diagnose", "--root", str(root), "--error-file", str(root / "err.txt")])
            self.assertIn("Possible credentials in what this report would share (2 found)", err.getvalue())
            self.assertNotIn(GOOGLE, err.getvalue())
            self.assertEqual(json.loads(out.getvalue())["error_output"], error)

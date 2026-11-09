# Failed-run source checks

The workbench starts with a concrete job: match a pasted Python failure to current local source. It preserves the original output and optional command, locates exact traceback paths inside the selected folder, and compares the reported statement with the current source line. It reports chained exceptions, missing files, source mismatches and bounded next checks for common errors such as missing modules, syntax errors and missing files.

This is deterministic source inspection. No model, project import, failing command, test, installation or repair runs. Finding a line does not prove a root cause. A fix still needs implementation and validation in the appropriate environment. Container paths and paths from another machine must match the connected root; there is no basename guessing or automatic path mapping.

**Connect project folder** approves an existing absolute directory for this browser service session. It is available to both browser workflows and disappears on service restart. It does not expand an existing assistant adapter's project scope. Broad roots, duplicate folders, helper scratch and private service settings are refused. Reading source remains confined to the selected root, with existing sensitive-file and symlink refusals.

The error is limited to 64 KiB of UTF-8, and the optional command to 4 KiB. Oversized input is refused without truncation. The report keeps at most twenty inner frames, ten source windows and 16 KiB of excerpts. Missing or excluded evidence and cutoffs remain visible. Server work runs in a trusted, time-limited child outside the source folder. Errors and reports are not added to saved drafts or recent briefs; exports include their exact contents.

For a saved error file, the same locator is available from the command line:

```bash
PYTHONPATH=src python3.12 -B -m shake_bake diagnose \
  --root /absolute/project/folder \
  --error-file /absolute/path/to/error.txt \
  --command 'python3 main.py'
```

It prints JSON. Exit status `0` means source was located, `3` means no source was located, and `2` means the request was refused. None means the bug has been fixed. Use UTF-8 input and keep private error files outside inspected source if they should not be included in future briefs.

Committed verification uses disposable synthetic source and Python errors. It covers exact line matching, source changes, chained errors, path confinement, input limits, real HTTP and browser exports. Those checks verify workflow mechanics; no private-project failure or general diagnostic accuracy is claimed.

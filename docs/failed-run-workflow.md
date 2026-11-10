# Failed-run source checks

The workbench starts with a concrete job: match a pasted Python, Node.js or TypeScript failure to current local source. It preserves the original output and optional command, locates exact reported paths inside the selected folder, and compares Python traceback statements with current source. Node.js and TypeScript provide reported line/column locations; they do not prove the source statement matches the failed run. It reports Python chained exceptions, missing files, source mismatches and bounded next checks for common errors such as missing modules, syntax errors and missing files.

This is deterministic source inspection. No model, project import, failing command, test, installation or repair runs. Finding a line does not prove a root cause. A fix still needs implementation and validation in the appropriate environment. Source-map lookups and browser-URL fetching are not performed. Container paths and paths from another machine must match the connected root; there is no basename guessing or automatic path mapping.

Logs may contain several independent Python tracebacks, such as multiple failed tests or retries. Their source stays separate: the main result uses only a location belonging to the final traceback. Earlier source is retained in matching details, and an unlocated or truncated final traceback stays incomplete. Explicit cause and handling relationships are retained only when the output contains those markers.

Only one automatic browser clipboard write may be pending across both workflows in this tab. A delayed write keeps Copy disabled until it settles, even after edits or a new result. Manual review and exports remain available; late completion still identifies the older capture.

**Load error file** reads a local UTF-8 text/log file up to 64 KiB into this tab. It does not send a request until **Find failing source**. Original BOM and line endings are kept separately from the textarea display; editing the error discards that original buffer and uses the edited text. Invalid, oversized or delayed file reads cannot overwrite newer input. Loaded errors are not saved as browser drafts.

**Connect project folder** approves an existing absolute directory for this browser service session. The shared control is visible in both workflows and selects the new folder only for the initiating workflow, preserving later selection changes. The connection disappears on service restart. It does not expand an existing assistant adapter's project scope. Broad roots, duplicate folders, helper scratch and private service settings are refused. Reading source remains confined to the selected root, with existing sensitive-file and symlink refusals.

Python terminal colors are removed only in the matching copy. JavaScript source line counts include Unicode line/paragraph separators; Python line counts do not. Exact source remains unchanged.

Node.js V8 frames are read in innermost-first order; TypeScript diagnostics keep compiler order. The first readable diagnostic is bound to its own message even when earlier errors are outside the project. Local `file:` URLs are decoded; remote hosts, runtime internals and unsupported schemes remain unread. The reported column is displayed, without asserting that it matches current source. The original path spelling is retained in the report. Node.js nested `cause` stacks keep their own messages. For a supported unexpected-end-of-input syntax diagnostic, a reported line immediately after the last newline captures labelled preceding context; the reported line number remains unchanged.

Launch-time root symlinks are canonicalized once. State and reports show that validated root; a traceback using the original alias spelling is deliberately refused rather than following an alias that may have changed. Relative and canonical absolute paths work.

**Copy debugging brief** creates a fenced handoff with the captured project, recorded command, exact error, source, hashes, unmatched frames and limits. A manual text fallback appears if clipboard access fails. Changing the input/project marks the result outdated and disables copy/export; late network or clipboard responses cannot label a newer input as complete. Possible credential formats in the error, command, captured source and project details appear as a masked warning above the copy action. Screening warns without changing exact contents or automatically sending anything; review the content before sharing. No findings is not a guarantee that nothing private is present. The receiving assistant still needs to investigate and verify a fix.

The error is limited to 64 KiB of UTF-8, and the optional command to 4 KiB. Oversized input is refused without truncation. The report keeps at most twenty inner frames, ten source windows and 16 KiB of excerpts. Missing or excluded evidence and cutoffs remain visible. Server work runs in a trusted, time-limited child outside the source folder. Errors and reports are not added to saved drafts or recent briefs; exports include their exact contents.

For a saved error file, the same locator is available from the command line:

```bash
PYTHONPATH=src python3.12 -B -m shake_bake diagnose \
  --root /absolute/project/folder \
  --error-file /absolute/path/to/error.txt \
  --command 'python3 main.py'
```

The CLI accepts a regular UTF-8 error file; named pipes are refused rather than waited on. It prints JSON. Exit status `0` means source was located, `3` means no source was located, and `2` means the request was refused. None means the bug has been fixed. Use UTF-8 input and keep private error files outside inspected source if they should not be included in future briefs.



Text exports use the same complete debugging brief as the copy action, including every captured excerpt, unmatched frame, source comparison and cutoff. An earlier-chain-only match remains incomplete for the final failure. JSON retains the structured original text and hashes.

Known format gaps: pytest's default decorated failure output, Python ExceptionGroup tree traces and arbitrary log prefixes are not parsed as full traceback formats. Unsupported output is kept as supplied and does not establish a source location or cause. Generated Node.js fixtures and synthetic browser/HTTP cases verify the supported mechanics; no private-project diagnosis or repair success is claimed.

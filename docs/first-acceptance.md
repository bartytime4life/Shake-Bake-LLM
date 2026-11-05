# First acceptance gate

Test: `FirstAcceptance.test_prepares_exact_evidence_offline_without_touching_repo`.

## Scenario

Create a temporary project containing two inert synthetic source lines with CRLF endings. Supply a review request containing leading/trailing whitespace and a newline. Select exactly those two source lines. Build the packet twice.

## Required result

1. The original request is preserved exactly.
2. The excerpt round-trips to the original source bytes, including line endings.
3. Relative path, line range and full-file SHA-256 match the selected source.
4. The packet identifies its scope as selected files only.
5. Both runs return the same evidence packet.
6. The temporary project's file names, contents and modes are unchanged.
7. Patched Python network connection methods and subprocess creation are never called.
8. The packet explicitly says that collection produced no code-review or safety conclusion.

Run from the project root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p test_first_acceptance.py -v
```

Expected result: one test passes. The original eight tests remain in the expanded 35-test suite, which passed in the development environment on November 4, 2026.

## What remains unproven

The test does not evaluate an LLM, find the intentional source defect, enforce a network sandbox, measure cloud savings or qualify a physical owner PC. The fixture is synthetic; real-project accuracy trials remain pending. Linux is the initial target; Windows admission is deliberately refused until separately implemented and qualified.

Evidence selection is implemented in version 0.2. Keep the code-review answer key separate from worker inputs in future blind evaluations; the recorded known-symbol retrieval smoke is not a blind review.

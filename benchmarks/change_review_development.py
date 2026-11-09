"""Exposed synthetic packet-coverage check for the change-review candidate.

This does not invoke a model or host, grade a final answer or measure savings.
"""

import difflib
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import time

from shake_bake.change_review import prepare_change_review
from shake_bake.search import prepare


def inventory(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> None:
    generator = runpy.run_path(str(Path(__file__).with_name("native-preparation") / "generate.py"))
    with tempfile.TemporaryDirectory(prefix="sb-change-review-development-") as directory:
        generator["generate"](Path(directory) / "dataset")
        root = Path(directory) / "dataset" / "fixtures" / "publish-reorder"
        old = (root / "before/publish.py").read_text(encoding="utf-8")
        new = (root / "after/publish.py").read_text(encoding="utf-8")
        # Prior-version bytes are evaluation input, outside the inspected current root.
        (root / "before/publish.py").unlink()
        diff = "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                            fromfile="a/after/publish.py", tofile="b/after/publish.py"))
        task = ("Review the pinned publish reorder against its journal and notification "
                "contracts, callers, and existing tests. State unknowns.")
        before = inventory(root)
        started = time.monotonic()
        generic = prepare(root, task)
        generic_seconds = time.monotonic() - started
        started = time.monotonic()
        focused = prepare_change_review(root, task, "after/publish.py", diff)
        focused_seconds = time.monotonic() - started
        after = inventory(root)
        assert before == after, "Preparation changed the synthetic project"
        anchors = {
            "after/publish.py": "notifications.send(payload)\n    receipt = journal.commit(payload)",
            "core/journal.py": "raise RuntimeError('journal_quota_exceeded')",
            "core/notifications.py": "self.delivered.append(payload)",
            "docs/contract.md": "Notifications must not be accepted",
            "tests/test_publish.py": "journal = Journal(quota=2)",
        }
        generic_text = {path: "".join(e.text for e in generic.packet.evidence if e.path == path)
                        for path in anchors} if generic.packet else {}
        focused_evidence = (*focused.changed_source.evidence, *(focused.context.evidence if focused.context else ()))
        focused_text = {path: "".join(e.text for e in focused_evidence if e.path == path) for path in anchors}
        generic_found = sorted(path for path, anchor in anchors.items() if anchor in generic_text.get(path, ""))
        focused_found = sorted(path for path, anchor in anchors.items() if anchor in focused_text.get(path, ""))
        assert focused_found == sorted(anchors), "Focused packet missed a development anchor"
        print(json.dumps({
            "kind": "exposed_change_review_packet_check",
            "fixture_sha256": before,
            "fixture_files": len([path for path in root.rglob("*") if path.is_file()]),
            "diff_sha256": focused.diff_sha256,
            "generic": {"anchor_paths": generic_found, "selected_paths": [e.path for e in generic.packet.evidence] if generic.packet else [],
                        "cutoffs": generic.cutoffs, "seconds": round(generic_seconds, 6)},
            "focused": {"anchor_paths": focused_found, "selected_paths": [e.path for e in focused_evidence],
                        "cutoffs": focused.cutoffs, "missing_candidate_roles": focused.missing_context_roles,
                        "seconds": round(focused_seconds, 6)},
            "source_unchanged": True,
            "model_or_host_calls": 0,
            "semantic_accuracy": None,
            "whole_task_savings": None,
            "warning": "Exposed synthetic packet coverage only; inputs and roles differ from a paired host comparison.",
        }, indent=2))


if __name__ == "__main__":
    main()

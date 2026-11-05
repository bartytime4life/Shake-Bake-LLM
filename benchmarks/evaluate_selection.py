"""A retrieval smoke evaluation, not an LLM review or cloud-savings benchmark."""

import json
from pathlib import Path
import tempfile
import time

from shake_bake.search import prepare


def main():
    cases = []
    for operator in ("<=", "=="):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "validator.py").write_text(
                "# executable slice coverage\ndef validate_structure(slices, detected):\n"
                f"    return len(slices) {operator} detected\n", encoding="utf-8")
            (root / "unrelated.py").write_text("rainbow = 42\n", encoding="utf-8")
            started = time.monotonic()
            result = prepare(root, "Find executable slice coverage")
            paths = [e.path for e in result.packet.evidence] if result.packet else []
            cases.append({"variant": operator, "selected": paths, "expected_source_found": paths == ["validator.py"],
                          "seconds": round(time.monotonic() - started, 6), "excerpt_bytes": result.selected_excerpt_bytes})
    receipt = {"kind": "synthetic_retrieval_smoke", "cases": cases,
               "all_expected_sources_found": all(c["expected_source_found"] for c in cases),
               "code_review_accuracy": None, "cloud_tokens": None, "token_savings": None}
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["all_expected_sources_found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

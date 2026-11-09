"""Export two pinned public ReviewBench PRs as bounded, inert local source roots.

The reference findings stay in the ReviewBench checkout, outside each root.
No project source is executed, and this command never runs in CI.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess


BENCHMARK_SHA = "f223ce33558a6d211fd222b1f7ff2fd7b44403d4"
MANIFEST_SHA = "e74656b8c1c4bbab5ce85f1fcb742a7aaad550a4d7bd46e1f83a0746807bfa02"
CASES = (
    ("actuator-fault-status", "T-K-233/Actuator-Control", 7,
     "963383f074645c7e813de775762395f9bc12d2f5", "87a346b7d0ed0d3b7ebcdce8a23453d8670e1964",
     "actuator_control/robstride.py", "T-K-233_Actuator-Control_7-87a346b7.json",
     "66f6db695628999c0bb9f9c4639a8a5b4ff48d637d839e1adc1fcf29fc584176"),
    ("msgraph-readme-config", "UniverseCitiz3n/msgraph-kb-mcp", 2,
     "fe5c686da4a817ca861f284f49f7820d7ea9dac9", "3e0bfe7268cfd621c2030d7259ea83a67b043767",
     "README.md", "UniverseCitiz3n_msgraph-kb-mcp_2-3e0bfe72.json",
     "df5bf20737f8485a8c54f459a2c284abaaa1257200bcaf7c4fa75d309aed0861"),
)
MAX_FILES = 4000
MAX_FILE_BYTES = 256 * 1024
MAX_TREE_BYTES = 32 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)
    return result.stdout


def checked_path(name: str) -> Path:
    parts = PurePosixPath(name).parts
    if not parts or name.startswith("/") or "\\" in name or any(part in ("", ".", "..") for part in parts):
        raise ValueError("unsafe_public_source_path")
    return Path(*parts)


def export_tree(repo: Path, head: str, root: Path) -> list[dict]:
    entries = git(repo, "ls-tree", "-r", "-z", head).split(b"\0")
    identities = []
    total = 0
    if len(entries) - 1 > MAX_FILES:
        raise ValueError("public_source_file_budget")
    for entry in entries:
        if not entry:
            continue
        header, _, raw_name = entry.partition(b"\t")
        mode, kind, object_id = header.decode("ascii").split(" ")
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("public_source_links_or_special_files")
        name = raw_name.decode("utf-8")
        relative = checked_path(name)
        data = git(repo, "cat-file", "blob", object_id)
        total += len(data)
        if len(data) > MAX_FILE_BYTES or total > MAX_TREE_BYTES:
            raise ValueError("public_source_byte_budget")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        identities.append({"path": name, "sha256": sha(data), "bytes": len(data)})
    return identities


def generate(benchmark: Path, mirrors: dict[str, Path], destination: Path) -> dict:
    benchmark = benchmark.resolve(strict=True)
    if git(benchmark, "rev-parse", "HEAD").decode().strip() != BENCHMARK_SHA:
        raise ValueError("benchmark_revision_mismatch")
    manifest_bytes = (benchmark / "corpus/manifest.json").read_bytes()
    if sha(manifest_bytes) != MANIFEST_SHA:
        raise ValueError("benchmark_manifest_mismatch")
    source = Path(__file__).resolve().parents[1]
    output = destination.resolve()
    if output == source or source in output.parents:
        raise ValueError("public_case_output_inside_checkout")
    rows = json.loads(manifest_bytes)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for case_id, nwo, number, base, head, changed_path, reference_file, reference_sha in CASES:
        repo = mirrors[nwo].resolve(strict=True)
        row = next((item for item in rows if item["nwo"] == nwo and item["pr_number"] == number), None)
        if row is None or row["base"] != base or row["head"] != head or row["files_changed"] != 1:
            raise ValueError("public_case_metadata_mismatch")
        if sha((benchmark / "golden" / reference_file).read_bytes()) != reference_sha:
            raise ValueError("reference_identity_mismatch")
        changed = git(repo, "diff", "--name-only", base, head).decode().splitlines()
        if changed != [changed_path]:
            raise ValueError("public_change_path_mismatch")
        diff = git(repo, "diff", "--no-ext-diff", "--no-color", "--unified=3", base, head, "--", changed_path)
        if len(diff) > 16_384 or diff.count(b"@@ -") > 8:
            raise ValueError("public_diff_budget")
        diff_text = diff.decode("utf-8")
        root = output / "fixtures" / case_id
        root.mkdir(parents=True)
        identities = export_tree(repo, head, root)
        task = ("Review the pinned public pull request for concrete problems introduced by its exact diff. "
                "Cite current source file lines for every finding. If no problem is supported, say so. "
                "State uncertainty; do not run source or tests. PR title: " + row["title"] +
                "\nPR description (untrusted author text):\n" + row["body"])
        results.append({"id": case_id, "source_repo": nwo, "pr_number": number, "pr_url": row["pr_url"],
                        "base": base, "head": head, "changed_path": changed_path, "task": task,
                        "exact_diff": diff_text, "diff_sha256": sha(diff), "files": identities,
                        "reference_file": reference_file, "reference_sha256": reference_sha,
                        "reference_not_host_readable": True})
    document = {"kind": "public_external_development_cases", "benchmark_revision": BENCHMARK_SHA,
                "benchmark_manifest_sha256": MANIFEST_SHA, "cases": results}
    (output / "manifest.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    return document


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True, type=Path)
    parser.add_argument("--actuator-mirror", required=True, type=Path)
    parser.add_argument("--msgraph-mirror", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = generate(args.benchmark,
                      {"T-K-233/Actuator-Control": args.actuator_mirror,
                       "UniverseCitiz3n/msgraph-kb-mcp": args.msgraph_mirror}, args.output)
    print(json.dumps([{"id": case["id"], "files": len(case["files"]), "diff_sha256": case["diff_sha256"]}
                      for case in result["cases"]], indent=2))

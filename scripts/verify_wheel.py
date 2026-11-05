"""Verify recovered code/assets, legal notices and dependency metadata in a wheel."""

from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile
import tomllib

root = Path(__file__).resolve().parent.parent
version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
wheels = list((root / "dist").glob(f"shake_and_bake_assistant-{version}-*.whl"))
assert len(wheels) == 1, "Build exactly one wheel for the current package version."
with ZipFile(wheels[0]) as archive:
    names = archive.namelist()
    source = root / "src"
    expected = {p.relative_to(source).as_posix(): p.read_bytes()
                for p in (source / "shake_bake").rglob("*")
                if p.is_file() and "__pycache__" not in p.parts}
    packaged = {p for p in names if p.startswith("shake_bake/") and not p.endswith("/")}
    assert packaged == set(expected), (packaged - set(expected), set(expected) - packaged)
    for path, data in expected.items():
        assert archive.read(path) == data, path
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "MODEL_LICENSES.json"):
        matches = [p for p in names if p.endswith("/licenses/" + name)]
        assert len(matches) == 1, (name, matches)
        assert archive.read(matches[0]) == (root / name).read_bytes(), name
    metadata_name, = [p for p in names if p.endswith(".dist-info/METADATA")]
    metadata = BytesParser().parsebytes(archive.read(metadata_name))
    assert metadata["Name"] == "shake-and-bake-assistant"
    assert metadata["Version"] == version
    assert metadata["License-Expression"] == "MIT"
    requirements = metadata.get_all("Requires-Dist", [])
    assert len(requirements) == 1 and requirements[0].startswith("mcp") and 'extra == "mcp"' in requirements[0], requirements
print("Wheel code, demo/web assets and all three legal files match source bytes; no core runtime dependencies.")

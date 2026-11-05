"""Check that legal notices and the inert demo ship unchanged in the wheel."""

from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parent.parent
wheels = list((root / "dist").glob("*.whl"))
assert len(wheels) == 1, "Use a clean dist directory with exactly one candidate wheel."
with ZipFile(wheels[0]) as archive:
    names = archive.namelist()
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        match = [item for item in names if item.endswith("/licenses/" + name)]
        assert len(match) == 1, (name, match)
        assert archive.read(match[0]) == (root / name).read_bytes(), name
    assert archive.read("shake_bake/fixtures/example.txt") == (root / "src/shake_bake/fixtures/example.txt").read_bytes()
print("Wheel notices and inert fixture match source bytes.")

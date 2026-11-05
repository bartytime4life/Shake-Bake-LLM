"""Check that legal notices and the inert demo ship unchanged in the wheel."""

from pathlib import Path
from zipfile import ZipFile
import tomllib

root = Path(__file__).resolve().parent.parent
version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
wheels = list((root / "dist").glob(f"shake_and_bake-{version}-*.whl"))
assert len(wheels) == 1, "Build exactly one candidate wheel for the current package version."
with ZipFile(wheels[0]) as archive:
    names = archive.namelist()
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        match = [item for item in names if item.endswith("/licenses/" + name)]
        assert len(match) == 1, (name, match)
        assert archive.read(match[0]) == (root / name).read_bytes(), name
    for name in ("example.txt", "startup.py", "startup.log"):
        fixture = root / "src/shake_bake/fixtures" / name
        assert archive.read(f"shake_bake/fixtures/{name}") == fixture.read_bytes(), name
    for path in (root / "src/shake_bake/web").rglob("*"):
        if path.is_file():
            assert archive.read(path.relative_to(root / "src").as_posix()) == path.read_bytes(), path
print("Wheel notices, all inert fixtures and every GUI asset match source bytes.")

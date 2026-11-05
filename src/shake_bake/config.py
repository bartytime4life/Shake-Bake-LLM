"""Explicit project registration. Never infer project roots from model output."""

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

from .contracts import Refusal, check_project_id


@dataclass(frozen=True)
class Configuration:
    state_dir: Path
    projects: dict[str, Path]

    def __post_init__(self):
        if not 1 <= len(self.projects) <= 16:
            raise Refusal("invalid_config", "Register between one and sixteen projects.")
        state = Path(os.path.abspath(self.state_dir))
        roots = []
        for project_id, value in self.projects.items():
            check_project_id(project_id)
            root = Path(os.path.abspath(value))
            if root == Path("/") or state == root or root in state.parents:
                raise Refusal("state_inside_project", "The private state directory must be outside every inspected project.")
            if state in root.parents:
                raise Refusal("project_inside_state", "An inspected project cannot be inside the private state directory.")
            if any(root == old or root in old.parents or old in root.parents for old in roots):
                raise Refusal("overlapping_projects", "Project roots must be distinct and must not overlap.")
            roots.append(root)


def load_config(path: Path) -> Configuration:
    try:
        if path.stat().st_size > 64 * 1024:
            raise Refusal("invalid_config", "The configuration exceeds 64 KiB.")
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        raise Refusal("invalid_config", "The configuration must be a readable UTF-8 TOML file.") from None
    if set(document) != {"schema_version", "state_dir", "projects"} or type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise Refusal("invalid_config", "Configuration requires schema_version = 1, state_dir and projects only.")
    def location(value):
        if not isinstance(value, str) or not value or ".." in Path(value).parts:
            raise Refusal("invalid_config", "Configuration paths must be nonempty and contain no parent traversal.")
        candidate = Path(value).expanduser()
        return candidate if candidate.is_absolute() else path.absolute().parent / candidate
    projects = document["projects"]
    if not isinstance(projects, dict):
        raise Refusal("invalid_config", "projects must be a table of project IDs and roots.")
    parsed = {}
    for key, value in projects.items():
        if not isinstance(value, dict) or set(value) != {"root"}:
            raise Refusal("invalid_config", "Each project table requires a root only.")
        parsed[key] = location(value["root"])
    return Configuration(location(document["state_dir"]), parsed)

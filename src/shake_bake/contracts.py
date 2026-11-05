"""Immutable evidence records; no model-generated facts are marked verified."""

from dataclasses import asdict, dataclass
from typing import Literal


class Refusal(ValueError):
    """A bounded, machine-readable refusal without host-path disclosure."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Selection:
    path: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Evidence:
    path: str
    start_line: int
    end_line: int
    text: str
    file_sha256: str
    excerpt_sha256: str
    size_bytes: int


@dataclass(frozen=True)
class Packet:
    schema_version: str
    outcome: Literal["ANSWER"]
    kind: str
    original_request: str
    snapshot_scope: str
    snapshot_id: str
    evidence: tuple[Evidence, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)

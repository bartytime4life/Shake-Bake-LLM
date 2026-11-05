"""Small immutable contracts shared by the collector, coordinator and CLI."""

from dataclasses import asdict, dataclass
import re

MAX_FILES = 4
MAX_FILE_BYTES = 256 * 1024
MAX_EXCERPT_BYTES = 32 * 1024
MAX_LINES = 200
MAX_REQUEST_BYTES = 16 * 1024
MAX_JOBS = 1000
MAX_JOB_SECONDS = 30
SCHEMA_VERSION = 1


class Refusal(ValueError):
    """A stable error code and safe explanation, without source contents."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": str(self)}


@dataclass(frozen=True)
class Selection:
    path: str
    start_line: int
    end_line: int

    def __post_init__(self):
        try:
            valid_path = isinstance(self.path, str) and 1 <= len(self.path.encode("utf-8")) <= 1024
        except UnicodeError:
            valid_path = False
        if not valid_path:
            raise Refusal("invalid_path", "A selection needs a bounded relative file path.")
        if type(self.start_line) is not int or type(self.end_line) is not int:
            raise Refusal("invalid_range", "Line numbers must be integers.")
        if not 1 <= self.start_line <= self.end_line or self.end_line - self.start_line + 1 > MAX_LINES:
            raise Refusal("invalid_range", f"Select 1 to {MAX_LINES} lines using one-based inclusive numbers.")

    @classmethod
    def from_dict(cls, value: dict):
        if not isinstance(value, dict) or set(value) != {"path", "start_line", "end_line"}:
            raise Refusal("invalid_selection", "Each selection requires path, start_line and end_line only.")
        return cls(**value)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    path: str
    start_line: int
    end_line: int
    file_sha256: str
    excerpt_sha256: str
    file_bytes: int
    excerpt_bytes: int
    content: str

    def to_dict(self):
        return asdict(self)


def check_project_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", value):
        raise Refusal("invalid_project", "Use a configured project ID containing lowercase letters, digits, _ or -.")
    return value


def check_request(value: str) -> str:
    try:
        valid = isinstance(value, str) and bool(value.strip()) and len(value.encode("utf-8")) <= MAX_REQUEST_BYTES
    except UnicodeError:
        valid = False
    if not valid:
        raise Refusal("invalid_request", f"The original request must contain text and fit in {MAX_REQUEST_BYTES} UTF-8 bytes.")
    return value

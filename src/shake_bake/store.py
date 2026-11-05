"""Private SQLite receipts and atomic terminal transitions; no global project cache."""

from datetime import datetime, timezone
try:
    import fcntl
except ImportError:  # require_posix provides a clear refusal before Store is used.
    fcntl = None
import json
import os
from pathlib import Path
import sqlite3
import stat
import threading
import uuid

from .contracts import MAX_JOBS, Refusal
from .policy import _open_directory


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def private_directory(path: Path):
    path = Path(os.path.abspath(path))
    # Existing ancestors may not be symlinks. Create missing components explicitly.
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        if current == current.parent:
            break
        current = current.parent
    fd = _open_directory(current)
    os.close(fd)
    for item in reversed(missing):
        item.mkdir(mode=0o700)
    fd = _open_directory(path)
    try:
        st = os.fstat(fd)
        if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o700:
            raise Refusal("state_permissions", "Use an owner-owned private state directory with mode 0700.")
    finally:
        os.close(fd)


def _private_file(path: Path) -> int:
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except OSError:
        raise Refusal("state_permissions", "A state file is unavailable or unsafe.") from None
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600:
        os.close(fd)
        raise Refusal("state_permissions", "State files must be owner-owned regular files with mode 0600 and one link.")
    return fd


class Store:
    def __init__(self, directory: Path):
        private_directory(directory)
        self.directory = directory
        self._mutex = threading.Lock()
        self._lock_fd = _private_file(directory / "coordinator.lock")
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self._lock_fd)
            self._lock_fd = None
            raise Refusal("coordinator_busy", "Another coordinator owns this state directory. Use it or wait for it to stop.") from None
        try:
            fd = _private_file(directory / "jobs.sqlite3")
            os.close(fd)
            self.db = sqlite3.connect(directory / "jobs.sqlite3", timeout=1, check_same_thread=False)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA foreign_keys=ON")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1, 2}:
                raise Refusal("store_version", "This state directory uses an unsupported schema version.")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, root_identity TEXT NOT NULL,
                    request TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                    completed_at TEXT, packet TEXT, error TEXT
                );
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                PRAGMA user_version=2;
            """)
            # The exclusive owner lock proves no cooperating previous worker is alive.
            with self.db:
                self.db.execute("UPDATE jobs SET status='failed', completed_at=?, error=? WHERE status='running'",
                                (now(), json.dumps({"code": "interrupted", "message": "The previous coordinator stopped before completion. Start a new job."})))
                self.db.execute("INSERT OR IGNORE INTO settings VALUES ('device_id', ?)", (json.dumps(uuid.uuid4().hex),))
        except Exception:
            if hasattr(self, "db"):
                self.db.close()
            os.close(self._lock_fd)
            self._lock_fd = None
            raise

    def close(self):
        self.db.close()
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None

    def create(self, project_id: str, root_identity: str, request: str) -> str:
        with self._mutex, self.db:
            if self.db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= MAX_JOBS:
                raise Refusal("store_full", f"This store holds {MAX_JOBS} receipts. Archive it and use a new private state directory.")
            job_id = uuid.uuid4().hex
            self.db.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, 'running', ?, NULL, NULL, NULL)",
                            (job_id, project_id, root_identity, request, now()))
        return job_id

    def get(self, project_id: str, root_identity: str, job_id: str) -> dict:
        with self._mutex:
            row = self.db.execute("SELECT * FROM jobs WHERE job_id=? AND project_id=? AND root_identity=?",
                                  (job_id, project_id, root_identity)).fetchone()
        if row is None:
            raise Refusal("job_unavailable", "No job is available for this project and root identity.")
        result = dict(row)
        result.pop("root_identity")
        for key in ("packet", "error"):
            if result[key] is not None:
                result[key] = json.loads(result[key])
        return result

    def finish(self, job_id: str, status: str, packet=None, error=None) -> bool:
        with self._mutex, self.db:
            result = self.db.execute("UPDATE jobs SET status=?, completed_at=?, packet=?, error=? WHERE job_id=? AND status='running'",
                                     (status, now(), json.dumps(packet, ensure_ascii=False) if packet is not None else None,
                                      json.dumps(error) if error is not None else None, job_id))
        return result.rowcount == 1

    def setting(self, key, default=None):
        with self._mutex:
            row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return default if row is None else json.loads(row[0])

    def set_setting(self, key, value):
        with self._mutex, self.db:
            self.db.execute("INSERT INTO settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (key, json.dumps(value, ensure_ascii=False)))

    def recent(self, project_id, root_identity):
        with self._mutex:
            rows = self.db.execute("SELECT job_id, project_id, status, created_at, completed_at, substr(request, 1, 200) AS request_preview FROM jobs WHERE project_id=? AND root_identity=? ORDER BY created_at DESC LIMIT 20",
                                   (project_id, root_identity)).fetchall()
        return [dict(row) for row in rows]

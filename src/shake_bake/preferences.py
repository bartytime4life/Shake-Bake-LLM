"""Private, single-writer persistence for the workbench's Local AI choice."""

import json
import os
from pathlib import Path
import secrets
import stat

from .contracts import Refusal
from .worker import parse_json


def default_state_directory():
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    if not base.is_absolute():
        raise Refusal("absolute_state_directory_required")
    return base / "shake-bake"


class LocalPreferences:
    """Only a boolean is stored. Jobs, source, policy and model profiles are not."""

    def __init__(self, directory, source_roots):
        if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
            raise Refusal("private_preferences_require_posix")
        import fcntl

        self._directory = self._lock = None
        self.enabled = False
        path = Path(directory).expanduser().absolute()
        resolved = path.parent.resolve() / path.name
        if any(resolved == Path(root).resolve() or Path(root).resolve() in resolved.parents
               for root in source_roots):
            raise Refusal("preferences_inside_source")
        try:
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            info = os.fstat(self._directory)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                raise Refusal("preferences_directory_must_be_private_0700")
            self._lock = os.open("preferences.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 0o600, dir_fd=self._directory)
            self._check_file(os.fstat(self._lock))
            try:
                fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refusal("preferences_already_in_use") from None
            try:
                value = parse_json(self._read().decode("utf-8"))
            except FileNotFoundError:
                return  # A new installation starts paused.
            if (not isinstance(value, dict) or set(value) != {"schema_version", "local_ai_enabled"} or
                    value["schema_version"] != "1" or type(value["local_ai_enabled"]) is not bool):
                raise Refusal("invalid_local_ai_preferences")
            self.enabled = value["local_ai_enabled"]
        except Exception as error:
            self.close()
            if isinstance(error, Refusal):
                raise
            raise Refusal("local_ai_preferences_unavailable") from None

    @staticmethod
    def _check_file(info):
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1 or info.st_size > 4096):
            raise Refusal("preferences_file_must_be_private_0600")

    def _read(self):
        descriptor = os.open("preferences.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=self._directory)
        try:
            self._check_file(os.fstat(descriptor))
            raw = os.read(descriptor, 4097)
            if len(raw) > 4096:
                raise Refusal("invalid_local_ai_preferences")
            return raw
        finally:
            os.close(descriptor)

    def save(self, enabled):
        if self._directory is None:
            raise Refusal("local_ai_preferences_closed")
        if type(enabled) is not bool:
            raise Refusal("invalid_settings")
        name = ".preferences-" + secrets.token_hex(16)
        created = False
        try:
            try:
                self._read()  # Refuse an unsafe owner-replaced destination.
            except FileNotFoundError:
                pass
            descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=self._directory)
            created = True
            with os.fdopen(descriptor, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(json.dumps({"schema_version": "1", "local_ai_enabled": enabled}).encode())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, "preferences.json", src_dir_fd=self._directory, dst_dir_fd=self._directory)
            created = False
            os.fsync(self._directory)
            self.enabled = enabled
        except (OSError, Refusal):
            raise Refusal("preferences_not_saved_local_ai_paused") from None
        finally:
            if created:
                os.unlink(name, dir_fd=self._directory)

    def close(self):
        for name in ("_lock", "_directory"):
            descriptor = getattr(self, name, None)
            if descriptor is not None:
                os.close(descriptor)
                setattr(self, name, None)

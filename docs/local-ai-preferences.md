# Local AI across restarts

The normal GUI launch stores only the Local AI on/off choice in a private settings directory. A launch with no saved choice starts **off**. Turning it on is an explicit owner action; starting a task cannot turn it on. The GUI and shared adapter use the same service choice. Evidence-only tasks remain available while paused.

The default is `$XDG_STATE_HOME/shake-bake`, or `~/.local/state/shake-bake` when that variable is unset. Use `--state-dir /absolute/private/directory` for a separate installation or development service. The directory must be outside approved source roots, owned by the current user and mode 0700. Its preferences and lock files must be regular owner-owned mode 0600 files. Symlink and hard-linked files are refused. Trusted parent directories remain part of the existing filesystem trust assumption.

`preferences.json` contains a schema version and one boolean. It contains no tasks, source, roots, model selections, credentials or qualification records. Writes use an atomic replacement and flush the file/directory. A lifetime lock prevents two services using the same directory from overwriting each other's choice. A second independent service needs a different `--state-dir`.

Corrupt or unreadable settings stop startup with an explicit error. A failed save pauses Local AI in the current process and reports that the preference was not saved; it does not claim the failed write will survive a restart. Resolve the storage problem and successfully save Off before relying on persistence. The app does not automatically delete or repair owner files.

The service's saved choice is authoritative. Browser preferences retain the draft/model selection but cannot silently resume a paused service. Older browser-only choices are not an independent service setting; the first launch of this build with no saved record starts off.

Jobs, captured evidence and pause effects on owned runners remain bounded to the service session. Completed helper results expire after five minutes or the eight-job retention limit. Recent metadata and a browser-pinned brief may remain visible until the session/page ends. This is not durable job recovery, synchronized multi-user settings, profile persistence or proof that a separate Ollama daemon stopped GPU work.

Direct `Controller` construction without a state directory is an explicit session-only diagnostic used by the tests and SDK smoke checks. The normal `gui` command always supplies the persistent directory. The interface states which lifetime applies.

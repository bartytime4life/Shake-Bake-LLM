"""An owner-configured, bounded task session used by the MCP adapter."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from .collector import MAX_FILES, _parts, validate_request
from .contracts import Refusal
from .task_protocol import MAX_TASK_INPUT_BYTES, MAX_TASK_RESULT_BYTES
from .worker import parse_json, validate_settings

ACTIVE = frozenset({"RUNNING"})


@dataclass
class _Job:
    identifier: str
    project: str
    request: str
    created: float
    process: subprocess.Popen
    streams: tuple
    state: str = "RUNNING"
    result: dict | None = None


class HelperSession:
    def __init__(self, projects: dict[str, Path], *, model: str | None = None, evidence_only: bool = False, port: int = 11434, policy_path: Path | None = None):
        if sys.platform != "linux":
            raise Refusal("linux_helper_required")
        if policy_path is not None:
            if model is not None or evidence_only:
                raise Refusal("explicit_helper_mode_required")
        elif (model is None) != evidence_only:
            raise Refusal("explicit_helper_mode_required")
        if model is not None:
            validate_settings(model, port)
        if not isinstance(projects, dict) or not 1 <= len(projects) <= 8:
            raise Refusal("invalid_project_configuration")
        self._projects = {}
        for name, path in projects.items():
            self._projects[name] = self._project_root(name, path)
        # Keep anonymous task I/O outside every inspected checkout, including
        # when the launch environment sets TMPDIR to a project directory.
        scratch_candidates = (Path(tempfile.gettempdir()), Path("/tmp"), Path("/var/tmp"))
        self._scratch = None
        for candidate in scratch_candidates:
            candidate = candidate.resolve()
            if candidate.is_dir() and all(root != candidate and root not in candidate.parents for root in self._projects.values()):
                self._scratch = candidate
                break
        if self._scratch is None:
            raise Refusal("external_task_scratch_required")
        self.model, self.port = model, port
        self.policy_path = Path(policy_path).resolve() if policy_path is not None else None
        self._jobs: dict[str, _Job] = {}
        self._lock = threading.RLock()
        self._closed = False

    @property
    def mode(self) -> str:
        if self.policy_path is not None:
            return "routed_helper"
        return "ollama_helper" if self.model is not None else "evidence_only_diagnostic"

    def list_projects(self) -> dict:
        with self._lock:
            return {"mode": self.mode, "projects": sorted(self._projects), "max_active_tasks": 1}

    @staticmethod
    def _project_root(project_id: str, path: Path) -> Path:
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", project_id):
            raise Refusal("invalid_project_id")
        try:
            supplied = Path(path)
            if not supplied.is_absolute():
                raise OSError()
            root = supplied.resolve(strict=True)
            if not root.is_dir():
                raise OSError()
        except (OSError, RuntimeError, TypeError, ValueError):
            raise Refusal("invalid_project_root") from None
        return root

    def add_project(self, project_id: str, path: Path, *, protected_paths=()) -> dict:
        """Connect an explicit owner-selected folder without reading its contents.

        This is an owner-controller operation, not an MCP/model tool. The caller
        must authenticate the owner request; inspected source and model output
        must never supply this method's arguments or expand adapter permissions.
        Existing project IDs and captured jobs retain their original scope.
        Protected owner paths must already be resolved by the controller. Check
        them against this method's resolved root, even after a caller precheck.
        """
        with self._lock:
            if self._closed:
                raise Refusal("helper_closed")
            for job in self._jobs.values():
                self._refresh(job)
            if any(job.state in ACTIVE for job in self._jobs.values()):
                raise Refusal("helper_busy")
            root = self._project_root(project_id, path)
            if project_id in self._projects:
                raise Refusal("duplicate_project_id")
            if root in self._projects.values():
                raise Refusal("duplicate_project_root")
            if len(self._projects) >= 8:
                raise Refusal("project_limit_reached")
            if root == Path(root.anchor) or root == Path.home().resolve():
                raise Refusal("project_root_too_broad")
            if root == self._scratch or root in self._scratch.parents:
                raise Refusal("external_task_scratch_required")
            if self.policy_path is not None and (root == self.policy_path or root in self.policy_path.parents):
                raise Refusal("routing_policy_inside_source")
            if any(root == protected or root in protected.parents for protected in protected_paths):
                raise Refusal("project_contains_private_settings")
            self._projects[project_id] = root
            return {"id": project_id, "path": str(root)}

    @staticmethod
    def _copy(value):
        return json.loads(json.dumps(value, ensure_ascii=False))

    def _refresh(self, job: _Job) -> None:
        if job.state not in ACTIVE:
            return
        status = job.process.poll()
        if status is None:
            if time.monotonic() - job.created > 46:
                self._stop(job, "TIMED_OUT")
            return
        try:
            job.streams[1].seek(0)
            raw = job.streams[1].read(MAX_TASK_RESULT_BYTES + 1)
            if len(raw) > MAX_TASK_RESULT_BYTES:
                raise Refusal("invalid_runner_result")
            result = parse_json(raw.decode("utf-8"))
            if not isinstance(result, dict) or result.get("outcome") not in ("ANSWER", "ABSTAIN", "DENY", "ERROR"):
                raise Refusal("invalid_runner_result")
            if "search" in result:
                search = result["search"]
                if search.get("original_request") != job.request:
                    raise Refusal("invalid_runner_result")
                packet = search.get("packet")
                if packet:
                    if packet.get("original_request") != job.request or not 1 <= len(packet["evidence"]) <= MAX_FILES:
                        raise Refusal("invalid_runner_result")
                    for record in packet["evidence"]:
                        _parts(record["path"])
                        if hashlib.sha256(record["text"].encode("utf-8")).hexdigest() != record["excerpt_sha256"]:
                            raise Refusal("invalid_runner_result")
                    if self.model and result.get("worker") is None and not result.get("worker_error"):
                        raise Refusal("invalid_runner_result")
            elif result.get("outcome") not in ("DENY", "ERROR"):
                raise Refusal("invalid_runner_result")
            job.result = result
            job.state = "DONE"
        except Exception:
            job.state = "TIMED_OUT" if status == -signal.SIGALRM else "ERROR"
            job.result = {"outcome": "ERROR", "code": "task_deadline" if job.state == "TIMED_OUT" else "invalid_runner_result"}
        finally:
            for stream in job.streams:
                stream.close()

    def _stop(self, job: _Job, state: str) -> None:
        if job.state not in ACTIVE:
            return
        if job.process.poll() is None:
            job.process.terminate()
            try:
                job.process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                job.process.kill()
                job.process.wait(timeout=1)
        job.state = state
        job.result = None
        for stream in job.streams:
            stream.close()

    def _lookup(self, identifier: str) -> _Job:
        if not isinstance(identifier, str) or identifier not in self._jobs:
            raise Refusal("unknown_or_expired_task")
        job = self._jobs[identifier]
        self._refresh(job)
        if job.state not in ACTIVE and time.monotonic() - job.created > 300:
            del self._jobs[identifier]
            raise Refusal("unknown_or_expired_task")
        return job

    def start_task(self, project_id: str, task: str, *, task_kind: str = "code", disabled: bool = False, candidate: dict | None = None) -> dict:
        with self._lock:
            if self._closed:
                raise Refusal("helper_closed")
            if not isinstance(project_id, str) or project_id not in self._projects:
                raise Refusal("project_not_allowed")
            validate_request(task)
            if task_kind not in ("code", "troubleshoot", "documents", "search") or type(disabled) is not bool:
                raise Refusal("invalid_task_options")
            if candidate is not None:
                if self.policy_path is None or disabled or not isinstance(candidate, dict) or set(candidate) != {"model", "digest", "acknowledged"} or candidate["acknowledged"] is not True:
                    raise Refusal("invalid_candidate_trial")
                validate_settings(candidate["model"], self.port)
                if not isinstance(candidate["digest"], str) or not re.fullmatch(r"[a-f0-9]{64}", candidate["digest"]):
                    raise Refusal("invalid_expected_digest")
            for job in self._jobs.values():
                self._refresh(job)
            if any(job.state in ACTIVE for job in self._jobs.values()):
                raise Refusal("helper_busy")
            request = {"root": str(self._projects[project_id]), "task": task, "model": self.model, "port": self.port}
            if self.policy_path is not None:
                request.update(policy_path=str(self.policy_path), task_kind=task_kind, disabled=disabled)
                if candidate is not None:
                    request["candidate"] = candidate
            try:
                raw = json.dumps(request, ensure_ascii=False).encode("utf-8")
            except UnicodeEncodeError:
                raise Refusal("task_input_utf8_required") from None
            if len(raw) > MAX_TASK_INPUT_BYTES:
                raise Refusal("task_input_too_large")
            # Bounded, session-only retention. Old handles fail explicitly.
            while len(self._jobs) >= 8:
                oldest = min(self._jobs.values(), key=lambda item: item.created)
                del self._jobs[oldest.identifier]
            streams = []
            try:
                for _ in range(3):
                    streams.append(tempfile.TemporaryFile(dir=self._scratch))
                streams[0].write(raw); streams[0].seek(0)
                environment = dict(os.environ)
                # Resolve only our package in the child, independently of the inspected root.
                environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
                # -P excludes launch cwd from imports; -S prevents sitecustomize.
                # The runner has no site-package dependencies. Never resolve its
                # module from a repository that happens to be the caller's cwd.
                process = subprocess.Popen([sys.executable, "-B", "-P", "-S", "-m", "shake_bake.job_runner", str(os.getpid())],
                    stdin=streams[0], stdout=streams[1], stderr=streams[2], env=environment,
                    cwd=environment["PYTHONPATH"], close_fds=True, start_new_session=True)
            except Exception:
                for stream in streams:
                    stream.close()
                raise Refusal("task_start_failed") from None
            identifier = uuid.uuid4().hex
            self._jobs[identifier] = _Job(identifier, project_id, task, time.monotonic(), process, tuple(streams))
            return {"task_id": identifier, "state": "RUNNING", "mode": self.mode}

    def get_result(self, task_id: str) -> dict:
        with self._lock:
            job = self._lookup(task_id)
            answer = {"task_id": task_id, "state": job.state, "mode": self.mode}
            if job.state != "DONE":
                if job.result:
                    answer.update(job.result)
                return self._copy(answer)
            result = job.result
            answer.update({"original_request": job.request, "outcome": result["outcome"],
                           "worker": result.get("worker"), "worker_error": result.get("worker_error"),
                           "result_kind": "preparation_result", "final_answer_ready": False,
                           "requires_host_reasoning": True,
                           "verification": {"evidence": "captured_bytes_and_hashes", "worker_notes": "unverified_interpretation"}})
            if "routing" in result:
                answer["routing"] = result["routing"]
            search = result.get("search", {})
            # Missing evidence does not mean a complete search found nothing.
            if search:
                answer["cutoffs"] = search["cutoffs"]
                answer["exclusions"] = search["exclusions"]
                answer["files_examined"] = search["files_examined"]
                answer["matching_files"] = search["matching_files"]
                answer["source_bytes_read"] = search["source_bytes_read"]
                answer["selected_excerpt_bytes"] = search["selected_excerpt_bytes"]
                answer["context"] = search.get("context", [])
                answer["context_map"] = search.get("context_map", [])
                answer["line_index"] = search.get("line_index", [])
                answer["screening"] = search.get("screening", [])
            packet = search.get("packet")
            if packet:
                answer["snapshot_id"] = packet["snapshot_id"]
                answer["evidence"] = [{"evidence_id": f"E{i+1}", **{k: record[k] for k in ("path", "start_line", "end_line", "file_sha256")}}
                                      for i, record in enumerate(packet["evidence"])]
                answer["instruction"] = "Fetch exact evidence before grounded code/security claims. Worker notes are unverified."
                if job.result.get("worker") is not None and job.result["worker"].get("label") != "unverified_worker_interpretation":
                    raise Refusal("invalid_worker_label")
            elif "code" in result:
                answer["code"] = result["code"]
            return self._copy(answer)

    def fetch_evidence(self, task_id: str, evidence_id: str) -> dict:
        with self._lock:
            job = self._lookup(task_id)
            if job.state != "DONE":
                raise Refusal("task_not_ready")
            records = (job.result or {}).get("search", {}).get("packet", {}) or {}
            records = records.get("evidence", [])
            if not isinstance(evidence_id, str) or not re.fullmatch(r"E[1-9][0-9]?", evidence_id):
                raise Refusal("unknown_evidence")
            index = int(evidence_id[1:]) - 1
            if index >= min(len(records), MAX_FILES):
                raise Refusal("unknown_evidence")
            return self._copy({"evidence_id": evidence_id, "freshness": "captured_snapshot_not_live_revalidation", **records[index]})

    def cancel_task(self, task_id: str) -> dict:
        with self._lock:
            job = self._lookup(task_id)
            if job.state in ACTIVE:
                self._stop(job, "CANCELLED")
            return {"task_id": task_id, "state": job.state}

    def close(self) -> None:
        with self._lock:
            self._closed = True
            for job in self._jobs.values():
                self._stop(job, "CANCELLED")
            self._jobs.clear()

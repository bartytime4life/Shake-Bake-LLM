"""Conservative owner-controlled profile routing; never a task-completion judge."""

from hashlib import sha256
import math
from pathlib import Path

from .contracts import Refusal
from .ollama import OPTIONS, digest_value, model_name

TASK_KINDS = ("code", "troubleshoot", "documents", "search")
AI_MODES = ("off", "best", "trial")


def pipeline_fingerprint():
    digest = sha256(b"shake-bake-pipeline-v2\0")
    root = Path(__file__).parent
    for path in sorted(root.glob("*.py")) + sorted((root / "web").glob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def validate_profiles(document):
    if not isinstance(document, dict) or set(document) != {"schema_version", "profiles"} or document["schema_version"] != 1:
        raise Refusal("profile_policy", "A profile policy needs schema_version = 1 and profiles only.")
    profiles = document["profiles"]
    if not isinstance(profiles, list) or len(profiles) > 16:
        raise Refusal("profile_policy", "A profile policy can contain at most sixteen profiles.")
    seen = set()
    for profile in profiles:
        if not isinstance(profile, dict) or set(profile) != {"id", "model", "digest", "tasks", "enabled", "qualification"}:
            raise Refusal("profile_policy", "Each profile requires id, model, digest, tasks, enabled and qualification.")
        from .contracts import check_project_id
        check_project_id(profile["id"])
        if profile["id"] in seen or type(profile["enabled"]) is not bool:
            raise Refusal("profile_policy", "Profiles need unique IDs and explicit enabled flags.")
        seen.add(profile["id"])
        model_name(profile["model"])
        digest_value(profile["digest"])
        if not isinstance(profile["tasks"], list) or not profile["tasks"] or any(task not in TASK_KINDS for task in profile["tasks"]):
            raise Refusal("profile_policy", "Profile tasks must use the supported task categories.")
        if profile["qualification"] is not None and not isinstance(profile["qualification"], dict):
            raise Refusal("profile_policy", "Qualification is a reviewed record or null for a candidate.")
    return tuple(profiles)


def qualification_problem(profile, device_id, pipeline):
    q = profile["qualification"]
    if not isinstance(q, dict):
        return "No reviewed local qualification record."
    required = {"reviewed", "held_out", "dataset", "dataset_version", "unique_cases", "accuracy", "baseline_accuracy", "critical_misses", "unsupported_critical_claims", "median_seconds", "device_id", "pipeline_sha256", "runtime_version", "options"}
    if set(q) != required:
        return "Incomplete qualification record."
    if q["reviewed"] is not True or q["held_out"] is not True:
        return "The record is unreviewed or development-only."
    if type(q["unique_cases"]) is not int or q["unique_cases"] < 20 or not all(isinstance(q[key], str) and q[key] for key in ("dataset", "dataset_version", "runtime_version")):
        return "Qualification needs a versioned held-out cohort of at least twenty unique cases."
    for key in ("accuracy", "baseline_accuracy", "median_seconds"):
        value = q[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            return "Invalid qualification measurements."
    if not 0 <= q["baseline_accuracy"] <= q["accuracy"] <= 1:
        return "Accuracy did not meet the paired native-host baseline."
    if type(q["critical_misses"]) is not int or q["critical_misses"] != 0 or type(q["unsupported_critical_claims"]) is not int or q["unsupported_critical_claims"] != 0:
        return "The record contains critical misses or unsupported critical claims."
    if q["device_id"] != device_id or q["pipeline_sha256"] != pipeline or q["options"] != OPTIONS:
        return "The device, pipeline or generation settings changed; re-qualification is required."
    return None


def choose_profile(profiles, task_kind, device_id, pipeline):
    eligible, rejected = [], []
    for profile in profiles:
        reason = None
        if not profile["enabled"] or task_kind not in profile["tasks"]:
            reason = "Profile disabled or not applicable to this task."
        else:
            reason = qualification_problem(profile, device_id, pipeline)
        if reason:
            rejected.append({"profile_id": profile["id"], "reason": reason})
        else:
            eligible.append(profile)
    if not eligible:
        return None, rejected
    cohorts = {(x["qualification"]["dataset"], x["qualification"]["dataset_version"], x["qualification"]["unique_cases"], x["qualification"]["baseline_accuracy"]) for x in eligible}
    if len(cohorts) != 1:
        return None, rejected + [{"profile_id": x["id"], "reason": "Qualified records use incomparable cohorts or baselines."} for x in eligible]
    eligible.sort(key=lambda p: (-p["qualification"]["accuracy"], p["qualification"]["median_seconds"], p["id"]))
    return eligible[0], rejected

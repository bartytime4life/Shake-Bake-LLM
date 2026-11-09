"""Owner-controlled accuracy gates and explanations; no model-based router."""

from dataclasses import asdict, dataclass, replace
import hashlib
import math
from pathlib import Path
import re
import time

from .briefing import Brief, build_brief, collection_scope
from .collector import _read
from .contracts import Refusal
from .search import prepare
from .worker import canonical_model, local_inventory, organize, parse_json, validate_settings

TASK_KINDS = ("code", "troubleshoot", "documents", "search")


def pipeline_id() -> str:
    digest = hashlib.sha256()
    root = Path(__file__).resolve().parent
    for name in ("__init__.py", "contracts.py", "collector.py", "search.py", "worker.py", "briefing.py", "routing.py",
                 "helper.py", "job_runner.py", "task_protocol.py", "gui.py", "shared.py", "mcp_server.py", "doctor.py", "capabilities.py", "preferences.py"):
        digest.update(name.encode() + b"\0" + (root / name).read_bytes())
    return digest.hexdigest()


def _number(value, *, integer=False, maximum=1.0):
    if type(value) not in ((int,) if integer else (int, float)) or not 0 <= value <= maximum or (type(value) is float and not math.isfinite(value)):
        raise Refusal("invalid_routing_policy")
    return value


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}", value):
        raise Refusal("invalid_routing_policy")


def validate_policy(policy: dict) -> dict:
    if not isinstance(policy, dict) or set(policy) != {"schema_version", "enabled", "baselines", "profiles"} or policy["schema_version"] != "1" or type(policy["enabled"]) is not bool:
        raise Refusal("invalid_routing_policy")
    baselines, profiles = policy["baselines"], policy["profiles"]
    if not isinstance(baselines, dict) or set(baselines) - set(TASK_KINDS) or not isinstance(profiles, list) or len(profiles) > 32:
        raise Refusal("invalid_routing_policy")
    for baseline in baselines.values():
        if not isinstance(baseline, dict) or set(baseline) != {"dataset_id", "host_baseline_id", "case_count", "accuracy"}:
            raise Refusal("invalid_routing_policy")
        _identifier(baseline["dataset_id"]); _identifier(baseline["host_baseline_id"])
        if _number(baseline["case_count"], integer=True, maximum=100000) < 1:
            raise Refusal("invalid_routing_policy")
        _number(baseline["accuracy"])
    seen = set()
    for profile in profiles:
        if not isinstance(profile, dict) or set(profile) != {"id", "task_kind", "model", "status", "digest", "pipeline_id", "evaluation"}:
            raise Refusal("invalid_routing_policy")
        _identifier(profile["id"])
        if profile["id"] in seen or profile["task_kind"] not in TASK_KINDS or profile["status"] not in ("candidate", "qualified", "disabled"):
            raise Refusal("invalid_routing_policy")
        seen.add(profile["id"])
        validate_settings(profile["model"])
        for field in ("digest", "pipeline_id"):
            if profile[field] is not None and (not isinstance(profile[field], str) or not re.fullmatch(r"[a-f0-9]{64}", profile[field])):
                raise Refusal("invalid_routing_policy")
        evaluation = profile["evaluation"]
        if evaluation is not None:
            required = {"dataset_id", "host_baseline_id", "case_count", "split", "reviewed", "critical_misses", "unsupported_critical_claims", "accuracy", "median_latency_ms"}
            if not isinstance(evaluation, dict) or set(evaluation) != required:
                raise Refusal("invalid_routing_policy")
            _identifier(evaluation["dataset_id"]); _identifier(evaluation["host_baseline_id"])
            if type(evaluation["reviewed"]) is not bool or evaluation["split"] not in ("development", "held_out"):
                raise Refusal("invalid_routing_policy")
            for field in ("case_count", "critical_misses", "unsupported_critical_claims"):
                _number(evaluation[field], integer=True, maximum=100000)
            _number(evaluation["accuracy"])
            _number(evaluation["median_latency_ms"], maximum=3600000)
    return policy


def load_policy(path: Path, source_root: Path) -> dict:
    try:
        path, root = path.resolve(strict=True), source_root.resolve(strict=True)
        if path == root or root in path.parents:
            raise Refusal("routing_policy_inside_source")
        return validate_policy(parse_json(_read(path.parent, path.name).decode("utf-8")))
    except (OSError, UnicodeError, RuntimeError):
        raise Refusal("routing_policy_unavailable") from None


@dataclass(frozen=True)
class Decision:
    task_kind: str
    mode: str
    reason: str
    why: str
    profile_id: str | None = None
    model: str | None = None
    expected_digest: str | None = None
    rejected: tuple[tuple[str, str], ...] = ()
    attempted_profile_id: str | None = None
    attempted_model: str | None = None

    def to_dict(self):
        return asdict(self)


def fallback(task_kind, reason, rejected=()):
    explanations = {
        "local_ai_disabled": "Local AI is switched off. Exact evidence remains available; no model was contacted.",
        "no_qualified_profile": "No local profile meets this task's recorded accuracy requirements. The host must assess the evidence.",
        "qualified_model_unavailable": "Qualified profiles are unavailable or their recorded model identity changed. No substitute was selected.",
        "inventory_unavailable": "Local inventory could not be verified. No model was selected; exact evidence is retained.",
    }
    return Decision(task_kind, "evidence_only", reason, explanations.get(reason, "The local preparation step could not be qualified. Exact evidence is retained."), rejected=tuple(rejected))


def eligible_profiles(policy, task_kind, current_pipeline):
    baseline = policy["baselines"].get(task_kind)
    eligible, rejected = [], []
    for profile in policy["profiles"]:
        if profile["task_kind"] != task_kind:
            continue
        record = profile["evaluation"]
        reason = None
        if profile["status"] == "disabled":
            reason = "disabled_by_owner"
        elif profile["status"] != "qualified" or not baseline or not record:
            reason = "not_qualified"
        elif profile["pipeline_id"] != current_pipeline or profile["digest"] is None:
            reason = "stale_identity"
        elif not record["reviewed"] or record["split"] != "held_out":
            reason = "unreviewed_or_development_only"
        elif any(record[key] != baseline[key] for key in ("dataset_id", "host_baseline_id", "case_count")):
            reason = "incomparable_trial"
        elif record["critical_misses"] or record["unsupported_critical_claims"]:
            reason = "critical_accuracy_failure"
        elif record["accuracy"] < baseline["accuracy"]:
            reason = "below_native_baseline"
        if reason:
            rejected.append((profile["id"], reason))
        else:
            eligible.append(profile)
    return eligible, rejected


def choose(policy, task_kind, inventory, *, current_pipeline=None) -> Decision:
    validate_policy(policy)
    if task_kind not in TASK_KINDS:
        raise Refusal("invalid_task_kind")
    if not isinstance(inventory, dict):
        raise Refusal("invalid_local_inventory")
    if not policy["enabled"]:
        return fallback(task_kind, "local_ai_disabled")
    eligible, rejected = eligible_profiles(policy, task_kind, current_pipeline or pipeline_id())
    available = []
    for profile in eligible:
        if inventory.get(canonical_model(profile["model"])) != profile["digest"]:
            rejected.append((profile["id"], "unavailable_or_digest_changed"))
        else:
            available.append(profile)
    if not available:
        return fallback(task_kind, "qualified_model_unavailable" if eligible else "no_qualified_profile", rejected)
    selected = min(available, key=lambda p: (-p["evaluation"]["accuracy"], p["evaluation"]["median_latency_ms"], p["id"]))
    evaluation = selected["evaluation"]
    why = (f"Selected {selected['model']} for {task_kind}: highest recorded accuracy among compatible profiles "
           f"on the same reviewed held-out trial ({evaluation['accuracy']:.1%}; native baseline {policy['baselines'][task_kind]['accuracy']:.1%}). "
           "The record reports no critical misses or unsupported critical claims. Latency only breaks accuracy ties. This is not a universal-best claim.")
    return Decision(task_kind, "local_model", "qualified_profile_selected", why, selected["id"], selected["model"], selected["digest"], tuple(rejected))


def assist(root: Path, task: str, task_kind: str, *, policy_path: Path | None, port=11434, disabled=False):
    if task_kind not in TASK_KINDS:
        raise Refusal("invalid_task_kind")
    search = prepare(root, task)
    if disabled:
        decision = fallback(task_kind, "local_ai_disabled")
    else:
        try:
            if policy_path is None:
                raise Refusal("routing_policy_required")
            policy = load_policy(policy_path, root)
            if not policy["enabled"]:
                decision = fallback(task_kind, "local_ai_disabled")
            else:
                eligible, rejected = eligible_profiles(policy, task_kind, pipeline_id())
                if not eligible:
                    decision = fallback(task_kind, "no_qualified_profile", rejected)
                elif search.packet is None:
                    decision = fallback(task_kind, "no_usable_evidence")
                else:
                    try:
                        inventory = local_inventory(port, time.monotonic() + 5)
                        decision = choose(policy, task_kind, inventory)
                    except Refusal:
                        decision = fallback(task_kind, "inventory_unavailable")
        except Refusal as refusal:
            decision = fallback(task_kind, refusal.code)
    worker, error = None, None
    if decision.mode == "local_model" and search.packet:
        try:
            worker = organize(search.packet, decision.model, port=port, expected_digest=decision.expected_digest,
                              collection_context=collection_scope(search), task_kind=task_kind)
        except Refusal as refusal:
            error = refusal.code
            failed = fallback(task_kind, refusal.code, decision.rejected)
            decision = replace(failed, attempted_profile_id=decision.profile_id, attempted_model=decision.model,
                               why=f"The attempted profile {decision.profile_id} could not produce a qualified handoff ({refusal.code}). Exact evidence is retained; no substitute was tried.")
    brief = Brief("ANSWER" if worker else "ABSTAIN", search, worker, error or (decision.reason if not worker else None))
    return decision, brief


def candidate_trial(root, task, task_kind, candidate, *, port=11434):
    """An acknowledged diagnostic run cannot promote an owner routing profile."""
    if task_kind not in TASK_KINDS or not isinstance(candidate, dict) or set(candidate) != {"model", "digest", "acknowledged"} or candidate["acknowledged"] is not True:
        raise Refusal("invalid_candidate_trial")
    validate_settings(candidate["model"], port)
    if not isinstance(candidate["digest"], str) or not re.fullmatch(r"[a-f0-9]{64}", candidate["digest"]):
        raise Refusal("invalid_expected_digest")
    brief = build_brief(root, task, model=candidate["model"], port=port, expected_digest=candidate["digest"], task_kind=task_kind)
    decision = Decision(task_kind, "candidate_trial", "unqualified_candidate_trial",
        "Explicit candidate trial. Notes are unverified; this run does not qualify accuracy or change routing policy.",
        model=candidate["model"], expected_digest=candidate["digest"])
    if brief.worker_error:
        decision = replace(decision, reason=brief.worker_error,
            why=f"Candidate notes were withheld ({brief.worker_error}). Exact evidence is retained; no substitute was tried.")
    return decision, brief

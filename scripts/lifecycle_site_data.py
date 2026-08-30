"""Build the split, client-facing lifecycle-aware leaderboard projection.

The adapter consumes only State's redacted public projection. It never reads
the private append-only event log, internal materialized views, or submission
source. Catalog metadata and optional schema-versioned preview fixtures fill
presentation fields that State does not own; every fallback is recorded in
``data_limitations``.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from html import escape as xml_escape
from types import MappingProxyType
from typing import Any
from urllib.parse import quote

try:
    from scripts.results_schema import result_id as expected_result_id
except ModuleNotFoundError:
    from results_schema import result_id as expected_result_id


GROUPS: tuple[dict[str, str], ...] = (
    {
        "id": "formalization-evaluation",
        "label": "Formalization evaluation",
        "policy": "Private-source submissions; accepted solutions are released after the publication delay.",
    },
    {
        "id": "software-verification",
        "label": "Software verification",
        "policy": "Private-source submissions; draft standings are provisional until the first frozen set.",
    },
    {
        "id": "open-problems",
        "label": "Open problems",
        "policy": "LeanEval-owned open problems, reviewed and published independently of external catalogs.",
    },
)
GROUP_BY_ID = {group["id"]: group for group in GROUPS}
STATUS_LABELS = {
    "draft": "Draft",
    "active": "Active",
    "archived": "Archive",
    "resolved": "Resolved",
}
SLUG_RE = re.compile(r"[^a-z0-9]+")
MODEL_ID_RE = re.compile(r"mi1_[0-9a-f]{64}")
ALIAS_KEY_RE = re.compile(r"ma1_[0-9a-f]{64}")
LOGIN_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?")
EVENT_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
RESULT_ID_RE = re.compile(r"r2_[0-9a-f]{64}")
REPLAY_TASK_ID_RE = re.compile(r"rt1_[0-9a-f]{64}")
DIGEST_RE = re.compile(r"[0-9a-f]{64}")
STATE_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{3}Z"
)
MODEL_ID_DOMAIN = b"lean-eval-model-identity-v1\0"
ALIAS_KEY_DOMAIN = b"lean-eval-model-alias-v1\0"
REPLAY_PROJECTION_FIELDS = {
    "status", "reason", "attempt", "checker", "checker_wall_time_ms",
    "checker_retired_instructions",
    "checker_retired_instructions_unavailable_reason", "build_wall_time_ms",
    "build_retired_instructions",
    "build_retired_instructions_unavailable_reason", "lines_of_code",
    "file_count",
}
REPLAY_STATUSES = {
    "queued", "running", "accepted", "rejected", "declined", "crashed",
    "timed_out", "failed", "unavailable",
}
HISTORICAL_FAILURE_REASONS = {
    "benchmark_fetch_failed", "runner_lost", "runner_start_failed",
    "source_fetch_failed", "toolchain_setup_failed", "verdict_invalid",
}
HISTORICAL_UNAVAILABLE_REASONS = {
    "source_ref_permanently_unavailable",
    "benchmark_ref_permanently_unavailable",
    "execution_profile_permanently_unavailable",
}
COUNTER_UNAVAILABLE_REASONS = {
    "counter_not_supported", "counter_permission_denied",
}
HISTORICAL_REPLAY_SERIES_FIELDS = {
    "result_id", "owner_login", "declared_model", "problem_id",
    "statement_revision", "historical_accepted_at", "source_visibility",
    "replay_task_id", "measurement_config_digest", "execution_profile_digest",
    "updated_at", "transition_event_id", "replay",
}
HISTORICAL_REPLAY_UNAVAILABILITY_FIELDS = {
    "result_id", "owner_login", "declared_model", "problem_id",
    "statement_revision", "historical_accepted_at", "source_visibility",
    "disposed_at", "disposition_event_id", "reason", "rationale",
}
STATE_OVERLAY_FIELDS = {
    "result_id", "owner_login", "declared_model", "problem_id",
    "statement_revision", "claim_event_id", "mutation_event_id", "claimed_at",
    "metadata", "model_id", "resolved_model_id",
}
STATE_AMENDMENT_FIELDS = {
    "effective_problem_id", "effective_statement_revision", "problem_repair",
    "applied_problem_repair", "retraction", "leaderboard_eligible",
}


def _slug(value: str) -> str:
    return SLUG_RE.sub("-", value.lower()).strip("-") or "unknown-model"


def _normalized_model(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _stable_legacy_id(parts: Iterable[object]) -> str:
    encoded = "\0".join(str(part) for part in parts).encode("utf-8")
    return "legacy_" + hashlib.sha256(encoded).hexdigest()


def _expected_replay_task_id(
    result_id_value: str, measurement_config_digest: str
) -> str:
    payload = (
        "lean-eval-replay-task-v1\0"
        + result_id_value
        + "\0"
        + measurement_config_digest
    ).encode("utf-8")
    return "rt1_" + hashlib.sha256(payload).hexdigest()


def _acceptance_key(solution: Solution) -> tuple[str, str, str]:
    return (solution.accepted_at, solution.acceptance_event_id, solution.result_id)


@dataclass(frozen=True)
class SetDefinition:
    id: str
    title: str
    frozen: bool
    published_at: str | None
    members: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ModelIdentityIndex:
    aliases: Mapping[tuple[str, str], tuple[str, str, str]]
    public_aliases: tuple[dict[str, str], ...]


EMPTY_MODEL_IDENTITY_INDEX = ModelIdentityIndex(MappingProxyType({}), ())


@dataclass
class Solution:
    result_id: str
    problem_id: str
    statement_revision: int
    declared_model: str
    canonical_model_id: str
    canonical_model_label: str
    submitter: str
    accepted_at: str
    acceptance_event_id: str
    retracted: bool
    metadata: dict[str, dict[str, Any]]
    provenance: dict[str, Any]
    public_solution: dict[str, Any]
    replay: dict[str, Any]
    measurements: list[dict[str, Any]] = field(default_factory=list)
    release: dict[str, Any] = field(default_factory=dict)
    model_identity_reviewed: bool = False


def load_preview_fixture(path: pathlib.Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1:
        raise SystemExit(f"{path}: unsupported preview fixture schema_version")
    aliases: set[str] = set()
    for alias in raw.get("model_aliases", []):
        required = {"declared_label", "canonical_id", "label"}
        if set(alias) != required or not all(
            isinstance(alias[field], str) and alias[field]
            for field in required
        ):
            raise SystemExit(f"{path}: invalid model alias")
        if alias["declared_label"] in aliases:
            raise SystemExit(f"{path}: duplicate declared model alias")
        aliases.add(alias["declared_label"])
    return raw


def load_set_definitions(manifest_dir: pathlib.Path) -> list[SetDefinition]:
    """Load named set manifests without making an unfrozen draft immutable."""

    import tomllib

    sets: list[SetDefinition] = []
    seen_ids: set[str] = set()
    if not manifest_dir.is_dir():
        return sets
    for path in sorted(manifest_dir.glob("*.toml")):
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        members: list[tuple[str, int]] = []
        for member in raw.get("members", []):
            problem_id = member.get("problem_id")
            revision = member.get("statement_revision")
            if not isinstance(problem_id, str) or not problem_id or type(revision) is not int or revision <= 0:
                raise SystemExit(f"{path}: invalid set member")
            members.append((problem_id, revision))
        set_id = raw.get("id")
        title = raw.get("title")
        frozen = raw.get("frozen")
        if not isinstance(set_id, str) or not set_id or not isinstance(title, str) or not title:
            raise SystemExit(f"{path}: id and title must be non-empty strings")
        if type(frozen) is not bool:
            raise SystemExit(f"{path}: frozen must be a boolean")
        if set_id in seen_ids:
            raise SystemExit(f"{path}: duplicate set id {set_id!r}")
        seen_ids.add(set_id)
        if len(members) != len(set(members)):
            raise SystemExit(f"{path}: duplicate set member")
        published_at = raw.get("published_at")
        if published_at is not None and not isinstance(published_at, str):
            raise SystemExit(f"{path}: published_at must be a string")
        if frozen and published_at is None:
            raise SystemExit(f"{path}: frozen set requires published_at")
        sets.append(SetDefinition(set_id, title, frozen, published_at, tuple(members)))
    return sets


def _metadata_fields(values: dict[str, Any], provenance: str) -> dict[str, dict[str, Any]]:
    return {
        key: {"value": value, "provenance": provenance}
        for key, value in sorted(values.items())
        if value is not None
    }


def _model_identity_id(request_event_id: str) -> str:
    return "mi1_" + hashlib.sha256(
        MODEL_ID_DOMAIN + request_event_id.encode("ascii")
    ).hexdigest()


def _model_alias_key(owner_login: str, alias: str) -> str:
    canonical = json.dumps(
        [owner_login, alias],
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "ma1_" + hashlib.sha256(ALIAS_KEY_DOMAIN + canonical).hexdigest()


def _model_label(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > 256
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise SystemExit(f"State projection: invalid {label}")
    return value


def build_model_identity_index(raw: dict[str, Any] | None) -> ModelIdentityIndex:
    """Validate and index the owner-scoped identity subset of State projection."""

    if raw is None or raw.get("schema_version") == 1:
        return EMPTY_MODEL_IDENTITY_INDEX
    if raw.get("schema_version") not in {4, 5, 6}:
        raise SystemExit("State domain: unsupported schema_version")
    identities: dict[str, dict[str, Any]] = {}
    identity_fields = {
        "model_id", "owner_login", "requested_name", "display_name", "status",
        "request_event_id", "requested_at", "decision_event_id", "decided_at",
        "reviewer_login", "rejection_reason", "mutation_event_id",
        "consolidated_into", "resolved_model_id",
    }
    for identity in raw.get("model_identities", []):
        if not isinstance(identity, dict) or set(identity) != identity_fields:
            raise SystemExit("State projection: invalid model identity fields")
        model_id = identity["model_id"]
        owner = identity["owner_login"]
        request_event_id = identity["request_event_id"]
        if (
            not isinstance(model_id, str)
            or MODEL_ID_RE.fullmatch(model_id) is None
            or not isinstance(owner, str)
            or LOGIN_RE.fullmatch(owner) is None
            or not isinstance(request_event_id, str)
            or EVENT_ID_RE.fullmatch(request_event_id) is None
            or model_id in identities
            or model_id != _model_identity_id(request_event_id)
        ):
            raise SystemExit("State projection: invalid model identity")
        _model_label(identity["requested_name"], "requested model name")
        _model_label(identity["display_name"], "model display name")
        if identity["status"] not in {
            "pending", "approved", "rejected", "consolidated"
        }:
            raise SystemExit("State projection: invalid model identity status")
        identities[model_id] = identity

    for model_id, identity in identities.items():
        status = identity["status"]
        consolidated_into = identity["consolidated_into"]
        resolved_id = identity["resolved_model_id"]
        if status == "approved":
            valid = consolidated_into is None and resolved_id == model_id
        elif status == "consolidated":
            direct_target = identities.get(consolidated_into)
            target = identities.get(resolved_id)
            valid = (
                isinstance(consolidated_into, str)
                and MODEL_ID_RE.fullmatch(consolidated_into) is not None
                and direct_target is not None
                and target is not None
                and direct_target["owner_login"] == identity["owner_login"]
                and direct_target["resolved_model_id"] == resolved_id
                and target["owner_login"] == identity["owner_login"]
                and target["status"] == "approved"
                and consolidated_into != model_id
                and target["model_id"] == resolved_id
            )
        else:
            valid = consolidated_into is None and resolved_id is None
        if not valid:
            raise SystemExit(
                "State projection: incoherent model identity resolution"
            )
        if status == "consolidated":
            current = model_id
            seen: set[str] = set()
            while current != resolved_id:
                if current in seen:
                    raise SystemExit(
                        "State projection: cyclic model identity consolidation"
                    )
                seen.add(current)
                current_identity = identities.get(current)
                if current_identity is None:
                    raise SystemExit(
                        "State projection: missing model identity consolidation target"
                    )
                current = current_identity["consolidated_into"]

    aliases: dict[tuple[str, str], tuple[str, str, str]] = {}
    summaries: list[dict[str, str]] = []
    alias_fields = {
        "alias_key", "owner_login", "alias", "model_id", "resolved_model_id",
        "assignment_event_id", "assigned_at",
    }
    for alias in raw.get("model_aliases", []):
        if not isinstance(alias, dict) or set(alias) != alias_fields:
            raise SystemExit("State projection: invalid model alias fields")
        owner = alias["owner_login"]
        declared = _model_label(alias["alias"], "model alias")
        alias_key = alias["alias_key"]
        model_id = alias["model_id"]
        resolved_id = alias["resolved_model_id"]
        source = identities.get(model_id)
        target = identities.get(resolved_id)
        key = (owner, declared)
        if (
            not isinstance(owner, str)
            or LOGIN_RE.fullmatch(owner) is None
            or not isinstance(alias_key, str)
            or ALIAS_KEY_RE.fullmatch(alias_key) is None
            or alias_key != _model_alias_key(owner, declared)
            or key in aliases
            or source is None
            or target is None
            or source["owner_login"] != owner
            or target["owner_login"] != owner
            or source["resolved_model_id"] != resolved_id
            or target["resolved_model_id"] != resolved_id
            or target["status"] != "approved"
        ):
            raise SystemExit("State projection: invalid model alias binding")
        label = _model_label(target["display_name"], "resolved model display name")
        aliases[key] = (model_id, resolved_id, label)
        summaries.append(
            {
                "owner_login": owner,
                "declared_label": declared,
                "model_id": model_id,
                "canonical_id": resolved_id,
                "label": label,
                "assignment_event_id": alias["assignment_event_id"],
            }
        )
    return ModelIdentityIndex(
        aliases,
        tuple(
            sorted(
                summaries,
                key=lambda item: (
                    item["owner_login"], item["declared_label"],
                    item["canonical_id"], item["label"]
                ),
            )
        ),
    )


def _canonical_identity(
    owner_login: str,
    declared_model: str,
    aliases: dict[str, dict[str, str]],
    model_identities: ModelIdentityIndex | None = None,
) -> tuple[str, str]:
    identity_index = (
        model_identities
        if model_identities is not None
        else EMPTY_MODEL_IDENTITY_INDEX
    )
    state_alias = identity_index.aliases.get(
        (owner_login.lower(), declared_model)
    )
    if state_alias is not None:
        return state_alias[1], state_alias[2]
    normalized = _normalized_model(declared_model)
    alias = aliases.get(normalized)
    if alias is None:
        return _slug(normalized), normalized
    return alias["canonical_id"], alias["label"]


def adapt_results_store(
    normalized_files: list[tuple[str, list[dict[str, Any]]]],
    aliases: dict[str, dict[str, str]],
    model_identities: ModelIdentityIndex | None = None,
) -> list[Solution]:
    """Adapt the legacy/base results store into the materialized domain shape."""

    out: list[Solution] = []
    for user, records in normalized_files:
        for record in records:
            raw_declared = record["declared_model"]
            declared = raw_declared
            identity_index = (
                model_identities
                if model_identities is not None
                else EMPTY_MODEL_IDENTITY_INDEX
            )
            reviewed = (
                user.lower(), raw_declared
            ) in identity_index.aliases
            canonical_id, canonical_label = _canonical_identity(
                user, raw_declared, aliases, identity_index
            )
            intake = record["intake"]
            submission = record["submission"]
            result_id = record.get("result_id") or _stable_legacy_id(
                (
                    user,
                    declared,
                    record["problem_id"],
                    record["statement_revision"],
                    record["accepted_at"],
                    intake,
                )
            )
            order_id = (
                f"issue-{intake['issue_number']:010d}"
                if intake.get("kind") == "issue"
                else str(intake.get("submission_id", result_id))
            )
            # `submission.public` records source visibility at intake, not a
            # durable release. Only State supplies materialized release evidence.
            out.append(
                Solution(
                    result_id=result_id,
                    problem_id=record["problem_id"],
                    statement_revision=record["statement_revision"],
                    declared_model=declared,
                    canonical_model_id=canonical_id,
                    canonical_model_label=canonical_label,
                    submitter=user,
                    accepted_at=record["accepted_at"],
                    acceptance_event_id=order_id,
                    retracted=False,
                    metadata=_metadata_fields(
                        record.get("production_metadata", {}), "declared-at-submission"
                    ),
                    provenance={
                        "source": "base-results-store",
                        "benchmark_commit": record["benchmark_commit"],
                        "intake": intake,
                        "submission": submission,
                    },
                    public_solution={"available": False, "url": None},
                    replay={"status": "unavailable", "reason": "not-materialized"},
                    release={
                        "status": "unavailable",
                        "url": None,
                        "reason": "not-materialized",
                    },
                    model_identity_reviewed=reviewed,
                )
            )
    return out


def _replay_projection_view(
    replay: dict[str, Any],
    *,
    measurement_identity: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(replay, dict) or set(replay) != REPLAY_PROJECTION_FIELDS:
        raise SystemExit("State projection: invalid replay fields")
    if (
        replay["status"] not in REPLAY_STATUSES
        or type(replay["attempt"]) is not int
        or replay["attempt"] < 0
        or (
            replay["checker"] is not None
            and (not isinstance(replay["checker"], str) or not replay["checker"])
        )
        or (
            replay["reason"] is not None
            and (not isinstance(replay["reason"], str) or not replay["reason"])
        )
    ):
        raise SystemExit("State projection: invalid replay values")
    for field in (
        "checker_wall_time_ms", "checker_retired_instructions",
        "build_wall_time_ms", "build_retired_instructions", "lines_of_code",
        "file_count",
    ):
        if replay[field] is not None and (
            type(replay[field]) is not int or replay[field] < 0
        ):
            raise SystemExit("State projection: invalid replay measurements")
    if measurement_identity is not None:
        status = replay["status"]
        reason = replay["reason"]
        expected_reasons = (
            HISTORICAL_FAILURE_REASONS
            if status == "failed"
            else HISTORICAL_UNAVAILABLE_REASONS
            if status == "unavailable"
            else None
        )
        if (
            replay["checker"] != "nanoda"
            or (expected_reasons is None and reason is not None)
            or (expected_reasons is not None and reason not in expected_reasons)
            or (
                status
                in {
                    "running", "failed", "accepted", "rejected", "declined",
                    "crashed", "timed_out",
                }
                and replay["attempt"] < 1
            )
        ):
            raise SystemExit("State projection: invalid historical replay values")
        terminal_verdict = status in {
            "accepted", "rejected", "declined", "crashed", "timed_out",
        }
        for field in (
            "checker_wall_time_ms", "build_wall_time_ms", "lines_of_code",
            "file_count",
        ):
            if terminal_verdict != (replay[field] is not None):
                raise SystemExit(
                    "State projection: incoherent historical replay measurements"
                )
        for counter, unavailable_reason in (
            (
                "checker_retired_instructions",
                "checker_retired_instructions_unavailable_reason",
            ),
            (
                "build_retired_instructions",
                "build_retired_instructions_unavailable_reason",
            ),
        ):
            counter_reason = replay[unavailable_reason]
            if (
                counter_reason is not None
                and counter_reason not in COUNTER_UNAVAILABLE_REASONS
            ):
                raise SystemExit(
                    "State projection: invalid historical counter evidence"
                )
            if terminal_verdict:
                if (replay[counter] is None) == (counter_reason is None):
                    raise SystemExit(
                        "State projection: incoherent historical counter evidence"
                    )
            elif replay[counter] is not None or counter_reason is not None:
                raise SystemExit(
                    "State projection: incoherent historical counter evidence"
                )
    view = {
        "status": replay["status"],
        "reason": replay["reason"],
        "attempt": replay["attempt"],
        "checker": replay["checker"],
    }
    measurement = {
        "kind": "checker-replay",
        "replay_status": replay["status"],
        "replay_reason": replay["reason"],
        "status": (
            "unavailable"
            if replay["checker_retired_instructions"] is None
            else "available"
        ),
        "checker": replay["checker"],
        "checker_wall_time_ms": replay["checker_wall_time_ms"],
        "checker_retired_instructions": replay[
            "checker_retired_instructions"
        ],
        "checker_retired_instructions_unavailable_reason": replay[
            "checker_retired_instructions_unavailable_reason"
        ],
        "build_wall_time_ms": replay["build_wall_time_ms"],
        "build_retired_instructions": replay["build_retired_instructions"],
        "build_retired_instructions_unavailable_reason": replay[
            "build_retired_instructions_unavailable_reason"
        ],
        "lines_of_code": replay["lines_of_code"],
        "file_count": replay["file_count"],
        "unavailable_reason": (
            "performance-counter-unavailable"
            if replay["checker_retired_instructions"] is None
            else None
        ),
        "attempt": replay["attempt"],
        **(measurement_identity or {}),
    }
    return view, measurement


def adapt_state_projection(
    raw: dict[str, Any] | None,
    aliases: dict[str, dict[str, str]],
    model_identities: ModelIdentityIndex | None = None,
) -> list[Solution]:
    """Normalize a supported cumulative redacted State projection."""

    if raw is None:
        return []
    version = raw.get("schema_version")
    if version not in {1, 4, 5, 6}:
        raise SystemExit("State domain: unsupported schema_version")
    if raw.get("environment") not in {"production", "staging"}:
        raise SystemExit("State domain: invalid environment")
    if type(raw.get("source_event_count")) is not int or raw["source_event_count"] < 0:
        raise SystemExit("State domain: invalid source_event_count")
    if not re.fullmatch(r"[0-9a-f]{64}", str(raw.get("source_digest", ""))):
        raise SystemExit("State domain: invalid source_digest")
    if not re.fullmatch(r"[0-9a-f]{40}", str(raw.get("source_state_commit", ""))):
        raise SystemExit("State projection: invalid source_state_commit")
    common_fields = {
        "schema_version", "environment", "source_state_commit",
        "source_event_count", "source_digest", "results",
    }
    expected_top_fields = common_fields
    if version in {4, 5, 6}:
        expected_top_fields |= {
            "result_overlays", "model_identities", "model_aliases",
            "model_identity_history",
        }
    if version in {5, 6}:
        expected_top_fields.add("result_amendment_history")
    if version == 6:
        expected_top_fields |= {
            "historical_replay_series", "historical_replay_unavailability",
        }
    if set(raw) != expected_top_fields:
        raise SystemExit("State projection: invalid top-level fields")
    identity_index = (
        model_identities
        if model_identities is not None
        else build_model_identity_index(raw)
    )
    solutions: list[Solution] = []
    for result in raw.get("results", []):
        required = {
            "result_id", "problem_id", "statement_revision", "declared_model",
            "submitter", "accepted_at", "acceptance_event_id", "recorded_at",
            "record_event_id", "benchmark_commit", "production_metadata", "replay",
            "release", "public_solution",
        }
        if version in {4, 5, 6}:
            required |= {"model_id", "resolved_model_id"}
        if version in {5, 6}:
            required |= {
                "effective_problem_id", "effective_statement_revision",
                "problem_repair", "applied_problem_repair", "retraction",
                "leaderboard_eligible",
            }
        if not isinstance(result, dict) or set(result) != required:
            raise SystemExit("State projection: invalid result fields")
        raw_declared = str(result["declared_model"])
        declared = raw_declared
        if result["result_id"] != expected_result_id(
            result["submitter"],
            result["declared_model"],
            result["problem_id"],
            result["statement_revision"],
        ):
            raise SystemExit("State projection: result_id does not match its identity fields")
        canonical_id, canonical_label = _canonical_identity(
            str(result["submitter"]), raw_declared, aliases, identity_index
        )
        state_resolution = identity_index.aliases.get(
            (str(result["submitter"]).lower(), raw_declared)
        )
        if version in {4, 5, 6}:
            projected_resolution = (
                result["model_id"], result["resolved_model_id"]
            )
            expected_resolution = (
                (None, None)
                if state_resolution is None
                else (state_resolution[0], state_resolution[1])
            )
            if projected_resolution != expected_resolution:
                raise SystemExit(
                    "State projection: result model identity binding is inconsistent"
                )
        replay = result["replay"]
        if replay is None:
            replay_view = {"status": "unavailable", "reason": "not-enqueued"}
            measurements: list[dict[str, Any]] = []
        else:
            replay_view, measurement = _replay_projection_view(replay)
            measurements = [measurement]
        release = result["release"]
        release_url = result["public_solution"]["url"]
        release_view = (
            {
                "status": release["status"],
                "release_at": release.get("release_at"),
                "url": release_url,
                "reason": release.get("reason_code"),
            }
            if release is not None
            else {"status": "unavailable", "reason": "not-scheduled", "url": None}
        )
        solutions.append(
            Solution(
                result_id=result["result_id"],
                problem_id=(
                    result["effective_problem_id"]
                    if version in {5, 6}
                    else result["problem_id"]
                ),
                statement_revision=(
                    result["effective_statement_revision"]
                    if version in {5, 6}
                    else result["statement_revision"]
                ),
                declared_model=declared,
                canonical_model_id=canonical_id,
                canonical_model_label=canonical_label,
                submitter=result["submitter"],
                accepted_at=result["accepted_at"],
                acceptance_event_id=result["acceptance_event_id"],
                retracted=(
                    not result["leaderboard_eligible"]
                    if version in {5, 6}
                    else False
                ),
                metadata=_metadata_fields(
                    result.get("production_metadata", {}),
                    "declared-at-submission",
                ),
                provenance={
                    "source": "public-state-projection",
                    "state_event_id": result["record_event_id"],
                    "benchmark_commit": result["benchmark_commit"],
                },
                public_solution={
                    "available": result["public_solution"]["available"],
                    "url": release_view.get("url"),
                },
                replay=replay_view,
                measurements=measurements,
                release=release_view,
                model_identity_reviewed=state_resolution is not None,
            )
        )
    return solutions


def merge_solutions(primary: list[Solution], fallback: list[Solution]) -> list[Solution]:
    """Prefer State records and retain unmatched base-store records."""

    primary_base_keys = {
        (
            solution.submitter,
            solution.declared_model,
            solution.problem_id,
            solution.statement_revision,
        )
        for solution in primary
    }
    merged = {
        solution.result_id: solution
        for solution in fallback
        if (
            solution.submitter,
            solution.declared_model,
            solution.problem_id,
            solution.statement_revision,
        )
        not in primary_base_keys
    }
    for solution in primary:
        merged[solution.result_id] = solution
    return sorted(merged.values(), key=_acceptance_key)


def apply_state_projection_overlays(
    solutions: list[Solution], raw: dict[str, Any] | None
) -> list[Solution]:
    """Apply redacted legacy overlays and historical replay series in place."""

    if raw is None or raw.get("schema_version") == 1:
        return solutions
    version = raw.get("schema_version")
    if version not in {4, 5, 6}:
        raise SystemExit("State domain: unsupported schema_version")
    by_result = {solution.result_id: solution for solution in solutions}
    if len(by_result) != len(solutions):
        raise SystemExit("State projection: duplicate materialized result_id")

    seen_overlays: set[str] = set()
    expected_overlay_fields = STATE_OVERLAY_FIELDS | (
        STATE_AMENDMENT_FIELDS if version in {5, 6} else set()
    )
    for overlay in raw["result_overlays"]:
        if not isinstance(overlay, dict) or set(overlay) != expected_overlay_fields:
            raise SystemExit("State projection: invalid result overlay fields")
        result_id_value = overlay["result_id"]
        solution = by_result.get(result_id_value)
        if solution is None or result_id_value in seen_overlays:
            raise SystemExit("State projection: unknown or duplicate result overlay")
        seen_overlays.add(result_id_value)
        if (
            overlay["owner_login"] != solution.submitter.lower()
            or overlay["declared_model"] != solution.declared_model
            or overlay["problem_id"] != solution.problem_id
            or overlay["statement_revision"] != solution.statement_revision
            or not isinstance(overlay["metadata"], dict)
        ):
            raise SystemExit("State projection: result overlay identity mismatch")
        solution.metadata = dict(overlay["metadata"])
        solution.provenance["state_claim_event_id"] = overlay["claim_event_id"]
        solution.provenance["state_mutation_event_id"] = overlay[
            "mutation_event_id"
        ]
        if version in {5, 6}:
            if (
                not isinstance(overlay["effective_problem_id"], str)
                or type(overlay["effective_statement_revision"]) is not int
                or overlay["effective_statement_revision"] < 1
                or not isinstance(overlay["leaderboard_eligible"], bool)
            ):
                raise SystemExit("State projection: invalid overlay amendment")
            solution.problem_id = overlay["effective_problem_id"]
            solution.statement_revision = overlay[
                "effective_statement_revision"
            ]
            solution.retracted = not overlay["leaderboard_eligible"]

    if version != 6:
        return solutions

    def expected_historical_visibility(result_id_value: str) -> str:
        solution = by_result[result_id_value]
        submission = solution.provenance.get("submission")
        if (
            solution.provenance.get("source") != "base-results-store"
            or not isinstance(submission, dict)
            or not isinstance(submission.get("public"), bool)
        ):
            raise SystemExit(
                "State projection: historical replay does not target a base result"
            )
        return "public" if submission["public"] else "private"

    def validate_historical_identity(
        item: dict[str, Any], result_id_value: str
    ) -> None:
        solution = by_result[result_id_value]
        if (
            not isinstance(item["owner_login"], str)
            or not LOGIN_RE.fullmatch(item["owner_login"])
            or not isinstance(item["declared_model"], str)
            or not item["declared_model"]
            or not isinstance(item["problem_id"], str)
            or not item["problem_id"]
            or type(item["statement_revision"]) is not int
            or item["statement_revision"] < 1
            or not isinstance(item["historical_accepted_at"], str)
            or not re.fullmatch(
                r"(?!0000-)[0-9]{4}-[0-9]{2}-[0-9]{2}T"
                r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
                item["historical_accepted_at"],
            )
            or expected_result_id(
                item["owner_login"],
                item["declared_model"],
                item["problem_id"],
                item["statement_revision"],
            )
            != result_id_value
            or item["owner_login"] != solution.submitter.lower()
            or item["declared_model"] != solution.declared_model
            or item["historical_accepted_at"] != solution.accepted_at
        ):
            raise SystemExit("State projection: historical result identity mismatch")

    series_by_result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_series: set[tuple[str, str]] = set()
    transition_event_ids: set[str] = set()
    series_order: list[tuple[str, str, str, str]] = []
    for series in raw["historical_replay_series"]:
        if not isinstance(series, dict) or set(series) != HISTORICAL_REPLAY_SERIES_FIELDS:
            raise SystemExit("State projection: invalid historical replay series fields")
        result_id_value = series["result_id"]
        replay_task_id = series["replay_task_id"]
        identity = (result_id_value, replay_task_id)
        if (
            not isinstance(result_id_value, str)
            or RESULT_ID_RE.fullmatch(result_id_value) is None
            or result_id_value not in by_result
            or not isinstance(replay_task_id, str)
            or REPLAY_TASK_ID_RE.fullmatch(replay_task_id) is None
            or identity in seen_series
            or series["source_visibility"] not in {"public", "private"}
            or series["source_visibility"]
            != expected_historical_visibility(result_id_value)
            or not isinstance(series["measurement_config_digest"], str)
            or DIGEST_RE.fullmatch(series["measurement_config_digest"]) is None
            or not isinstance(series["execution_profile_digest"], str)
            or DIGEST_RE.fullmatch(series["execution_profile_digest"]) is None
            or not isinstance(series["updated_at"], str)
            or STATE_TIMESTAMP_RE.fullmatch(series["updated_at"]) is None
            or not isinstance(series["transition_event_id"], str)
            or EVENT_ID_RE.fullmatch(series["transition_event_id"]) is None
            or series["transition_event_id"] in transition_event_ids
            or replay_task_id
            != _expected_replay_task_id(
                result_id_value, series["measurement_config_digest"]
            )
        ):
            raise SystemExit("State projection: invalid historical replay series")
        validate_historical_identity(series, result_id_value)
        seen_series.add(identity)
        transition_event_ids.add(series["transition_event_id"])
        series_order.append(
            (
                result_id_value,
                replay_task_id,
                series["measurement_config_digest"],
                series["execution_profile_digest"],
            )
        )
        series_by_result[result_id_value].append(series)
    if series_order != sorted(series_order):
        raise SystemExit("State projection: historical replay series are not sorted")

    dispositions: dict[str, dict[str, Any]] = {}
    disposition_order: list[str] = []
    for disposition in raw["historical_replay_unavailability"]:
        if (
            not isinstance(disposition, dict)
            or set(disposition) != HISTORICAL_REPLAY_UNAVAILABILITY_FIELDS
        ):
            raise SystemExit("State projection: invalid historical disposition fields")
        result_id_value = disposition["result_id"]
        if (
            not isinstance(result_id_value, str)
            or RESULT_ID_RE.fullmatch(result_id_value) is None
            or result_id_value not in by_result
            or result_id_value in dispositions
            or result_id_value in series_by_result
            or disposition["source_visibility"] not in {"public", "private"}
            or disposition["source_visibility"]
            != expected_historical_visibility(result_id_value)
            or not isinstance(disposition["disposed_at"], str)
            or STATE_TIMESTAMP_RE.fullmatch(disposition["disposed_at"]) is None
            or not isinstance(disposition["disposition_event_id"], str)
            or EVENT_ID_RE.fullmatch(disposition["disposition_event_id"]) is None
            or disposition["disposition_event_id"] in transition_event_ids
            or not isinstance(disposition["reason"], str)
            or not disposition["reason"]
            or (
                disposition["rationale"] is not None
                and (
                    not isinstance(disposition["rationale"], str)
                    or not disposition["rationale"]
                )
            )
        ):
            raise SystemExit("State projection: invalid historical disposition")
        validate_historical_identity(disposition, result_id_value)
        expected_disposition = (
            (
                "source_ref_permanently_unavailable",
                "accepted_immutable_source_ref_unavailable_without_archive",
            )
            if disposition["source_visibility"] == "public"
            else ("archive_not_found", None)
        )
        if (disposition["reason"], disposition["rationale"]) != expected_disposition:
            raise SystemExit("State projection: invalid historical disposition")
        disposition_order.append(result_id_value)
        transition_event_ids.add(disposition["disposition_event_id"])
        dispositions[result_id_value] = disposition
    if disposition_order != sorted(disposition_order):
        raise SystemExit("State projection: historical dispositions are not sorted")

    for result_id_value, series_items in series_by_result.items():
        lanes = {item["source_visibility"] for item in series_items}
        if len(lanes) != 1:
            raise SystemExit("State projection: historical replay lane changed")
        solution = by_result[result_id_value]
        measurements: list[dict[str, Any]] = []
        summaries: list[tuple[tuple[str, str, str], dict[str, Any]]] = []
        for series in series_items:
            summary, measurement = _replay_projection_view(
                series["replay"],
                measurement_identity={
                    key: series[key]
                    for key in (
                        "source_visibility", "replay_task_id",
                        "measurement_config_digest", "execution_profile_digest",
                        "updated_at", "transition_event_id",
                    )
                },
            )
            measurements.append(measurement)
            summaries.append(
                (
                    (
                        series["updated_at"], series["transition_event_id"],
                        series["replay_task_id"],
                    ),
                    summary,
                )
            )
        solution.measurements = measurements
        solution.replay = max(summaries, key=lambda item: item[0])[1]

    for result_id_value, disposition in dispositions.items():
        solution = by_result[result_id_value]
        solution.replay = {
            "status": "unavailable",
            "reason": disposition["reason"],
        }
        solution.measurements = []
    return solutions


def _scope_problem_ids(
    group_id: str,
    problems: list[Any],
    set_definitions: list[SetDefinition],
) -> tuple[list[dict[str, Any]], str]:
    problem_by_id = {problem.id: problem for problem in problems}
    scopes: list[dict[str, Any]] = []
    frozen: list[dict[str, Any]] = []
    for set_def in set_definitions:
        members = [
            {"problem_id": problem_id, "statement_revision": revision}
            for problem_id, revision in set_def.members
            if problem_id in problem_by_id
            and problem_by_id[problem_id].group == group_id
            and problem_by_id[problem_id].visible
        ]
        if not members:
            continue
        scope = {
            "id": set_def.id,
            "label": set_def.title,
            "kind": "frozen-set",
            "frozen": set_def.frozen,
            "published_at": set_def.published_at,
            "members": members,
        }
        scopes.append(scope)
        if set_def.frozen:
            frozen.append(scope)
    statuses = [
        status
        for status in ("draft", "active", "archived", "resolved")
        if any(
            problem.group == group_id
            and problem.visible
            and problem.status == status
            for problem in problems
        )
    ]
    for status in statuses:
        scopes.append(
            {
                "id": status,
                "label": STATUS_LABELS[status],
                "kind": "current-status",
                "frozen": False,
                "published_at": None,
                "members": [
                    {
                        "problem_id": problem.id,
                        "statement_revision": problem.statement_revision,
                    }
                    for problem in problems
                    if problem.group == group_id
                    and problem.visible
                    and problem.status == status
                ],
            }
        )
    if frozen:
        default_scope = max(
            frozen, key=lambda scope: (scope["published_at"] or "", scope["id"])
        )["id"]
    elif "draft" in statuses:
        default_scope = "draft"
    elif statuses:
        default_scope = statuses[0]
    else:
        default_scope = "none"
    for scope in scopes:
        scope["flagship"] = scope["id"] == default_scope and scope["kind"] == "frozen-set"
    return scopes, default_scope


def _deduplicated_credits(solutions: list[Solution]) -> list[Solution]:
    credits: dict[tuple[str, str], Solution] = {}
    for solution in solutions:
        if solution.retracted:
            continue
        key = (solution.canonical_model_id, solution.problem_id)
        if key not in credits or _acceptance_key(solution) < _acceptance_key(credits[key]):
            credits[key] = solution
    return sorted(credits.values(), key=_acceptance_key)


def _first_result_ids(solutions: list[Solution]) -> set[str]:
    first: dict[str, Solution] = {}
    for solution in _deduplicated_credits(solutions):
        current = first.get(solution.problem_id)
        if current is None or _acceptance_key(solution) < _acceptance_key(current):
            first[solution.problem_id] = solution
    return {solution.result_id for solution in first.values()}


def _standings(
    credits: list[Solution], members: set[tuple[str, int]]
) -> list[dict[str, Any]]:
    selected = [
        credit
        for credit in credits
        if (credit.problem_id, credit.statement_revision) in members
    ]
    solvers_by_problem: dict[str, set[str]] = defaultdict(set)
    for credit in selected:
        solvers_by_problem[credit.problem_id].add(credit.canonical_model_id)
    first_ids = _first_result_ids(selected)
    by_model: dict[str, list[Solution]] = defaultdict(list)
    for credit in selected:
        by_model[credit.canonical_model_id].append(credit)
    rows = []
    for model_id, model_credits in by_model.items():
        rows.append(
            {
                "canonical_model_id": model_id,
                "model_label": model_credits[0].canonical_model_label,
                "counts": {
                    "unique": sum(
                        len(solvers_by_problem[item.problem_id]) == 1
                        for item in model_credits
                    ),
                    "first": sum(item.result_id in first_ids for item in model_credits),
                    "total": len(model_credits),
                },
                "problem_ids": sorted(item.problem_id for item in model_credits),
                "submitters": sorted({item.submitter for item in model_credits}),
            }
        )
    rows.sort(
        key=lambda row: (
            -row["counts"]["unique"],
            -row["counts"]["first"],
            -row["counts"]["total"],
            row["model_label"].lower(),
            row["canonical_model_id"],
        )
    )
    return rows


def _problem_lifecycle(problem: Any, fixture: dict[str, Any]) -> dict[str, Any]:
    override = fixture.get("problem_lifecycle", {}).get(problem.id, {})
    catalog_status_history = getattr(problem, "status_history", ())
    catalog_revision_history = getattr(problem, "revision_history", ())
    history = (
        [
            {
                "status": entry["status"],
                "effective_at": entry["effective_date"],
                "reason": entry["reason"],
                "source": "catalog-manifest",
            }
            for entry in catalog_status_history
        ]
        if catalog_status_history
        else [dict(entry) for entry in override.get("status_history", [])]
    )
    revisions = (
        [
            {
                "revision": entry["revision"],
                "status": (
                    "current"
                    if entry["revision"] == problem.statement_revision
                    else "superseded"
                ),
                "effective_at": entry["effective_date"],
                "reason": entry["reason"],
                "statement_digest": entry["statement_digest"],
                "source": "catalog-manifest",
            }
            for entry in catalog_revision_history
        ]
        if catalog_revision_history
        else [dict(entry) for entry in override.get("statement_revisions", [])]
    )
    return {"status_history": history, "statement_revisions": revisions}


def _solution_payload(solution: Solution, first_ids: set[str]) -> dict[str, Any]:
    return {
        "result_id": solution.result_id,
        "problem_id": solution.problem_id,
        "statement_revision": solution.statement_revision,
        "canonical_credit": {
            "id": solution.canonical_model_id,
            "label": solution.canonical_model_label,
            "declared_label": solution.declared_model,
        },
        "submitter": solution.submitter,
        "accepted_at": solution.accepted_at,
        "acceptance_event_id": solution.acceptance_event_id,
        "first_solve": solution.result_id in first_ids,
        "retracted": solution.retracted,
        "metadata": solution.metadata,
        "provenance": solution.provenance,
        "public_solution": solution.public_solution,
        "replay": solution.replay,
        "measurements": solution.measurements,
        "release": solution.release,
    }


def build_lifecycle_projection(
    *,
    problems: list[Any],
    solutions: list[Solution],
    set_definitions: list[SetDefinition],
    tag_registry: dict[str, dict[str, str]],
    fixture: dict[str, Any],
    generated_at: str,
    benchmark_commit: str,
    state_commit: str | None,
    state_metadata: dict[str, Any] | None,
    site_base_url: str,
    model_aliases: tuple[dict[str, str], ...] = (),
) -> dict[str, Any]:
    """Return path→payload for every schema-version-2 JSON file and RSS."""

    fixture_metadata = fixture.get("metadata_amendments", {})
    fixture_retractions = set(fixture.get("retracted_result_ids", []))
    for solution in solutions:
        for key, amendment in fixture_metadata.get(solution.result_id, {}).items():
            if amendment.get("provenance") not in {"declared-at-submission", "backfilled"}:
                raise SystemExit(
                    f"preview fixture metadata {solution.result_id}/{key} has invalid provenance"
                )
            solution.metadata[key] = dict(amendment)
        if solution.result_id in fixture_retractions:
            solution.retracted = True

    problem_ids = [problem.id for problem in problems]
    if len(problem_ids) != len(set(problem_ids)):
        raise SystemExit("lifecycle-aware projection: duplicate catalog problem id")
    for problem in problems:
        if problem.group not in GROUP_BY_ID:
            raise SystemExit(
                f"lifecycle-aware projection: unsupported group {problem.group!r} for {problem.id}"
            )
        unknown_tags = set(problem.tags) - set(tag_registry)
        if unknown_tags:
            raise SystemExit(
                f"lifecycle-aware projection: unregistered tags for {problem.id}: {sorted(unknown_tags)}"
            )
    visible = [problem for problem in problems if problem.visible]
    visible_ids = {problem.id for problem in visible}
    solutions = [solution for solution in solutions if solution.problem_id in visible_ids]
    credits = _deduplicated_credits(solutions)
    first_ids = _first_result_ids(solutions)
    problem_lifecycles = {
        problem.id: _problem_lifecycle(problem, fixture) for problem in visible
    }
    limitations: list[str] = []
    if not state_commit:
        limitations.append(
            "The redacted production State projection was unavailable; base results were adapted and replay/release states are explicitly unavailable."
        )
    elif any(
        solution.provenance.get("source") == "base-results-store"
        for solution in solutions
    ):
        limitations.append(
            "Results absent from modern State result materialization were adapted from the immutable base-results store. Historical replay or disposition evidence is applied where State supplies it; otherwise replay is explicitly unavailable, and release remains unavailable."
        )
    if not any(
        lifecycle["status_history"] or lifecycle["statement_revisions"]
        for lifecycle in problem_lifecycles.values()
    ):
        limitations.append(
            "The pinned catalog records no lifecycle history for any visible problem; current fields are reported separately and no history entry is fabricated."
        )
    published_model_aliases = list(model_aliases) or fixture.get(
        "model_aliases", []
    )
    if any(not solution.model_identity_reviewed for solution in solutions):
        limitations.append(
            "Some results have no reviewed State model alias; their normalized declared model labels are used as fallback credit identities."
        )

    files: dict[str, Any] = {}
    group_indexes: list[dict[str, Any]] = []
    problem_by_id = {problem.id: problem for problem in visible}
    member_sets: dict[tuple[str, int], list[SetDefinition]] = defaultdict(list)
    for set_def in set_definitions:
        member_groups = {
            problem_by_id[problem_id].group
            for problem_id, _revision in set_def.members
            if problem_id in problem_by_id
        }
        if len(member_groups) > 1:
            raise SystemExit(f"named set {set_def.id!r} spans multiple problem groups")
        for member in set_def.members:
            member_sets[member].append(set_def)

    for group in GROUPS:
        group_problems = [problem for problem in visible if problem.group == group["id"]]
        scopes, default_scope = _scope_problem_ids(group["id"], visible, set_definitions)
        problem_summaries = []
        for problem in group_problems:
            membership = [
                set_def.id
                for set_def in member_sets[(problem.id, problem.statement_revision)]
            ]
            problem_summaries.append(
                {
                    "id": problem.id,
                    "title": problem.title,
                    "status": problem.status,
                    "statement_revision": problem.statement_revision,
                    "tags": list(problem.tags),
                    "sets": membership,
                    "url": f"problems/{quote(problem.id, safe='')}/",
                    "stable_url": f"problems/{quote(problem.id, safe='')}/",
                    "sort_index": problem.sort_index,
                }
            )
        default_members = next(
            (
                {
                    (member["problem_id"], member["statement_revision"])
                    for member in scope["members"]
                }
                for scope in scopes
                if scope["id"] == default_scope
            ),
            set(),
        )
        group_credits = [
            credit
            for credit in credits
            if credit.problem_id in {problem.id for problem in group_problems}
        ]
        group_payload = {
            "schema_version": 2,
            "generated_at": generated_at,
            "group": group,
            "default_scope": default_scope,
            "scopes": scopes,
            "tags": [
                {"id": tag, **tag_registry.get(tag, {"label": tag, "description": ""})}
                for tag in sorted({tag for problem in group_problems for tag in problem.tags})
            ],
            "problems": sorted(problem_summaries, key=lambda item: item["sort_index"]),
            "credits": [
                {
                    "result_id": credit.result_id,
                    "problem_id": credit.problem_id,
                    "statement_revision": credit.statement_revision,
                    "canonical_model_id": credit.canonical_model_id,
                    "model_label": credit.canonical_model_label,
                    "submitter": credit.submitter,
                    "accepted_at": credit.accepted_at,
                    "acceptance_event_id": credit.acceptance_event_id,
                    "first_solve": credit.result_id in first_ids,
                }
                for credit in group_credits
            ],
            "standings": _standings(group_credits, default_members),
            "standings_default_sort": "unique",
            "data_limitations": limitations,
        }
        path = f"v2/groups/{group['id']}.json"
        files[path] = group_payload
        group_indexes.append(
            {
                **group,
                "default_scope": default_scope,
                "problem_count": len(group_problems),
                "solution_count": len(group_credits),
                "data_url": f"site-data/{path}",
                "url": f"{group['id']}/",
            }
        )

    for problem in visible:
        problem_solutions = [item for item in solutions if item.problem_id == problem.id]
        lifecycle = problem_lifecycles[problem.id]
        problem_limitations = list(limitations)
        if not lifecycle["status_history"]:
            problem_limitations.append(
                "No status transition history is recorded for this problem; current_status is reported separately and no history entry is fabricated."
            )
        if not lifecycle["statement_revisions"]:
            problem_limitations.append(
                "No statement revision history is recorded for this problem; statement_revision is reported separately and no history entry is fabricated."
            )
        files[f"v2/problems/{problem.id}.json"] = {
            "schema_version": 2,
            "generated_at": generated_at,
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "group": problem.group,
                "current_status": problem.status,
                "visible": problem.visible,
                "statement_revision": problem.statement_revision,
                "tags": list(problem.tags),
                "submitter": problem.submitter,
                "module": problem.module,
                "notes": problem.notes,
                "source": problem.source,
                "informal_solution": problem.informal_solution,
                "stable_url": f"problems/{quote(problem.id, safe='')}/",
                "preview_url": f"preview/problems/{quote(problem.id, safe='')}/",
            },
            "lifecycle": lifecycle,
            "sets": [
                {
                    "id": set_def.id,
                    "title": set_def.title,
                    "frozen": set_def.frozen,
                    "published_at": set_def.published_at,
                    "statement_revision": problem.statement_revision,
                }
                for set_def in member_sets[(problem.id, problem.statement_revision)]
            ],
            "solutions": [
                _solution_payload(solution, first_ids)
                for solution in sorted(problem_solutions, key=_acceptance_key)
            ],
            "data_limitations": problem_limitations,
        }

    recent = sorted(solutions, key=_acceptance_key, reverse=True)
    recent_payload = {
        "schema_version": 2,
        "generated_at": generated_at,
        "solutions": [
            {
                **_solution_payload(solution, first_ids),
                "group": problem_by_id[solution.problem_id].group,
                "problem_title": problem_by_id[solution.problem_id].title,
                "problem_url": f"problems/{quote(solution.problem_id, safe='')}/",
            }
            for solution in recent
            if not solution.retracted
        ],
        "data_limitations": limitations,
    }
    files["v2/recent-solutions.json"] = recent_payload
    files["v2/index.json"] = {
        "schema_version": 2,
        "generated_at": generated_at,
        "benchmark": {"repo": "leanprover/lean-eval", "commit": benchmark_commit},
        "state": {
            "repo": "leanprover/lean-eval-state",
            "commit": state_commit,
            "materialized": state_commit is not None,
            "environment": (state_metadata or {}).get("environment"),
            "source_event_count": (state_metadata or {}).get("source_event_count"),
            "source_digest": (state_metadata or {}).get("source_digest"),
        },
        "default_group": "formalization-evaluation",
        "model_aliases": sorted(
            published_model_aliases,
            key=lambda alias: (
                alias["canonical_id"], alias["declared_label"], alias["label"]
            ),
        ),
        "groups": group_indexes,
        "recent_solutions_url": "site-data/v2/recent-solutions.json",
        "recent_solutions_rss_url": "site-data/v2/recent-solutions.xml",
        "data_limitations": limitations,
    }
    files["v2/recent-solutions.xml"] = build_recent_rss(
        recent_payload, site_base_url
    )
    return files


def build_recent_rss(payload: dict[str, Any], site_base_url: str) -> str:
    base = site_base_url.rstrip("/") + "/"
    items = []
    for solution in payload["solutions"][:50]:
        title = (
            f"{solution['canonical_credit']['label']} solved "
            f"{solution['problem_title']}"
        )
        link = base + solution["problem_url"]
        description = (
            f"Submitted by @{solution['submitter']} in "
            f"{GROUP_BY_ID[solution['group']]['label']}."
        )
        items.append(
            "\n".join(
                [
                    "    <item>",
                    f"      <title>{xml_escape(title)}</title>",
                    f"      <link>{xml_escape(link)}</link>",
                    f"      <guid isPermaLink=\"false\">{xml_escape(solution['result_id'])}</guid>",
                    f"      <pubDate>{xml_escape(_rss_date(solution['accepted_at']))}</pubDate>",
                    f"      <description>{xml_escape(description)}</description>",
                    "    </item>",
                ]
            )
        )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<rss version=\"2.0\">\n"
        "  <channel>\n"
        "    <title>LeanEval recent solutions</title>\n"
        f"    <link>{xml_escape(base + 'recent/')}</link>\n"
        "    <description>Recently accepted LeanEval solutions</description>\n"
        + ("\n".join(items) + "\n" if items else "")
        + "  </channel>\n</rss>\n"
    )


def _rss_date(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.strftime("%a, %d %b %Y %H:%M:%S +0000")

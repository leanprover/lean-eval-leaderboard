#!/usr/bin/env python3
"""Build the split, client-facing lifecycle-aware leaderboard projection.

The adapter deliberately consumes only materialized State data.  It never reads
the append-only event log and it never executes submission source.  While the
production State projection lacks lifecycle/amendment fields, catalog metadata
and optional schema-versioned preview fixtures fill those presentation fields;
every such fallback is recorded in ``data_limitations``.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from html import escape as xml_escape
from typing import Any, Iterable
from urllib.parse import quote


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
        "id": "open-conjectures",
        "label": "Open conjectures",
        "policy": "Public-source submissions; resolved statements retain their frozen-set history.",
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


def _slug(value: str) -> str:
    return SLUG_RE.sub("-", value.lower()).strip("-") or "unknown-model"


def _normalized_model(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _stable_legacy_id(parts: Iterable[object]) -> str:
    encoded = "\0".join(str(part) for part in parts).encode("utf-8")
    return "legacy_" + hashlib.sha256(encoded).hexdigest()


def _acceptance_key(solution: "Solution") -> tuple[str, str, str]:
    return (solution.accepted_at, solution.acceptance_event_id, solution.result_id)


@dataclass(frozen=True)
class SetDefinition:
    id: str
    title: str
    frozen: bool
    published_at: str | None
    members: tuple[tuple[str, int], ...]


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


def _canonical_identity(
    declared_model: str, aliases: dict[str, dict[str, str]]
) -> tuple[str, str]:
    normalized = _normalized_model(declared_model)
    alias = aliases.get(normalized)
    if alias is None:
        return _slug(normalized), normalized
    return alias["canonical_id"], alias["label"]


def adapt_results_store(
    normalized_files: list[tuple[str, list[dict[str, Any]]]],
    aliases: dict[str, dict[str, str]],
) -> list[Solution]:
    """Adapt the legacy/base results store into the materialized domain shape."""

    out: list[Solution] = []
    for user, records in normalized_files:
        for record in records:
            declared = _normalized_model(record["declared_model"])
            canonical_id, canonical_label = _canonical_identity(declared, aliases)
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
            public = bool(submission.get("public"))
            url = None
            if public and submission.get("kind") == "gist":
                url = f"https://gist.github.com/{submission['repo']}/{submission['ref']}"
            elif public:
                url = (
                    f"https://github.com/{submission['repo']}/tree/"
                    f"{submission['ref']}/generated/{record['problem_id']}"
                )
            order_id = (
                f"issue-{intake['issue_number']:010d}"
                if intake.get("kind") == "issue"
                else str(intake.get("submission_id", result_id))
            )
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
                    public_solution={"available": public, "url": url},
                    replay={"status": "unavailable", "reason": "not-materialized"},
                    release={
                        "status": "released" if public else "unavailable",
                        "url": url,
                        "reason": None if public else "not-materialized",
                    },
                )
            )
    return out


def adapt_state_domain(
    raw: dict[str, Any] | None,
    aliases: dict[str, dict[str, str]],
) -> list[Solution]:
    """Normalize the public ``materialized/domain.json`` State projection."""

    if raw is None:
        return []
    if raw.get("schema_version") != 1:
        raise SystemExit("State domain: unsupported schema_version")
    if raw.get("environment") not in {"production", "staging"}:
        raise SystemExit("State domain: invalid environment")
    if type(raw.get("source_event_count")) is not int or raw["source_event_count"] < 0:
        raise SystemExit("State domain: invalid source_event_count")
    if not re.fullmatch(r"[0-9a-f]{64}", str(raw.get("source_digest", ""))):
        raise SystemExit("State domain: invalid source_digest")
    submissions = {item["submission_id"]: item for item in raw.get("submissions", [])}
    replay_by_result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for replay in raw.get("replay_tasks", []):
        replay_by_result[replay["result_id"]].append(replay)
    release_by_result = {
        item["result_id"]: item for item in raw.get("release_tasks", [])
    }
    solutions: list[Solution] = []
    for result in raw.get("results", []):
        submission = submissions.get(result["submission_id"])
        if submission is None:
            raise SystemExit(
                f"State domain: result {result['result_id']} has no submission"
            )
        declared = _normalized_model(
            str(result.get("declared_model", submission["declared_model"]))
        )
        canonical_id, canonical_label = _canonical_identity(declared, aliases)
        replay_tasks = sorted(
            replay_by_result.get(result["result_id"], []),
            key=lambda task: (task.get("occurred_at", ""), task["replay_task_id"]),
        )
        replay = replay_tasks[-1] if replay_tasks else None
        if replay is None:
            replay_view = {"status": "unavailable", "reason": "not-enqueued"}
            measurements: list[dict[str, Any]] = []
        else:
            replay_view = {
                "status": replay["status"],
                "reason": replay.get("reason_code"),
                "attempt": replay.get("attempt", 0),
                "checker": replay.get("checker"),
            }
            measurements = [
                {
                    "kind": "checker-replay",
                    "status": (
                        "unavailable"
                        if replay.get("retired_instructions") is None
                        else "available"
                    ),
                    "checker": replay.get("checker"),
                    "wall_time_ms": replay.get("wall_time_ms"),
                    "retired_instructions": replay.get("retired_instructions"),
                    "unavailable_reason": (
                        "performance-counter-unavailable"
                        if replay.get("retired_instructions") is None
                        else None
                    ),
                    "attempt": replay.get("attempt", 0),
                }
            ]
        release = release_by_result.get(result["result_id"])
        release_url = None
        if release is not None and release.get("status") == "published":
            release_url = (
                "https://github.com/leanprover/lean-eval-releases/tree/"
                f"{release.get('repository_commit', '')}/{quote(str(release.get('path', '')), safe='/')}"
            )
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
        evaluation = submission.get("evaluation", {})
        accepted_at = evaluation.get("occurred_at", result["recorded_at"])
        acceptance_event_id = evaluation.get("event_id", result["event_id"])
        solutions.append(
            Solution(
                result_id=result["result_id"],
                problem_id=result["problem_id"],
                statement_revision=result["statement_revision"],
                declared_model=declared,
                canonical_model_id=canonical_id,
                canonical_model_label=canonical_label,
                submitter=submission["actor"],
                accepted_at=accepted_at,
                acceptance_event_id=acceptance_event_id,
                retracted=bool(result.get("retracted", False)),
                metadata=_metadata_fields(
                    submission.get("production_metadata", {}),
                    "declared-at-submission",
                ),
                provenance={
                    "source": "state-materialized-domain",
                    "state_event_id": result["event_id"],
                    "submission_id": result["submission_id"],
                    "benchmark_commit": submission.get("evaluation", {}).get(
                        "benchmark_commit"
                    ),
                },
                public_solution={
                    "available": release_view.get("status") == "published",
                    "url": release_view.get("url"),
                },
                replay=replay_view,
                measurements=measurements,
                release=release_view,
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
    history = override.get("status_history") or [
        {
            "status": problem.status,
            "effective_at": None,
            "source": "catalog-current-state",
        }
    ]
    revisions = override.get("statement_revisions") or [
        {
            "revision": problem.statement_revision,
            "status": "current",
            "source": "catalog-current-state",
        }
    ]
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


def build_v2_projection(
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
    limitations: list[str] = []
    if not state_commit:
        limitations.append(
            "Production State materialized-domain data was unavailable; base results were adapted and replay/release states are explicitly unavailable."
        )
    elif any(
        solution.provenance.get("source") == "base-results-store"
        for solution in solutions
    ):
        limitations.append(
            "Results not yet present in the State materialized domain were adapted from the immutable base-results store; their replay/release states are explicitly unavailable."
        )
    if not fixture.get("problem_lifecycle"):
        limitations.append(
            "Production State does not yet materialize lifecycle histories; the preview shows the current catalog status as a one-entry history."
        )
    if not fixture.get("model_aliases"):
        limitations.append(
            "Production State does not yet materialize model aliases; normalized declared model labels are used as canonical credit identities."
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
        lifecycle = _problem_lifecycle(problem, fixture)
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
            "data_limitations": limitations,
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
            fixture.get("model_aliases", []),
            key=lambda alias: (alias["canonical_id"], alias["declared_label"]),
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

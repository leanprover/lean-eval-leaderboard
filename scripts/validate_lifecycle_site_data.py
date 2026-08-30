#!/usr/bin/env python3
"""Validate lifecycle-aware site-data schema version 2 without dependencies."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from typing import Any

GROUPS = {
    "formalization-evaluation",
    "software-verification",
    "open-problems",
}
CATALOG_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
STATEMENT_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
REPLAY_TASK_ID_RE = re.compile(r"rt1_[0-9a-f]{64}")
DIGEST_RE = re.compile(r"[0-9a-f]{64}")
EVENT_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
STATE_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z"
)
REPLAY_STATUSES = {
    "queued", "running", "accepted", "rejected", "declined", "crashed",
    "timed_out", "failed", "unavailable",
}
MEASUREMENT_CORE_FIELDS = {
    "kind", "replay_status", "replay_reason", "status", "checker",
    "checker_wall_time_ms", "checker_retired_instructions",
    "checker_retired_instructions_unavailable_reason", "build_wall_time_ms",
    "build_retired_instructions", "build_retired_instructions_unavailable_reason",
    "lines_of_code", "file_count", "unavailable_reason", "attempt",
}
MEASUREMENT_SERIES_FIELDS = {
    "source_visibility", "replay_task_id", "measurement_config_digest",
    "execution_profile_digest", "updated_at", "transition_event_id",
}
CATALOG_REASONS = {
    "initial",
    "statement-change",
    "policy",
    "correction",
    "retraction",
    "restoration",
}


class ContractError(ValueError):
    pass


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path}: top-level value must be an object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def catalog_date(value: Any, message: str) -> str:
    require(
        isinstance(value, str) and CATALOG_DATE_RE.fullmatch(value) is not None,
        message,
    )
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ContractError(message) from error
    require(parsed.isoformat() == value, message)
    return value


def validate_measurements(path: pathlib.Path, solution: dict[str, Any]) -> None:
    measurements = solution.get("measurements")
    require(isinstance(measurements, list), f"{path}: measurements must be an array")
    series_order: list[tuple[str, str, str]] = []
    replay_task_ids: set[str] = set()
    transition_event_ids: set[str] = set()
    for index, measurement in enumerate(measurements):
        label = f"{path}: measurement {index}"
        require(isinstance(measurement, dict), f"{label} must be an object")
        fields = set(measurement)
        require(
            fields == MEASUREMENT_CORE_FIELDS
            or fields == MEASUREMENT_CORE_FIELDS | MEASUREMENT_SERIES_FIELDS,
            f"{label} fields are invalid",
        )
        require(measurement["kind"] == "checker-replay", f"{label} kind is invalid")
        require(
            measurement["replay_status"] in REPLAY_STATUSES,
            f"{label} replay status is invalid",
        )
        require(
            measurement["replay_reason"] is None
            or isinstance(measurement["replay_reason"], str)
            and bool(measurement["replay_reason"]),
            f"{label} replay reason is invalid",
        )
        require(
            measurement["status"] in {"available", "unavailable"},
            f"{label} counter status is invalid",
        )
        require(
            measurement["checker"] is None
            or isinstance(measurement["checker"], str)
            and bool(measurement["checker"]),
            f"{label} checker is invalid",
        )
        require(
            type(measurement["attempt"]) is int and measurement["attempt"] >= 0,
            f"{label} attempt is invalid",
        )
        for field in (
            "checker_wall_time_ms", "checker_retired_instructions",
            "build_wall_time_ms", "build_retired_instructions", "lines_of_code",
            "file_count",
        ):
            value = measurement[field]
            require(
                value is None or type(value) is int and value >= 0,
                f"{label} {field} is invalid",
            )
        for field in (
            "checker_retired_instructions_unavailable_reason",
            "build_retired_instructions_unavailable_reason", "unavailable_reason",
        ):
            value = measurement[field]
            require(
                value is None or isinstance(value, str) and bool(value),
                f"{label} {field} is invalid",
            )
        if fields == MEASUREMENT_CORE_FIELDS:
            continue
        require(
            measurement["source_visibility"] in {"public", "private"},
            f"{label} source visibility is invalid",
        )
        replay_task_id = measurement["replay_task_id"]
        transition_event_id = measurement["transition_event_id"]
        require(
            isinstance(replay_task_id, str)
            and REPLAY_TASK_ID_RE.fullmatch(replay_task_id) is not None,
            f"{label} replay task is invalid",
        )
        require(
            isinstance(transition_event_id, str)
            and EVENT_ID_RE.fullmatch(transition_event_id) is not None,
            f"{label} transition event is invalid",
        )
        require(replay_task_id not in replay_task_ids, f"{label} replay task is duplicated")
        require(
            transition_event_id not in transition_event_ids,
            f"{label} transition event is duplicated",
        )
        replay_task_ids.add(replay_task_id)
        transition_event_ids.add(transition_event_id)
        for field in ("measurement_config_digest", "execution_profile_digest"):
            value = measurement[field]
            require(
                isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None,
                f"{label} {field} is invalid",
            )
        require(
            isinstance(measurement["updated_at"], str)
            and STATE_TIMESTAMP_RE.fullmatch(measurement["updated_at"]) is not None,
            f"{label} updated_at is invalid",
        )
        series_order.append(
            (
                replay_task_id,
                measurement["measurement_config_digest"],
                measurement["execution_profile_digest"],
            )
        )
    require(series_order == sorted(series_order), f"{path}: measurement series order is invalid")


def scope_ids(group: dict[str, Any]) -> set[tuple[str, int]]:
    default = next(
        (scope for scope in group["scopes"] if scope["id"] == group["default_scope"]),
        None,
    )
    if default is None:
        require(not group["problems"] and group["default_scope"] == "none", "missing default scope")
        return set()
    return {
        (member["problem_id"], member["statement_revision"])
        for member in default["members"]
    }


def recompute_counts(group: dict[str, Any]) -> dict[str, dict[str, int]]:
    selected_ids = scope_ids(group)
    credits = [
        credit
        for credit in group["credits"]
        if (credit["problem_id"], credit["statement_revision"]) in selected_ids
    ]
    solvers: dict[str, set[str]] = defaultdict(set)
    for credit in credits:
        solvers[credit["problem_id"]].add(credit["canonical_model_id"])
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"unique": 0, "first": 0, "total": 0}
    )
    for credit in credits:
        current = counts[credit["canonical_model_id"]]
        current["total"] += 1
        current["unique"] += len(solvers[credit["problem_id"]]) == 1
        current["first"] += bool(credit["first_solve"])
    return dict(counts)


def validate_problem_lifecycle(
    path: pathlib.Path, problem: dict[str, Any], lifecycle: dict[str, Any]
) -> None:
    require(
        set(lifecycle) == {"status_history", "statement_revisions"},
        f"{path}: invalid lifecycle fields",
    )
    status_history = lifecycle["status_history"]
    revisions = lifecycle["statement_revisions"]
    require(isinstance(status_history, list), f"{path}: invalid status history")
    require(isinstance(revisions, list), f"{path}: invalid revision history")

    previous_date = ""
    for entry in status_history:
        require(
            isinstance(entry, dict)
            and set(entry) == {"status", "effective_at", "reason", "source"},
            f"{path}: invalid status history entry",
        )
        require(
            entry["status"] in {"draft", "active", "archived", "resolved"},
            f"{path}: invalid historical status",
        )
        effective_at = catalog_date(
            entry["effective_at"], f"{path}: status history date is invalid"
        )
        require(
            effective_at > previous_date,
            f"{path}: status history order is invalid",
        )
        require(
            entry["reason"] in CATALOG_REASONS,
            f"{path}: invalid status reason",
        )
        require(
            isinstance(entry["source"], str) and bool(entry["source"]),
            f"{path}: invalid status source",
        )
        previous_date = effective_at
    if status_history:
        require(
            status_history[-1]["status"] == problem["current_status"],
            f"{path}: terminal status history differs from current status",
        )

    previous_date = ""
    previous_revision = 0
    for index, entry in enumerate(revisions):
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "revision",
                "status",
                "effective_at",
                "reason",
                "statement_digest",
                "source",
            },
            f"{path}: invalid revision history entry",
        )
        revision = entry["revision"]
        effective_at = catalog_date(
            entry["effective_at"], f"{path}: revision history date is invalid"
        )
        require(
            type(revision) is int
            and revision > previous_revision
            and effective_at > previous_date,
            f"{path}: revision history order is invalid",
        )
        expected_status = (
            "current" if index == len(revisions) - 1 else "superseded"
        )
        require(entry["status"] == expected_status, f"{path}: invalid revision state")
        require(
            entry["reason"] in CATALOG_REASONS,
            f"{path}: invalid revision reason",
        )
        require(
            isinstance(entry["statement_digest"], str)
            and STATEMENT_DIGEST_RE.fullmatch(entry["statement_digest"]) is not None,
            f"{path}: invalid statement digest",
        )
        require(
            isinstance(entry["source"], str) and bool(entry["source"]),
            f"{path}: invalid revision source",
        )
        previous_revision = revision
        previous_date = effective_at
    if revisions:
        require(
            revisions[-1]["revision"] == problem["statement_revision"],
            f"{path}: terminal revision history differs from current revision",
        )


def validate(root: pathlib.Path) -> None:
    index = load_json(root / "index.json")
    require(index.get("schema_version") == 2, "index: schema_version must be 2")
    index_groups = {group["id"] for group in index.get("groups", [])}
    require(index_groups == GROUPS, "index: exactly three canonical groups are required")
    require(index.get("default_group") in GROUPS, "index: invalid default group")
    all_problem_ids: set[str] = set()
    problem_group: dict[str, str] = {}
    all_result_ids: set[str] = set()

    for group_id in sorted(GROUPS):
        path = root / "groups" / f"{group_id}.json"
        group = load_json(path)
        require(group.get("schema_version") == 2, f"{path}: schema_version must be 2")
        require(group.get("group", {}).get("id") == group_id, f"{path}: group id mismatch")
        require(group.get("standings_default_sort") == "unique", f"{path}: unique must be default")
        ids = [problem["id"] for problem in group.get("problems", [])]
        require(len(ids) == len(set(ids)), f"{path}: duplicate problem id")
        require(not (all_problem_ids & set(ids)), f"{path}: problem appears in multiple groups")
        all_problem_ids.update(ids)
        problem_group.update({problem_id: group_id for problem_id in ids})
        for credit in group.get("credits", []):
            require(credit["problem_id"] in set(ids), f"{path}: cross-group/unknown credit")
            require(credit["result_id"] not in all_result_ids, f"{path}: credit duplicated across groups")
            all_result_ids.add(credit["result_id"])
        expected = recompute_counts(group)
        actual = {
            row["canonical_model_id"]: row["counts"] for row in group.get("standings", [])
        }
        require(actual == expected, f"{path}: default standings do not match credits")

    problem_result_ids: set[str] = set()
    for problem_id in sorted(all_problem_ids):
        path = root / "problems" / f"{problem_id}.json"
        payload = load_json(path)
        require(payload.get("schema_version") == 2, f"{path}: schema_version must be 2")
        problem = payload.get("problem", {})
        require(problem.get("id") == problem_id, f"{path}: problem id mismatch")
        require(problem.get("group") == problem_group[problem_id], f"{path}: group mismatch")
        require(problem.get("visible") is True, f"{path}: hidden problem leaked")
        lifecycle = payload.get("lifecycle", {})
        require(isinstance(lifecycle, dict), f"{path}: lifecycle must be an object")
        validate_problem_lifecycle(path, problem, lifecycle)
        for solution in payload.get("solutions", []):
            require(solution.get("problem_id") == problem_id, f"{path}: solution problem mismatch")
            require("status" in solution.get("replay", {}), f"{path}: replay state omitted")
            require("status" in solution.get("release", {}), f"{path}: release state omitted")
            validate_measurements(path, solution)
            result_id = solution["result_id"]
            require(result_id not in problem_result_ids, f"{path}: duplicate base result")
            problem_result_ids.add(result_id)

    recent = load_json(root / "recent-solutions.json")
    require(recent.get("schema_version") == 2, "recent: schema_version must be 2")
    recent_keys = [
        (item["accepted_at"], item["acceptance_event_id"], item["result_id"])
        for item in recent.get("solutions", [])
    ]
    require(recent_keys == sorted(recent_keys, reverse=True), "recent: order is not deterministic")
    require(
        all(item["problem_id"] in all_problem_ids for item in recent.get("solutions", [])),
        "recent: unknown problem",
    )
    try:
        ET.parse(root / "recent-solutions.xml")
    except (OSError, ET.ParseError) as exc:
        raise ContractError(f"recent RSS: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("site-data/v2"))
    args = parser.parse_args()
    try:
        validate(args.root.resolve())
    except ContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("lifecycle-aware site-data schema version 2: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

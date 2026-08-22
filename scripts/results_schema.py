"""Strict raw-results schema-version-2 reader used by the leaderboard.

The stable identifier contract and envelope mirror
``lean-eval-submissions/docs/results-schema-v2.md``.  This module is vendored
into the site repository rather than importing code from the results checkout:
the checkout is data input and must not become executable build input.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from typing import Any


RESULT_ID_DOMAIN = b"lean-eval-result-v2\0"
RESULT_ID_RE = re.compile(r"^r2_[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")
OWNER_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9._-]+$")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
UUIDV7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
SCHEMA_VERSION_2_FIELDS = {
    "result_id",
    "problem_id",
    "statement_revision",
    "declared_model",
    "accepted_at",
    "benchmark_commit",
    "intake",
    "submission",
    "production_metadata",
}


class ResultsSchemaError(ValueError):
    """A schema-version-2 results file violates the public contract."""


def _canonical_identity(value: list[Any]) -> bytes:
    """RFC 8785 serialization for the identifier's strings/integer array."""

    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        return rendered.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ResultsSchemaError(f"identity is not RFC 8785 canonicalizable: {exc}") from exc


def result_id(
    user: str,
    declared_model: str,
    problem_id: str,
    statement_revision: int,
) -> str:
    if not isinstance(user, str) or not user:
        raise ResultsSchemaError("user must be a non-empty string")
    if not isinstance(declared_model, str) or not declared_model:
        raise ResultsSchemaError("declared_model must be a non-empty string")
    if not isinstance(problem_id, str) or not problem_id:
        raise ResultsSchemaError("problem_id must be a non-empty string")
    if (
        not isinstance(statement_revision, int)
        or isinstance(statement_revision, bool)
        or statement_revision <= 0
    ):
        raise ResultsSchemaError("statement_revision must be a positive integer")
    identity = [user.lower(), declared_model, problem_id, statement_revision]
    digest = hashlib.sha256(RESULT_ID_DOMAIN + _canonical_identity(identity)).hexdigest()
    return "r2_" + digest


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ResultsSchemaError(f"{context} must be an object")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ResultsSchemaError(f"{context} must be a non-empty string")
    return value


def _positive_int(value: Any, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ResultsSchemaError(f"{context} must be a positive integer")
    return value


def _validate_production_metadata(
    metadata: dict[str, Any],
    *,
    public: bool,
    context: str,
) -> None:
    description = metadata.get("production_description")
    if description is not None and (
        not isinstance(description, str)
        or not description.strip()
        or "\x00" in description
        or len(description) > 4000
    ):
        raise ResultsSchemaError(f"{context}.production_description is invalid")
    status = metadata.get("solution_publication_status")
    date = metadata.get("solution_publication_date")
    if status is not None:
        if status not in {"private", "planned", "published"}:
            raise ResultsSchemaError(f"{context}.solution_publication_status is invalid")
        if status == "published" and not public:
            raise ResultsSchemaError(f"{context} published solution must be public")
        if status in {"private", "planned"} and public:
            raise ResultsSchemaError(f"{context} {status} solution must be private")
    if status in {"planned", "published"}:
        if not isinstance(date, str):
            raise ResultsSchemaError(f"{context}.solution_publication_date is required")
        try:
            datetime.date.fromisoformat(date)
        except ValueError as exc:
            raise ResultsSchemaError(
                f"{context}.solution_publication_date is invalid"
            ) from exc
    elif date is not None:
        raise ResultsSchemaError(f"{context}.solution_publication_date is not allowed")


def parse_schema_version_2_file(
    document: Any, *, context: str
) -> list[dict[str, Any]]:
    """Validate a complete schema-version-2 file and return its records."""

    data = _object(document, context)
    if set(data) != {"schema_version", "user", "results"}:
        raise ResultsSchemaError(
            f"{context} must contain only schema_version, user, and results"
        )
    if data.get("schema_version") != 2:
        raise ResultsSchemaError(f"{context} is not results schema version 2")
    user = _string(data.get("user"), f"{context}.user")
    if not LOGIN_RE.fullmatch(user):
        raise ResultsSchemaError(f"{context}.user is not a valid GitHub login")
    values = data.get("results")
    if not isinstance(values, list):
        raise ResultsSchemaError(f"{context}.results must be an array")
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, int]] = set()
    for index, value in enumerate(values):
        item_context = f"{context}.results[{index}]"
        record = _object(value, item_context)
        if set(record) != SCHEMA_VERSION_2_FIELDS:
            raise ResultsSchemaError(
                f"{item_context} has invalid fields; "
                f"missing={sorted(SCHEMA_VERSION_2_FIELDS - set(record))}, "
                f"extra={sorted(set(record) - SCHEMA_VERSION_2_FIELDS)}"
            )
        model = _string(record["declared_model"], f"{item_context}.declared_model")
        problem = _string(record["problem_id"], f"{item_context}.problem_id")
        revision = _positive_int(
            record["statement_revision"], f"{item_context}.statement_revision"
        )
        identifier = _string(record["result_id"], f"{item_context}.result_id")
        if not RESULT_ID_RE.fullmatch(identifier):
            raise ResultsSchemaError(f"{item_context}.result_id has invalid syntax")
        if identifier != result_id(user, model, problem, revision):
            raise ResultsSchemaError(f"{item_context}.result_id does not match its fields")
        if identifier in seen_ids:
            raise ResultsSchemaError(f"{context} has duplicate result_id {identifier}")
        seen_ids.add(identifier)
        sticky_key = (model, problem, revision)
        if sticky_key in seen_keys:
            raise ResultsSchemaError(f"{context} has duplicate sticky key {sticky_key!r}")
        seen_keys.add(sticky_key)
        accepted_at = _string(record["accepted_at"], f"{item_context}.accepted_at")
        if not UTC_TIMESTAMP_RE.fullmatch(accepted_at):
            raise ResultsSchemaError(
                f"{item_context}.accepted_at must be second-precision UTC"
            )
        try:
            datetime.datetime.fromisoformat(accepted_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ResultsSchemaError(f"{item_context}.accepted_at is invalid") from exc
        benchmark_commit = _string(
            record["benchmark_commit"], f"{item_context}.benchmark_commit"
        )
        if not SHA_RE.fullmatch(benchmark_commit):
            raise ResultsSchemaError(f"{item_context}.benchmark_commit must be a SHA")
        intake = _object(record["intake"], f"{item_context}.intake")
        if intake.get("kind") == "issue":
            if set(intake) != {"kind", "issue_number"}:
                raise ResultsSchemaError(f"{item_context}.intake fields are invalid")
            _positive_int(intake["issue_number"], f"{item_context}.issue_number")
        elif intake.get("kind") == "server":
            if set(intake) != {"kind", "submission_id"}:
                raise ResultsSchemaError(f"{item_context}.intake fields are invalid")
            submission_id = _string(
                intake["submission_id"], f"{item_context}.submission_id"
            )
            if not UUIDV7_RE.fullmatch(submission_id):
                raise ResultsSchemaError(
                    f"{item_context}.submission_id must be a canonical lowercase UUIDv7"
                )
        else:
            raise ResultsSchemaError(f"{item_context}.intake.kind is unsupported")
        submission = _object(record["submission"], f"{item_context}.submission")
        if set(submission) != {"kind", "repo", "ref", "public"}:
            raise ResultsSchemaError(f"{item_context}.submission fields are invalid")
        if submission["kind"] not in {"github_repo", "gist"}:
            raise ResultsSchemaError(f"{item_context}.submission.kind is unsupported")
        repo = _string(submission["repo"], f"{item_context}.submission.repo")
        if not OWNER_NAME_RE.fullmatch(repo):
            raise ResultsSchemaError(f"{item_context}.submission.repo is invalid")
        ref = _string(submission["ref"], f"{item_context}.submission.ref")
        if not SHA_RE.fullmatch(ref):
            raise ResultsSchemaError(f"{item_context}.submission.ref must be a SHA")
        if not isinstance(submission["public"], bool):
            raise ResultsSchemaError(f"{item_context}.submission.public must be boolean")
        production = _object(
            record["production_metadata"], f"{item_context}.production_metadata"
        )
        _validate_production_metadata(
            production, public=submission["public"], context=item_context
        )
    return values

"""Strict, source-free acceptance measurements shared with recorder consumers."""

from __future__ import annotations
import datetime as dt
import hashlib
import json
import pathlib
import re
from typing import Any


def _check(value: Any, spec: dict, label: str) -> None:
    if "const" in spec and (
        type(value) is not type(spec["const"]) or value != spec["const"]
    ):
        raise ValueError(f"{label}: invalid constant")
    if "enum" in spec and not any(
        type(value) is type(x) and value == x for x in spec["enum"]
    ):
        raise ValueError(f"{label}: invalid enum")
    types = spec.get("type", [])
    if isinstance(types, str):
        types = [types]
    kinds = {"object": dict, "string": str, "integer": int, "null": type(None)}
    if types and type(value) not in [kinds[t] for t in types]:
        raise ValueError(f"{label}: invalid type")
    if value is None:
        return
    if isinstance(value, dict):
        if set(value) != set(spec["required"]):
            raise ValueError(f"{label}: unknown or missing fields")
        for key, item in value.items():
            _check(item, spec["properties"][key], f"{label}.{key}")
    elif isinstance(value, str):
        if not spec.get("minLength", 0) <= len(value) <= spec.get("maxLength", 1000):
            raise ValueError(f"{label}: invalid length")
        if "pattern" in spec and re.fullmatch(spec["pattern"], value) is None:
            raise ValueError(f"{label}: invalid string")
    elif type(value) is int:
        if not spec.get("minimum", 0) <= value <= spec.get("maximum", 9007199254740991):
            raise ValueError(f"{label}: invalid integer")


def measurement_series(value: dict) -> str:
    fields = {
        key: value[key]
        for key in (
            "kind",
            "toolchain",
            "runner_class",
            "architecture",
            "cache_state",
            "components",
        )
    }
    return hashlib.sha256(
        json.dumps(
            fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def validate_measurement(value: Any) -> dict:
    root = pathlib.Path(__file__).resolve().parent.parent
    folder = "schema" if (root / "schema").is_dir() else "schemas"
    schema = json.loads(
        (root / folder / "acceptance-measurement-v1.schema.json").read_text()
    )
    _check(value, schema, "measurement")
    dt.datetime.strptime(value["measured_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
    if value["series"] != measurement_series(value):
        raise ValueError("measurement: series does not match environment")
    identity = "lean-eval-result-v2\0" + json.dumps(
        [
            value[k]
            for k in (
                "owner_login",
                "declared_model",
                "problem_id",
                "statement_revision",
            )
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    expected = "r2_" + hashlib.sha256(identity.encode()).hexdigest()
    if value["result_id"] != expected:
        raise ValueError("measurement: result identity disagrees")
    available = value["status"] == "available"
    if available != (value["reason_code"] is None):
        raise ValueError("measurement: incoherent status")
    for phase in ("build", "checker"):
        elapsed, counter, reason = (
            value[phase + suffix]
            for suffix in (
                "_wall_time_ms",
                "_retired_instructions",
                "_retired_instructions_unavailable_reason",
            )
        )
        if available != (elapsed is not None):
            raise ValueError("measurement: incomplete phase times")
        if (counter is None) == (reason is None):
            raise ValueError("measurement: counter requires exactly a value or reason")
        if not available and counter is not None:
            raise ValueError("measurement: failed measurement contains a counter")
    return value

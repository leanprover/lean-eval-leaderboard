from __future__ import annotations
import json
import pathlib
import unittest
from scripts.acceptance_measurement import validate_measurement

ROOT = pathlib.Path(__file__).parents[1]


def fixture():
    return json.loads(
        (ROOT / "tests/fixtures/acceptance-measurement-v1.json").read_text()
    )


class MeasurementContractTests(unittest.TestCase):
    def test_unavailable_counter_preserves_elapsed_time(self):
        m = validate_measurement(fixture())
        self.assertEqual(m["checker_wall_time_ms"], 120)
        self.assertIsNone(m["checker_retired_instructions"])

    def test_rejects_tampered_identity_environment_and_counter(self):
        for key, value in [
            ("result_id", "r2_" + "0" * 64),
            ("architecture", "aarch64"),
            ("attempt", True),
            ("build_wall_time_ms", -1),
            ("build_retired_instructions", None),
            ("checker_retired_instructions", 0),
            ("source_code", "private proof"),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m = fixture()
                m[key] = value
                validate_measurement(m)

    def test_failure_is_explicit_and_never_has_partial_totals(self):
        m = fixture()
        m.update(status="failed", reason_code="measurement_invalid")
        for phase in ("build", "checker"):
            m[phase + "_wall_time_ms"] = None
            m[phase + "_retired_instructions"] = None
            m[phase + "_retired_instructions_unavailable_reason"] = (
                "counter_not_reported"
            )
        validate_measurement(m)
        m["build_wall_time_ms"] = 100
        with self.assertRaises(ValueError):
            validate_measurement(m)


from scripts.lifecycle_site_data import (
    adapt_results_store,
    apply_acceptance_measurements,
)


class AcceptanceSiteTests(unittest.TestCase):
    def solution(self):
        m = fixture()
        record = {
            "result_id": m["result_id"],
            "declared_model": m["declared_model"],
            "problem_id": m["problem_id"],
            "statement_revision": 1,
            "accepted_at": "2026-10-20T00:00:00Z",
            "benchmark_commit": m["benchmark_commit"],
            "intake": {"kind": "issue", "issue_number": 1},
            "submission": {
                "kind": "github_repo",
                "repo": "example/proof",
                "ref": "a" * 40,
                "public": True,
            },
            "production_metadata": {},
        }
        return adapt_results_store([("kim-em", [record])], {})[0]

    def test_adds_acceptance_measurement_and_dated_self_report(self):
        s = self.solution()
        raw = {
            "schema_version": 7,
            "acceptance_measurements": [fixture()],
            "metadata_updates": [
                {
                    "result_id": s.result_id,
                    "event_id": "0198abcd-0000-7000-8000-000000000009",
                    "recorded_at": "2026-10-22T06:00:00.000Z",
                    "initial": False,
                    "production_metadata": {
                        "input_tokens": 0,
                        "cached_input_tokens": 0,
                    },
                }
            ],
        }
        apply_acceptance_measurements([s], raw)
        self.assertEqual(s.measurements, [fixture()])
        self.assertEqual(s.metadata["input_tokens"]["provenance"], "backfilled")
        self.assertEqual(s.metadata["cached_input_tokens"]["value"], 0)

    def test_rejects_mismatched_and_duplicate_measurements(self):
        s = self.solution()
        for measurements in (
            [fixture(), fixture()],
            [dict(fixture(), benchmark_commit="0" * 40)],
        ):
            with self.assertRaises(SystemExit):
                apply_acceptance_measurements(
                    [s],
                    {
                        "schema_version": 7,
                        "acceptance_measurements": measurements,
                        "metadata_updates": [],
                    },
                )

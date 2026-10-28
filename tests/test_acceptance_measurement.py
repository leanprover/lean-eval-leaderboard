from __future__ import annotations
import json
import pathlib
import unittest
import io
from contextlib import redirect_stderr

ROOT = pathlib.Path(__file__).parents[1]


def fixture():
    return json.loads(
        (ROOT / "tests/fixtures/acceptance-measurement-v1.json").read_text()
    )


from scripts.lifecycle_site_data import (
    adapt_results_store,
    apply_acceptance_measurements,
)


class AcceptanceSiteTests(unittest.TestCase):
    def solution(self, metadata=None):
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
            "production_metadata": metadata or {},
        }
        return adapt_results_store([("kim-em", [record])], {})[0]

    def test_current_fields_keep_their_individual_origins(self):
        s = self.solution({"input_tokens": 100, "notes": "Current note"})
        raw = {
            "schema_version": 7, "acceptance_measurements": [fixture()],
            "metadata_provenance": [{"result_id": s.result_id, "fields": {
                "input_tokens": {"event_id": "0198abcd-0000-7000-8000-000000000001", "recorded_at": "2026-10-22T06:00:00.000Z", "initial": True},
                "notes": {"event_id": "0198abcd-0000-7000-8000-000000000002", "recorded_at": "2026-10-27T06:00:00.000Z", "initial": False},
            }}],
        }
        apply_acceptance_measurements([s], raw)
        self.assertEqual(s.measurements, [fixture()])
        self.assertEqual(s.metadata["input_tokens"]["value"], 100)
        self.assertEqual(s.metadata["input_tokens"]["provenance"], "declared-at-submission")
        self.assertEqual(s.metadata["input_tokens"]["recorded_at"], "2026-10-22T06:00:00.000Z")
        self.assertEqual(s.metadata["notes"]["provenance"], "backfilled")
        self.assertEqual(s.metadata["notes"]["value"], "Current note")
        self.assertNotIn("prompt", s.metadata)

    def test_stray_bad_and_duplicate_statistics_do_not_block_valid_results(self):
        s = self.solution()
        raw = {"schema_version": 7, "metadata_provenance": [], "acceptance_measurements": [
            dict(fixture(), result_id="r2_" + "0" * 64),
            dict(fixture(), benchmark_commit="0" * 40),
            dict(fixture(), build_wall_time_ms="bad"),
            fixture(), fixture(),
        ]}
        output = io.StringIO()
        with redirect_stderr(output):
            apply_acceptance_measurements([s], raw)
        self.assertEqual(s.measurements, [fixture()])
        self.assertEqual(output.getvalue().count("Skipping acceptance measurement"), 4)

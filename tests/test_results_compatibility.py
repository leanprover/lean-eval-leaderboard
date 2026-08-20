from __future__ import annotations

import copy
import pathlib
import unittest
from unittest.mock import patch

from scripts.generate_site_data import Problem, build_leaderboard_payload
from scripts.results_v2 import result_id


SHA = "a" * 40
REF = "b" * 40


def problem() -> Problem:
    return Problem(
        id="two_plus_two",
        title="Two plus two",
        test=False,
        submitter="benchmark-author",
        module="LeanEval.TwoPlusTwo",
        notes=None,
        source=None,
        informal_solution=None,
        holes=(),
        challenge_path="generated/two_plus_two",
        sort_index=0,
    )


def v1_document() -> dict:
    return {
        "schema_version": 1,
        "user": "alice",
        "solved": {
            "Claude Opus 4.6": {
                "two_plus_two": {
                    "solved_at": "2026-04-11T10:45:00Z",
                    "benchmark_commit": SHA,
                    "submission_kind": "github_repo",
                    "submission_repo": "alice/proofs",
                    "submission_ref": REF,
                    "submission_public": True,
                    "issue_number": 42,
                    "production_description": "Agent harness.",
                    "legacy_extension_ignored_by_existing_reader": True,
                }
            }
        },
    }


def v2_record(revision: int = 1, accepted_at: str = "2026-04-11T10:45:00Z") -> dict:
    model = "Claude Opus 4.6"
    problem_id = "two_plus_two"
    return {
        "result_id": result_id("alice", model, problem_id, revision),
        "problem_id": problem_id,
        "statement_revision": revision,
        "declared_model": model,
        "accepted_at": accepted_at,
        "benchmark_commit": SHA,
        "intake": {"kind": "issue", "issue_number": 42},
        "submission": {
            "kind": "github_repo",
            "repo": "alice/proofs",
            "ref": REF,
            "public": True,
        },
        "production_metadata": {"production_description": "Agent harness."},
    }


def v2_document() -> dict:
    return {"schema_version": 2, "user": "alice", "results": [v2_record()]}


def build(raw: list[dict]) -> dict:
    with (
        patch("scripts.generate_site_data.git_head", return_value="c" * 40),
        patch("scripts.generate_site_data.utc_now", return_value="2026-08-20T00:00:00Z"),
    ):
        return build_leaderboard_payload(
            results_repo=pathlib.Path("results"),
            benchmark_repo=pathlib.Path("benchmark"),
            problems=[problem()],
            raw_results=raw,
        )


class ResultsCompatibilityTests(unittest.TestCase):
    def test_v1_reader_behavior_and_v2_visible_payload_match(self) -> None:
        v1 = build([v1_document()])
        v2 = build([v2_document()])
        self.assertEqual(v1["raw_results_schema_versions"], [1])
        self.assertEqual(v2["raw_results_schema_versions"], [2])
        for payload in (v1, v2):
            entry = payload["entries"][0]
            self.assertEqual(entry["model_name"], "Claude Opus 4.6")
            self.assertEqual(entry["score"]["solved_main"], 1)
            self.assertEqual(entry["submitters"], [{"user": "alice", "solved_total": 1}])
            solved = entry["solved_problems"][0]
            self.assertEqual(solved["problem_id"], "two_plus_two")
            self.assertEqual(solved["production_description"], "Agent harness.")
            self.assertTrue(solved["public_solution"]["available"])

    def test_revision_records_do_not_double_count_current_problem_view(self) -> None:
        document = v2_document()
        later = copy.deepcopy(v2_record(2, "2026-05-01T00:00:00Z"))
        later["intake"]["issue_number"] = 43
        document["results"].append(later)
        payload = build([document])
        entry = payload["entries"][0]
        self.assertEqual(entry["score"]["solved_total"], 1)
        self.assertEqual(entry["submitters"][0]["solved_total"], 1)
        self.assertEqual(
            entry["solved_problems"][0]["solved_at"], "2026-04-11T10:45:00Z"
        )

    def test_invalid_v2_fails_before_aggregation(self) -> None:
        document = v2_document()
        document["results"][0]["benchmark_commit"] = "mutable-main"
        with self.assertRaisesRegex(SystemExit, "benchmark_commit must be a SHA"):
            build([document])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
import pathlib
import unittest

from scripts.results_v2 import ResultsV2Error, parse_v2_file, result_id


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SHA = "a" * 40
REF = "b" * 40


def v2_document() -> dict:
    model = "Claude Opus 4.6"
    problem = "two_plus_two"
    return {
        "schema_version": 2,
        "user": "alice",
        "results": [
            {
                "result_id": result_id("alice", model, problem, 1),
                "problem_id": problem,
                "statement_revision": 1,
                "declared_model": model,
                "accepted_at": "2026-04-11T10:45:00Z",
                "benchmark_commit": SHA,
                "intake": {"kind": "issue", "issue_number": 42},
                "submission": {
                    "kind": "github_repo",
                    "repo": "alice/proofs",
                    "ref": REF,
                    "public": True,
                },
                "production_metadata": {
                    "production_description": "Agent harness."
                },
            }
        ],
    }


class ResultIdContractTests(unittest.TestCase):
    def test_vectors_match_submissions_contract(self) -> None:
        fixture = json.loads(
            (REPO_ROOT / "tests/fixtures/result_id_vectors.json").read_text()
        )
        for vector in fixture["vectors"]:
            with self.subTest(vector=vector["name"]):
                self.assertEqual(
                    result_id(
                        vector["user"],
                        vector["declared_model"],
                        vector["problem_id"],
                        vector["statement_revision"],
                    ),
                    vector["expected"],
                )


class StrictV2ReaderTests(unittest.TestCase):
    def test_valid_file_is_returned(self) -> None:
        document = v2_document()
        self.assertEqual(parse_v2_file(document, context="fixture"), document["results"])

    def test_identifier_mismatch_is_rejected(self) -> None:
        document = v2_document()
        document["results"][0]["result_id"] = "r2_" + "0" * 64
        with self.assertRaisesRegex(ResultsV2Error, "does not match"):
            parse_v2_file(document, context="fixture")

    def test_unknown_field_and_duplicate_are_rejected(self) -> None:
        document = v2_document()
        document["results"][0]["unexpected"] = True
        with self.assertRaisesRegex(ResultsV2Error, "invalid fields"):
            parse_v2_file(document, context="fixture")

        duplicate = v2_document()
        duplicate["results"].append(copy.deepcopy(duplicate["results"][0]))
        with self.assertRaisesRegex(ResultsV2Error, "duplicate result_id"):
            parse_v2_file(duplicate, context="fixture")

    def test_server_intake_is_supported(self) -> None:
        document = v2_document()
        document["results"][0]["intake"] = {
            "kind": "server",
            "submission_id": "0198cafe-1234-7000-8000-000000000000",
        }
        parse_v2_file(document, context="fixture")


if __name__ == "__main__":
    unittest.main()

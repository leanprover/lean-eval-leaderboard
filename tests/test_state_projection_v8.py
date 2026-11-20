from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import unittest

from scripts.lifecycle_site_data import (
    adapt_results_store, adapt_state_projection, apply_state_projection_overlays,
    build_model_identity_index,
)
from scripts.state_contracts import STATE_CODE_CONTRACTS
from scripts.validate_lifecycle_site_data import validate_measurements
import test_lifecycle_site_data as legacy_tests

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ArchiveProjectionTests(unittest.TestCase):
    def setUp(self):
        self.legacy = legacy_tests.HistoricalReplayProjectionTests()

    def projection(self):
        raw = self.legacy.projection()
        raw.update(schema_version=8, acceptance_measurements=[], metadata_provenance=[])
        return raw

    def apply(self, raw, *, public=True):
        identity = build_model_identity_index(raw)
        self.assertEqual(adapt_state_projection(raw, {}, identity), [])
        solutions = adapt_results_store(
            [("alice", [self.legacy.base_record(public=public)])], {}, identity
        )
        apply_state_projection_overlays(solutions, raw)
        return solutions[0]

    def test_public_archive_preserves_original_visibility_without_publication(self):
        raw = self.projection()
        series = self.legacy.series(1, "accepted")
        series["fetch_method"] = "archive"
        raw["historical_replay_series"] = [series]
        solution = self.apply(raw)
        self.assertEqual(solution.replay["status"], "accepted")
        self.assertEqual(solution.measurements[0]["source_visibility"], "public")
        self.assertEqual(solution.measurements[0]["fetch_method"], "archive")
        baseline = self.apply(self.projection())
        self.assertEqual(solution.release, baseline.release)
        self.assertEqual(solution.public_solution, baseline.public_solution)
        self.assertIsNone(solution.release["url"])
        validate_measurements(pathlib.Path("synthetic.json"), {"measurements": solution.measurements})
        # No archive locator or source URL is introduced by the redacted projection.
        self.assertFalse(any("url" in key or "path" in key for key in solution.measurements[0]))

    def test_v7_output_stays_unchanged_and_cannot_accept_v8_fields(self):
        raw = self.projection()
        raw["schema_version"] = 7
        raw["historical_replay_series"] = [self.legacy.series(1, "accepted")]
        measurement = self.apply(raw).measurements[0]
        self.assertNotIn("fetch_method", measurement)
        raw["historical_replay_series"][0]["fetch_method"] = "git"
        with self.assertRaisesRegex(SystemExit, "series fields"):
            self.apply(raw)

    def test_v8_rejects_missing_unknown_or_private_git_methods_and_locator_fields(self):
        for mutation in ("missing", "unknown", "private_git", "archive_path", "source_url"):
            with self.subTest(mutation=mutation):
                raw = self.projection()
                series = self.legacy.series(1, "accepted")
                series["fetch_method"] = "archive"
                public = mutation != "private_git"
                if mutation == "missing":
                    series.pop("fetch_method")
                elif mutation == "unknown":
                    series["fetch_method"] = "unreviewed"
                elif mutation == "private_git":
                    series.update(source_visibility="private", fetch_method="git")
                else:
                    series[mutation] = "sensitive locator"
                raw["historical_replay_series"] = [series]
                with self.assertRaises(SystemExit):
                    self.apply(raw, public=public)

    def disposition(self, public):
        return {
            **{key: value for key, value in self.legacy.series(1, "accepted").items()
               if key in {"result_id", "owner_login", "declared_model", "problem_id",
                          "statement_revision", "historical_accepted_at", "source_visibility"}},
            "source_visibility": "public" if public else "private",
            "fetch_method": "archive",
            "disposed_at": "2026-10-20T06:08:40.000Z",
            "disposition_event_id": "0198abcd-0000-7000-8000-000000000040",
            "reason": "archive_permanently_unrecoverable",
            "rationale": "accepted_archive_permanently_unrecoverable_after_review",
        }

    def test_archive_loss_disposition_is_valid_for_either_original_visibility(self):
        for public in (True, False):
            with self.subTest(public=public):
                raw = self.projection()
                raw["historical_replay_unavailability"] = [self.disposition(public)]
                solution = self.apply(raw, public=public)
                self.assertEqual(solution.replay, {"status": "unavailable", "reason": "archive_permanently_unrecoverable"})
                self.assertEqual(solution.measurements, [])
                bad = copy.deepcopy(raw)
                bad["historical_replay_unavailability"][0]["fetch_method"] = "git"
                with self.assertRaises(SystemExit):
                    self.apply(bad, public=public)

    def test_all_vendored_projection_schemas_match_reviewed_state_components(self):
        for anchor, entry in STATE_CODE_CONTRACTS.items():
            for path, (_, _, expected) in entry["components"].items():
                if not path.startswith("schema/public-state-projection-"):
                    continue
                with self.subTest(contract=anchor, path=path):
                    contents = (ROOT / "schemas" / pathlib.Path(path).name).read_bytes()
                    self.assertEqual(hashlib.sha256(contents).hexdigest(), expected)

    def test_exact_state_generated_v8_recovery_and_adjudication_vectors(self):
        # Generated by State351b1c4 project_public_state_v8 from its validated
        # synthetic recovery_events()/permanent_archive_unavailability() tests.
        for name in ("recovered-public", "unrecoverable-public"):
            with self.subTest(name=name):
                raw = json.loads((ROOT / f"tests/fixtures/public-state-projection-v8-{name}.json").read_text())
                identity = (raw["historical_replay_series"] or raw["historical_replay_unavailability"])[0]
                base = {
                    "result_id": identity["result_id"],
                    "problem_id": identity["problem_id"],
                    "statement_revision": identity["statement_revision"],
                    "declared_model": identity["declared_model"],
                    "accepted_at": identity["historical_accepted_at"],
                    "benchmark_commit": "a" * 40,
                    "intake": {"kind": "issue", "issue_number": 1},
                    "submission": {"kind": "github_repo", "repo": "alice/proofs", "ref": "b" * 40, "public": True},
                    "production_metadata": {},
                }
                index = build_model_identity_index(raw)
                self.assertEqual(adapt_state_projection(raw, {}, index), [])
                solutions = adapt_results_store([(identity["owner_login"], [base])], {}, index)
                apply_state_projection_overlays(solutions, raw)
                self.assertEqual(identity["source_visibility"], "public")
                self.assertEqual(identity["fetch_method"], "archive")
                if name == "recovered-public":
                    self.assertEqual(solutions[0].measurements[0]["fetch_method"], "archive")
                else:
                    self.assertEqual(solutions[0].replay["reason"], "archive_permanently_unrecoverable")


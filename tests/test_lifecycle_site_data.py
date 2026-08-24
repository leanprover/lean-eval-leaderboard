from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import unittest
from types import SimpleNamespace

from scripts.lifecycle_site_data import (
    SetDefinition,
    Solution,
    adapt_results_store,
    adapt_state_projection,
    build_lifecycle_projection,
    build_model_identity_index,
    load_preview_fixture,
    merge_solutions,
)
from scripts.results_schema import result_id

ROOT = pathlib.Path(__file__).resolve().parent.parent


def model_id(request_event_id: str) -> str:
    return "mi1_" + hashlib.sha256(
        b"lean-eval-model-identity-v1\0" + request_event_id.encode("ascii")
    ).hexdigest()


def alias_key(owner: str, alias: str) -> str:
    canonical = json.dumps(
        [owner, alias], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return "ma1_" + hashlib.sha256(
        b"lean-eval-model-alias-v1\0" + canonical
    ).hexdigest()


def identity_projection_v4() -> dict:
    source_request = "0198abcd-0000-7000-8000-000000000100"
    target_request = "0198abcd-0000-7000-8000-000000000200"
    source_id = model_id(source_request)
    target_id = model_id(target_request)
    declared = "Example Model Revision A"
    result = {
        "result_id": result_id("alice", declared, "alpha", 1),
        "problem_id": "alpha",
        "statement_revision": 1,
        "declared_model": declared,
        "submitter": "alice",
        "accepted_at": "2026-08-20T00:00:00.000Z",
        "acceptance_event_id": "0198abcd-0000-7000-8000-000000000001",
        "recorded_at": "2026-08-20T00:00:01.000Z",
        "record_event_id": "0198abcd-0000-7000-8000-000000000002",
        "benchmark_commit": "a" * 40,
        "production_metadata": {},
        "replay": None,
        "release": None,
        "public_solution": {"available": False, "url": None},
        "model_id": source_id,
        "resolved_model_id": target_id,
    }
    identity_common = {
        "requested_at": "2026-08-20T00:00:00.000Z",
        "decision_event_id": "0198abcd-0000-7000-8000-000000000300",
        "decided_at": "2026-08-20T00:00:01.000Z",
        "reviewer_login": "reviewer",
        "rejection_reason": None,
        "mutation_event_id": "0198abcd-0000-7000-8000-000000000400",
    }
    return {
        "schema_version": 4,
        "environment": "production",
        "source_state_commit": "e" * 40,
        "source_event_count": 8,
        "source_digest": "f" * 64,
        "results": [result],
        "result_overlays": [],
        "model_identities": [
            {
                **identity_common,
                "model_id": source_id,
                "owner_login": "alice",
                "requested_name": "Original Model",
                "display_name": "Renamed Before Consolidation",
                "status": "consolidated",
                "request_event_id": source_request,
                "consolidated_into": target_id,
                "resolved_model_id": target_id,
            },
            {
                **identity_common,
                "model_id": target_id,
                "owner_login": "alice",
                "requested_name": "Canonical Model",
                "display_name": "Canonical Model Renamed",
                "status": "approved",
                "request_event_id": target_request,
                "consolidated_into": None,
                "resolved_model_id": target_id,
            },
        ],
        "model_aliases": [
            {
                "alias_key": alias_key("alice", declared),
                "owner_login": "alice",
                "alias": declared,
                "model_id": source_id,
                "resolved_model_id": target_id,
                "assignment_event_id": "0198abcd-0000-7000-8000-000000000500",
                "assigned_at": "2026-08-20T00:00:02.000Z",
            }
        ],
        "model_identity_history": [],
    }


def problem(
    problem_id: str,
    group: str = "formalization-evaluation",
    *,
    status: str = "active",
    tags: tuple[str, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=problem_id,
        title=f"Problem <{problem_id}>",
        group=group,
        status=status,
        visible=True,
        statement_revision=1,
        tags=tags,
        submitter="Author",
        module=f"LeanEval.{problem_id.title()}",
        notes=None,
        source=None,
        informal_solution=None,
        sort_index=0,
    )


def solution(
    result_id: str,
    problem_id: str,
    model_id: str,
    accepted_at: str,
    event_id: str,
) -> Solution:
    return Solution(
        result_id=result_id,
        problem_id=problem_id,
        statement_revision=1,
        declared_model=model_id,
        canonical_model_id=model_id,
        canonical_model_label=model_id.title(),
        submitter="alice&bob",
        accepted_at=accepted_at,
        acceptance_event_id=event_id,
        retracted=False,
        metadata={},
        provenance={"source": "test"},
        public_solution={"available": False, "url": None},
        replay={"status": "unavailable", "reason": "not-enqueued"},
        release={"status": "unavailable", "reason": "not-scheduled"},
    )


class LifecycleProjectionTests(unittest.TestCase):
    def build(self):
        problems = [
            problem("alpha", tags=("annals",)),
            problem("beta"),
            problem("gamma", "software-verification", status="draft"),
        ]
        solutions = [
            solution("r2_b", "alpha", "model-b", "2026-08-20T00:00:00Z", "event-b"),
            solution("r2_a", "alpha", "model-a", "2026-08-20T00:00:00Z", "event-a"),
            solution("r2_c", "beta", "model-a", "2026-08-21T00:00:00Z", "event-c"),
            solution("r2_d", "gamma", "model-c", "2026-08-22T00:00:00Z", "event-d"),
        ]
        fixture = load_preview_fixture(
            ROOT / "tests/fixtures/preview-domain-schema-version-1.json"
        )
        return build_lifecycle_projection(
            problems=problems,
            solutions=solutions,
            set_definitions=[
                SetDefinition(
                    "v1",
                    "LeanEval v1",
                    True,
                    "2026-08-20",
                    (("alpha", 1), ("beta", 1)),
                )
            ],
            tag_registry={
                "annals": {"label": "Annals Challenge", "description": "Corpus tag"}
            },
            fixture=fixture,
            generated_at="2026-08-20T12:00:00Z",
            benchmark_commit="a" * 40,
            state_commit=None,
            state_metadata=None,
            site_base_url="https://example.test/eval/",
        )

    def test_flagship_is_default_and_groups_never_share_standings(self) -> None:
        files = self.build()
        formal = files["v2/groups/formalization-evaluation.json"]
        software = files["v2/groups/software-verification.json"]

        self.assertEqual(formal["default_scope"], "v1")
        self.assertTrue(formal["scopes"][0]["flagship"])
        self.assertEqual(
            {row["canonical_model_id"] for row in formal["standings"]},
            {"model-a", "model-b"},
        )
        self.assertEqual(
            {row["canonical_model_id"] for row in software["standings"]},
            {"model-c"},
        )

    def test_counts_and_first_solve_use_deterministic_event_order(self) -> None:
        formal = self.build()["v2/groups/formalization-evaluation.json"]
        rows = {row["canonical_model_id"]: row for row in formal["standings"]}

        self.assertEqual(rows["model-a"]["counts"], {"unique": 1, "first": 2, "total": 2})
        self.assertEqual(rows["model-b"]["counts"], {"unique": 0, "first": 0, "total": 1})
        self.assertEqual(formal["standings_default_sort"], "unique")

    def test_problem_contract_has_lifecycle_sets_and_unavailable_states(self) -> None:
        payload = self.build()["v2/problems/alpha.json"]

        self.assertEqual(len(payload["lifecycle"]["status_history"]), 2)
        self.assertEqual(payload["sets"][0]["id"], "v1")
        self.assertEqual(payload["solutions"][0]["replay"]["status"], "unavailable")
        self.assertEqual(payload["solutions"][0]["release"]["status"], "unavailable")
        self.assertEqual(payload["problem"]["stable_url"], "problems/alpha/")
        self.assertEqual(
            payload["solutions"][0]["metadata"]["human_involvement"]["provenance"],
            "backfilled",
        )
        self.assertEqual(
            self.build()["v2/index.json"]["model_aliases"][0]["canonical_id"],
            "example-model",
        )

    def test_recent_json_and_rss_escape_untrusted_display_text(self) -> None:
        files = self.build()
        rss = files["v2/recent-solutions.xml"]

        self.assertIn("Problem &lt;gamma&gt;", rss)
        self.assertIn("@alice&amp;bob", rss)
        self.assertNotIn("<gamma>", rss)
        self.assertEqual(files["v2/recent-solutions.json"]["solutions"][0]["problem_id"], "gamma")

    def test_limitations_explicitly_label_missing_production_state(self) -> None:
        limitations = self.build()["v2/index.json"]["data_limitations"]

        self.assertTrue(any("unavailable" in limitation for limitation in limitations))

    def test_public_state_projection_adapter_joins_replay_and_release(self) -> None:
        projected_result_id = result_id("alice", "Example Model Revision A", "alpha", 1)
        raw = {
            "schema_version": 1,
            "environment": "production",
            "source_state_commit": "e" * 40,
            "source_event_count": 8,
            "source_digest": "f" * 64,
            "results": [{
                "result_id": projected_result_id,
                "problem_id": "alpha",
                "statement_revision": 1,
                "declared_model": "Example Model Revision A",
                "submitter": "alice",
                "accepted_at": "2026-08-20T00:00:00Z",
                "acceptance_event_id": "0198abcd-0000-7000-8000-000000000001",
                "recorded_at": "2026-08-20T00:00:01Z",
                "record_event_id": "0198abcd-0000-7000-8000-000000000002",
                "benchmark_commit": "a" * 40,
                "production_metadata": {},
                "replay": {
                    "status": "accepted",
                    "reason": None,
                    "attempt": 1,
                    "checker": "lean4lean",
                    "checker_wall_time_ms": 20,
                    "checker_retired_instructions": None,
                    "checker_retired_instructions_unavailable_reason": "counter_not_supported",
                    "build_wall_time_ms": 40,
                    "build_retired_instructions": 100,
                    "build_retired_instructions_unavailable_reason": None,
                    "lines_of_code": 12,
                    "file_count": 1,
                },
                "release": {
                    "status": "scheduled",
                    "release_at": "2026-10-20T00:00:00Z",
                    "reason": None,
                },
                "public_solution": {"available": False, "url": None},
            }],
        }
        aliases = {
            "Example Model Revision A": {
                "canonical_id": "example-model",
                "label": "Example Model",
            }
        }

        adapted = adapt_state_projection(raw, aliases)

        self.assertEqual(adapted[0].canonical_model_id, "example-model")
        self.assertEqual(adapted[0].replay["status"], "accepted")
        self.assertEqual(adapted[0].measurements[0]["status"], "unavailable")
        self.assertEqual(adapted[0].release["status"], "scheduled")

    def test_public_state_projection_rejects_private_internal_fields(self) -> None:
        raw = {
            "schema_version": 1,
            "environment": "production",
            "source_state_commit": "e" * 40,
            "source_event_count": 1,
            "source_digest": "f" * 64,
            "results": [],
            "submissions": [],
        }
        with self.assertRaisesRegex(SystemExit, "top-level fields"):
            adapt_state_projection(raw, {})

    def test_public_state_projection_recomputes_result_identity(self) -> None:
        raw = {
            "schema_version": 1,
            "environment": "production",
            "source_state_commit": "e" * 40,
            "source_event_count": 1,
            "source_digest": "f" * 64,
            "results": [{
                "result_id": "r2_" + "b" * 64,
                "problem_id": "alpha",
                "statement_revision": 1,
                "declared_model": "Example Model Revision B",
                "submitter": "alice",
                "accepted_at": "2026-08-20T00:00:00.000Z",
                "acceptance_event_id": "0198abcd-0000-7000-8000-000000000001",
                "recorded_at": "2026-08-20T00:00:01.000Z",
                "record_event_id": "0198abcd-0000-7000-8000-000000000002",
                "benchmark_commit": "a" * 40,
                "production_metadata": {},
                "replay": None,
                "release": None,
                "public_solution": {"available": False, "url": None},
            }],
        }
        with self.assertRaisesRegex(SystemExit, "result_id does not match"):
            adapt_state_projection(raw, {})

    def test_projection_v4_uses_owner_scoped_consolidated_identity(self) -> None:
        raw = identity_projection_v4()
        index = build_model_identity_index(raw)
        adapted = adapt_state_projection(
            raw,
            {
                "Example Model Revision A": {
                    "canonical_id": "unreviewed-static-alias",
                    "label": "Unreviewed Static Alias",
                }
            },
            index,
        )

        target_id = raw["model_identities"][1]["model_id"]
        self.assertEqual(adapted[0].canonical_model_id, target_id)
        self.assertEqual(
            adapted[0].canonical_model_label, "Canonical Model Renamed"
        )
        self.assertEqual(index.public_aliases[0]["canonical_id"], target_id)
        files = build_lifecycle_projection(
            problems=[problem("alpha")],
            solutions=adapted,
            set_definitions=[],
            tag_registry={},
            fixture={},
            generated_at="2026-08-20T12:00:00Z",
            benchmark_commit="a" * 40,
            state_commit=raw["source_state_commit"],
            state_metadata=raw,
            site_base_url="https://example.test/eval/",
            model_aliases=index.public_aliases,
        )
        published_alias = files["v2/index.json"]["model_aliases"][0]
        self.assertEqual(published_alias["owner_login"], "alice")
        self.assertEqual(published_alias["model_id"], raw["model_identities"][0]["model_id"])
        self.assertFalse(
            any(
                "no reviewed State model alias" in limitation
                for limitation in files["v2/index.json"]["data_limitations"]
            )
        )
        mixed_files = build_lifecycle_projection(
            problems=[problem("alpha")],
            solutions=[
                *adapted,
                solution(
                    "legacy-unreviewed",
                    "alpha",
                    "unreviewed-model",
                    "2026-08-21T00:00:00Z",
                    "issue-2",
                ),
            ],
            set_definitions=[],
            tag_registry={},
            fixture={},
            generated_at="2026-08-20T12:00:00Z",
            benchmark_commit="a" * 40,
            state_commit=raw["source_state_commit"],
            state_metadata=raw,
            site_base_url="https://example.test/eval/",
            model_aliases=index.public_aliases,
        )
        self.assertTrue(
            any(
                "no reviewed State model alias" in limitation
                for limitation in mixed_files["v2/index.json"]["data_limitations"]
            )
        )

    def test_state_generated_v4_fixture_is_consumed_without_rewriting(self) -> None:
        raw = json.loads(
            (
                ROOT
                / "tests/fixtures/public-state-projection-v4-model-identity.json"
            ).read_text(encoding="utf-8")
        )

        index = build_model_identity_index(raw)
        adapted = adapt_state_projection(raw, {}, index)

        self.assertEqual(len(raw["model_identity_history"]), 10)
        self.assertEqual(adapted[0].declared_model, "Example Model")
        self.assertEqual(adapted[0].canonical_model_label, "Third")
        self.assertEqual(
            adapted[0].canonical_model_id,
            index.aliases[("kim-em", "Example Model")][1],
        )

    def test_projection_v4_aliases_are_owner_scoped(self) -> None:
        raw = identity_projection_v4()
        bob_request = "0198abcd-0000-7000-8000-000000000600"
        bob_id = model_id(bob_request)
        bob_identity = copy.deepcopy(raw["model_identities"][1])
        bob_identity.update(
            model_id=bob_id,
            owner_login="bob",
            request_event_id=bob_request,
            requested_name="Bob Canonical",
            display_name="Bob Canonical",
            consolidated_into=None,
            resolved_model_id=bob_id,
        )
        raw["model_identities"].append(bob_identity)
        bob_alias = copy.deepcopy(raw["model_aliases"][0])
        bob_alias.update(
            alias_key=alias_key("bob", bob_alias["alias"]),
            owner_login="bob",
            model_id=bob_id,
            resolved_model_id=bob_id,
        )
        raw["model_aliases"].append(bob_alias)

        index = build_model_identity_index(raw)

        self.assertNotEqual(
            index.aliases[("alice", "Example Model Revision A")][1],
            index.aliases[("bob", "Example Model Revision A")][1],
        )

    def test_projection_v4_rejects_alias_collisions_and_spoofed_bindings(self) -> None:
        duplicate = identity_projection_v4()
        duplicate["model_aliases"].append(
            copy.deepcopy(duplicate["model_aliases"][0])
        )
        with self.assertRaisesRegex(SystemExit, "invalid model alias binding"):
            build_model_identity_index(duplicate)

        hostile_key = identity_projection_v4()
        hostile_key["model_aliases"][0]["alias_key"] = "ma1_" + "0" * 64
        with self.assertRaisesRegex(SystemExit, "invalid model alias binding"):
            build_model_identity_index(hostile_key)

        spoofed_result = identity_projection_v4()
        spoofed_result["results"][0]["model_id"] = spoofed_result[
            "model_identities"
        ][1]["model_id"]
        with self.assertRaisesRegex(SystemExit, "binding is inconsistent"):
            adapt_state_projection(spoofed_result, {})

    def test_projection_v4_rejects_identity_and_resolution_drift(self) -> None:
        wrong_id = identity_projection_v4()
        wrong_id["model_identities"][0]["model_id"] = "mi1_" + "0" * 64
        with self.assertRaisesRegex(SystemExit, "invalid model identity"):
            build_model_identity_index(wrong_id)

        cross_owner = identity_projection_v4()
        cross_owner["model_identities"][1]["owner_login"] = "bob"
        with self.assertRaisesRegex(SystemExit, "incoherent model identity"):
            build_model_identity_index(cross_owner)

        hostile_label = identity_projection_v4()
        hostile_label["model_identities"][1]["display_name"] = "bad\nlabel"
        with self.assertRaisesRegex(SystemExit, "invalid model display name"):
            build_model_identity_index(hostile_label)

    def test_base_result_fallback_uses_state_identity_without_mutation(self) -> None:
        raw = identity_projection_v4()
        index = build_model_identity_index(raw)
        record = {
            "result_id": raw["results"][0]["result_id"],
            "problem_id": "alpha",
            "statement_revision": 1,
            "declared_model": "Example Model Revision A",
            "accepted_at": "2026-08-20T00:00:00Z",
            "benchmark_commit": "a" * 40,
            "intake": {"kind": "issue", "issue_number": 1},
            "submission": {
                "kind": "github_repo",
                "repo": "alice/proofs",
                "ref": "b" * 40,
                "public": False,
            },
            "production_metadata": {},
        }

        adapted = adapt_results_store([("alice", [record])], {}, index)

        self.assertEqual(
            adapted[0].canonical_model_id,
            raw["model_identities"][1]["model_id"],
        )
        self.assertEqual(adapted[0].declared_model, record["declared_model"])

    def test_verbatim_alias_mismatch_stays_visible_and_falls_back(self) -> None:
        raw = identity_projection_v4()
        raw["results"][0]["declared_model"] = "Example  Model Revision A"
        raw["results"][0]["result_id"] = result_id(
            "alice", "Example  Model Revision A", "alpha", 1
        )
        raw["results"][0]["model_id"] = None
        raw["results"][0]["resolved_model_id"] = None

        adapted = adapt_state_projection(raw, {})

        self.assertEqual(adapted[0].declared_model, "Example  Model Revision A")
        self.assertEqual(adapted[0].canonical_model_id, "example-model-revision-a")
        self.assertFalse(adapted[0].model_identity_reviewed)

    def test_state_record_replaces_matching_legacy_base_record(self) -> None:
        legacy = solution("legacy_a", "alpha", "model-a", "2026-08-20T00:00:00Z", "issue-1")
        state = solution("r2_a", "alpha", "model-a", "2026-08-20T00:00:00Z", "event-1")

        merged = merge_solutions([state], [legacy])

        self.assertEqual([item.result_id for item in merged], ["r2_a"])


if __name__ == "__main__":
    unittest.main()

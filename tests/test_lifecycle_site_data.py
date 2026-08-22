from __future__ import annotations

import pathlib
import unittest
from types import SimpleNamespace

from scripts.lifecycle_site_data import (
    SetDefinition,
    Solution,
    adapt_state_domain,
    build_lifecycle_projection,
    load_preview_fixture,
    merge_solutions,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent


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

    def test_materialized_domain_adapter_joins_replay_and_release(self) -> None:
        raw = {
            "schema_version": 1,
            "environment": "production",
            "source_event_count": 8,
            "source_digest": "f" * 64,
            "submissions": [{
                "submission_id": "0198abcd-1111-7000-8000-000000000001",
                "actor": "alice",
                "declared_model": "Example Model Revision A",
                "evaluation": {
                    "status": "accepted",
                    "occurred_at": "2026-08-20T00:00:00Z",
                    "event_id": "0198abcd-0000-7000-8000-000000000001",
                    "benchmark_commit": "a" * 40,
                },
            }],
            "results": [{
                "result_id": "r2_" + "b" * 64,
                "submission_id": "0198abcd-1111-7000-8000-000000000001",
                "problem_id": "alpha",
                "statement_revision": 1,
                "declared_model": "Example Model Revision A",
                "recorded_at": "2026-08-20T00:00:01Z",
                "event_id": "0198abcd-0000-7000-8000-000000000002",
            }],
            "replay_tasks": [{
                "replay_task_id": "rt1_" + "c" * 64,
                "result_id": "r2_" + "b" * 64,
                "status": "accepted",
                "occurred_at": "2026-08-21T00:00:00Z",
                "attempt": 1,
                "checker": "lean4lean",
                "wall_time_ms": 20,
                "retired_instructions": None,
            }],
            "release_tasks": [{
                "result_id": "r2_" + "b" * 64,
                "status": "scheduled",
                "release_at": "2026-10-20T00:00:00Z",
            }],
        }
        aliases = {
            "Example Model Revision A": {
                "canonical_id": "example-model",
                "label": "Example Model",
            }
        }

        adapted = adapt_state_domain(raw, aliases)

        self.assertEqual(adapted[0].canonical_model_id, "example-model")
        self.assertEqual(adapted[0].replay["status"], "accepted")
        self.assertEqual(adapted[0].measurements[0]["status"], "unavailable")
        self.assertEqual(adapted[0].release["status"], "scheduled")

    def test_state_record_replaces_matching_legacy_base_record(self) -> None:
        legacy = solution("legacy_a", "alpha", "model-a", "2026-08-20T00:00:00Z", "issue-1")
        state = solution("r2_a", "alpha", "model-a", "2026-08-20T00:00:00Z", "event-1")

        merged = merge_solutions([state], [legacy])

        self.assertEqual([item.result_id for item in merged], ["r2_a"])


if __name__ == "__main__":
    unittest.main()

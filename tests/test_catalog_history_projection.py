from __future__ import annotations

import pathlib
import tempfile
import unittest
from unittest.mock import patch

from scripts.generate_site_data import load_manifest
from scripts.lifecycle_site_data import build_lifecycle_projection

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "catalog-history"


def load_fixture(name: str):
    with patch("scripts.generate_site_data.load_holes", return_value=()):
        return load_manifest(FIXTURES / name, pathlib.Path("benchmark"))[0]


def project(problem):
    return build_lifecycle_projection(
        problems=[problem],
        solutions=[],
        set_definitions=[],
        tag_registry={},
        fixture={},
        generated_at="2026-08-26T00:00:00Z",
        benchmark_commit="a" * 40,
        state_commit=None,
        state_metadata=None,
        site_base_url="https://example.test/eval/",
    )


class CatalogHistoryProjectionTests(unittest.TestCase):
    def test_client_handles_empty_history_and_calendar_dates(self) -> None:
        client = (ROOT / "static" / "lifecycle-preview.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("No recorded status transitions.", client)
        self.assertIn("Number(calendar[2]) - 1", client)

    def test_current_canonical_status_fixture_projects_real_history(self) -> None:
        problem = load_fixture("canonical")
        payload = project(problem)[
            "v2/problems/coc_strong_normalization.json"
        ]

        self.assertEqual(problem.status_history, (
            {
                "status": "draft",
                "effective_date": "2026-08-25",
                "reason": "correction",
            },
        ))
        self.assertEqual(payload["lifecycle"]["status_history"], [
            {
                "status": "draft",
                "effective_at": "2026-08-25",
                "reason": "correction",
                "source": "catalog-manifest",
            }
        ])
        self.assertFalse(
            any(
                "status transition history is recorded" in limitation
                for limitation in payload["data_limitations"]
            )
        )

    def test_real_manifest_history_is_projected_without_losing_fields(self) -> None:
        problem = load_fixture("with-history")
        files = project(problem)
        lifecycle = files[
            "v2/problems/catalog_history_fixture.json"
        ]["lifecycle"]

        self.assertEqual(
            lifecycle["status_history"],
            [
                {
                    "status": "draft",
                    "effective_at": "2026-07-01",
                    "reason": "initial",
                    "source": "catalog-manifest",
                },
                {
                    "status": "active",
                    "effective_at": "2026-08-20",
                    "reason": "policy",
                    "source": "catalog-manifest",
                },
            ],
        )
        self.assertEqual(
            lifecycle["statement_revisions"],
            [
                {
                    "revision": 2,
                    "status": "superseded",
                    "effective_at": "2026-07-15",
                    "reason": "statement-change",
                    "statement_digest": "sha256:" + "a" * 64,
                    "source": "catalog-manifest",
                },
                {
                    "revision": 3,
                    "status": "current",
                    "effective_at": "2026-08-21",
                    "reason": "correction",
                    "statement_digest": "sha256:" + "b" * 64,
                    "source": "catalog-manifest",
                },
            ],
        )
        self.assertFalse(
            any(
                "Catalog lifecycle history beyond" in limitation
                for limitation in files["v2/index.json"]["data_limitations"]
            )
        )

    def test_manifest_history_order_is_enforced(self) -> None:
        original = (
            FIXTURES / "with-history" / "catalog_history_fixture.toml"
        ).read_text(encoding="utf-8")
        cases = {
            "status": original.replace(
                'effective_date = "2026-08-20"',
                'effective_date = "2026-06-30"',
            ),
            "revision": original.replace("revision = 3", "revision = 1"),
        }
        for label, manifest in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = pathlib.Path(raw)
                (root / "catalog_history_fixture.toml").write_text(
                    manifest, encoding="utf-8"
                )
                with (
                    patch("scripts.generate_site_data.load_holes", return_value=()),
                    self.assertRaisesRegex(SystemExit, "increase strictly"),
                ):
                    load_manifest(root, pathlib.Path("benchmark"))

    def test_terminal_history_must_equal_current_manifest_state(self) -> None:
        original = (
            FIXTURES / "with-history" / "catalog_history_fixture.toml"
        ).read_text(encoding="utf-8")
        cases = {
            "status": (
                original.replace('status = "active"', 'status = "archived"', 1),
                "current status",
            ),
            "revision": (
                original.replace("statement_revision = 3", "statement_revision = 4"),
                "statement_revision",
            ),
        }
        for label, (manifest, message) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = pathlib.Path(raw)
                (root / "catalog_history_fixture.toml").write_text(
                    manifest, encoding="utf-8"
                )
                with (
                    patch("scripts.generate_site_data.load_holes", return_value=()),
                    self.assertRaisesRegex(SystemExit, message),
                ):
                    load_manifest(root, pathlib.Path("benchmark"))

    def test_current_state_does_not_fabricate_history(self) -> None:
        problem = load_fixture("without-history")
        files = project(problem)
        payload = files["v2/problems/catalog_current_only.json"]

        self.assertEqual(payload["lifecycle"]["status_history"], [])
        self.assertEqual(payload["lifecycle"]["statement_revisions"], [])
        self.assertEqual(payload["problem"]["current_status"], "draft")
        self.assertEqual(payload["problem"]["statement_revision"], 1)
        self.assertTrue(
            any(
                "no lifecycle history for any visible problem" in limitation
                for limitation in files["v2/index.json"]["data_limitations"]
            )
        )
        history_limitations = [
            limitation
            for limitation in payload["data_limitations"]
            if "history is recorded" in limitation
        ]
        self.assertEqual(len(history_limitations), 2)
        self.assertTrue(
            all(
                "no history entry is fabricated" in limitation
                for limitation in history_limitations
            )
        )


if __name__ == "__main__":
    unittest.main()

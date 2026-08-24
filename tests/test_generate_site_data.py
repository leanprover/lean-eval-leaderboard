import json
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.generate_site_data import (
    dedupe_universe_declarations,
    fetch_json_url,
    load_manifest,
    load_results,
    preserve_root_declarations,
    qualify_probability_root_opens,
)


class SnapshotContextTests(unittest.TestCase):
    @patch("scripts.generate_site_data.time.sleep")
    @patch("scripts.generate_site_data.urllib.request.urlopen")
    def test_retries_transient_json_fetches(
        self, urlopen: MagicMock, sleep: MagicMock
    ) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'
        urlopen.side_effect = [OSError("rate limited"), response]

        self.assertEqual(
            fetch_json_url("https://example.test/data.json", retry_delay_seconds=2),
            {"ok": True},
        )
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2)


class CatalogMetadataTests(unittest.TestCase):
    manifest = """\
id = "alpha"
title = "Alpha"
group = "formalization-evaluation"
status = "draft"
visible = false
statement_revision = 2
tags = ["annals"]
module = "LeanEval.Alpha"
holes = ["alpha"]
submitter = "Alice"
"""

    @patch("scripts.generate_site_data.load_holes", return_value=())
    def test_loads_required_catalog_metadata(self, _load_holes: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_dir = pathlib.Path(directory)
            (manifest_dir / "alpha.toml").write_text(self.manifest)
            loaded = load_manifest(manifest_dir, pathlib.Path("benchmark"))

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].group, "formalization-evaluation")
        self.assertEqual(loaded[0].status, "draft")
        self.assertFalse(loaded[0].visible)
        self.assertEqual(loaded[0].statement_revision, 2)
        self.assertEqual(loaded[0].tags, ("annals",))

    @patch("scripts.generate_site_data.load_holes", return_value=())
    def test_missing_visible_field_fails_closed(self, _load_holes: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_dir = pathlib.Path(directory)
            (manifest_dir / "alpha.toml").write_text(
                self.manifest.replace("visible = false\n", "")
            )
            with self.assertRaisesRegex(SystemExit, "visible must be a boolean"):
                load_manifest(manifest_dir, pathlib.Path("benchmark"))


class ResultOwnerBindingTests(unittest.TestCase):
    def test_results_owner_must_match_canonical_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "bob.json").write_text(
                json.dumps({"schema_version": 1, "user": "alice", "solved": {}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "matching its filename"):
                load_results(root)

    def test_results_owner_filename_match_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            document = {"schema_version": 1, "user": "Alice", "solved": {}}
            (root / "alice.json").write_text(
                json.dumps(document), encoding="utf-8"
            )

            self.assertEqual(load_results(root), [document])


class SnapshotTransformationTests(unittest.TestCase):
    def test_deduplicates_universes_across_inlined_modules(self) -> None:
        fragments = [
            "universe u v\ndef first := 1",
            "universe u w -- shared context\nuniverse v -- keep this comment",
        ]

        self.assertEqual(
            dedupe_universe_declarations(fragments),
            [
                "universe u v\ndef first := 1",
                "universe w -- shared context\n-- keep this comment",
            ],
        )

    def test_roots_only_explicitly_selected_dotted_declarations(self) -> None:
        fragment = (
            "def Nat.IsCubeFree (n : Nat) : Prop := True\n"
            "noncomputable def Local.helper : Nat := 1\n"
            "def _root_.Nat.AlreadyRooted : Nat := 2"
        )

        self.assertEqual(
            preserve_root_declarations(fragment, {"Nat.IsCubeFree"}),
            (
                "def _root_.Nat.IsCubeFree (n : Nat) : Prop := True\n"
                "noncomputable def Local.helper : Nat := 1\n"
                "def _root_.Nat.AlreadyRooted : Nat := 2"
            ),
        )

    def test_qualifies_only_ordinary_probability_opens(self) -> None:
        fragment = (
            "  open  ProbabilityTheory MeasureTheory -- needed for measures\n"
            "open scoped ProbabilityTheory\n"
            "namespace ProbabilityTheory"
        )

        self.assertEqual(
            qualify_probability_root_opens(fragment),
            (
                "  open  _root_.ProbabilityTheory MeasureTheory -- needed for measures\n"
                "open scoped ProbabilityTheory\n"
                "namespace ProbabilityTheory"
            ),
        )


if __name__ == "__main__":
    unittest.main()

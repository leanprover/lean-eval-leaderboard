import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.generate_site_data import (
    dedupe_universe_declarations,
    fetch_json_url,
    load_manifest,
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
        fragment = "\n".join(
            [
                "def Nat.IsCubeFree (n : Nat) : Prop := True",
                "noncomputable def Local.helper : Nat := 1",
                "def _root_.Nat.AlreadyRooted : Nat := 2",
            ]
        )

        self.assertEqual(
            preserve_root_declarations(fragment, {"Nat.IsCubeFree"}),
            "\n".join(
                [
                    "def _root_.Nat.IsCubeFree (n : Nat) : Prop := True",
                    "noncomputable def Local.helper : Nat := 1",
                    "def _root_.Nat.AlreadyRooted : Nat := 2",
                ]
            ),
        )

    def test_qualifies_only_ordinary_probability_opens(self) -> None:
        fragment = "\n".join(
            [
                "  open  ProbabilityTheory MeasureTheory -- needed for measures",
                "open scoped ProbabilityTheory",
                "namespace ProbabilityTheory",
            ]
        )

        self.assertEqual(
            qualify_probability_root_opens(fragment),
            "\n".join(
                [
                    "  open  _root_.ProbabilityTheory MeasureTheory -- needed for measures",
                    "open scoped ProbabilityTheory",
                    "namespace ProbabilityTheory",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()

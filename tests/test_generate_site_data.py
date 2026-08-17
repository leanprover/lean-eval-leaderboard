import unittest

from scripts.generate_site_data import (
    dedupe_universe_declarations,
    preserve_root_declarations,
    qualify_probability_root_opens,
)


class SnapshotContextTests(unittest.TestCase):
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

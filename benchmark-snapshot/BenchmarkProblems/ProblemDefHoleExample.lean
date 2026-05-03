import Mathlib

/-!
Minimal example exercising the def-hole / multi-hole eval-problem pipeline.

A `def` and a `theorem` referring to it, both `sorry`. A submission
defines `Submission.foo := 37` and proves `Submission.foo_def`; comparator
should accept it.
-/
-- ANCHOR: def_hole_example__foo
def foo : Nat := sorry
-- ANCHOR_END: def_hole_example__foo
-- ANCHOR: def_hole_example__foo_def
theorem foo_def : foo = 37 := sorry
-- ANCHOR_END: def_hole_example__foo_def

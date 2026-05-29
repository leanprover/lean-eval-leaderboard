import Mathlib

/-!
Regression test for the multi-hole / trusted-helpers pipeline. Exercises
three failure modes the generator used to have:

1. **Root-level helpers** (`rootHelper`) — no enclosing namespace, so the
   generator must *not* emit a spurious `open` for them.

2. **Helpers in a namespace that differs from the module's last path
   component** (`Helpers.preHole`, `Helpers.postHole`) — the injected
   `open` line must be derived from the helper names, not from
   `lastComponentStr entry.moduleName`.

3. **A helper that appears in source order *after* a hole**
   (`Helpers.postHole` between `first` and `second_eq`) — helper byte
   ranges computed from the raw source must remain valid when applied
   alongside hole-body replacement; a sequential strip-then-replace
   pipeline (with ranges derived from `.ilean`) would corrupt this case.
-/


namespace Helpers
-- ANCHOR: multi_hole_helpers_example__first
def first : Nat := sorry
-- ANCHOR_END: multi_hole_helpers_example__first
-- ANCHOR: multi_hole_helpers_example__second_eq
theorem second_eq : first + rootHelper + preHole = first + 141 := sorry
-- ANCHOR_END: multi_hole_helpers_example__second_eq
-- ANCHOR: multi_hole_helpers_example__third_eq
theorem third_eq : postHole = 1000 := sorry
-- ANCHOR_END: multi_hole_helpers_example__third_eq

end Helpers

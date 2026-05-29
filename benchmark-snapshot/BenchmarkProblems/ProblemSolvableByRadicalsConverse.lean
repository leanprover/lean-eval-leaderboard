import Mathlib

namespace ProblemSolvableByRadicalsConverse

open Polynomial IntermediateField

-- ANCHOR: solvable_by_radicals_converse__solvable_iff_solvableByRad
theorem solvable_iff_solvableByRad (F : Type*) [Field F] [CharZero F]
    (p : F[X]) (_hp : p ≠ 0) :
    (∀ x : AlgebraicClosure F, aeval x p = 0 →
        x ∈ solvableByRad F (AlgebraicClosure F)) ↔ IsSolvable p.Gal := by
  sorry
-- ANCHOR_END: solvable_by_radicals_converse__solvable_iff_solvableByRad

end ProblemSolvableByRadicalsConverse

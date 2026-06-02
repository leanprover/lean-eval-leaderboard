import Mathlib

namespace ProblemAbelRuffini

open Polynomial

-- ANCHOR: abel_ruffini__abel_ruffini
theorem abel_ruffini (n : ℕ) (_hn : 1 ≤ n) :
    (∀ p : ℚ[X], p.natDegree = n → ∀ x : ℂ, aeval x p = 0 →
        x ∈ solvableByRad ℚ ℂ) ↔ n ≤ 4 := by
  sorry
-- ANCHOR_END: abel_ruffini__abel_ruffini

end ProblemAbelRuffini

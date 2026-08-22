import Mathlib.Analysis.SpecialFunctions.Pow.Real

namespace ProblemAnnalsLargeValueEstimates

/-!
# Main Statement from New large value estimates for Dirichlet polynomials

We formalise the statement of the main result from L. Guth and J. Maynard,
`New large value estimates for Dirichlet polynomials`, Annals of Math, 203 (2) 2026.
-/

set_option autoImplicit false

namespace LargeValueEstimates

open Asymptotics Complex

/-- The bound `N^2 V^(-2) + N^(18/5) V^(-4) + T N^(12/5) V^(-4)` appearing in Theorem 1.1. -/
noncomputable def bound (N : ℕ) (V T : ℝ) : ℝ :=
  N ^ 2 * V ^ (- 2 : ℤ) + N ^ (18 / 5 : ℝ) * V ^ (- 4 : ℤ) + T * N ^ (12 / 5 : ℝ) * V ^ (- 4 : ℤ)



end LargeValueEstimates

open LargeValueEstimates
open Asymptotics Complex

set_option autoImplicit false

-- ANCHOR: annals_large_value_estimates__theorem_1_1
theorem theorem_1_1 : ∃ o : ℝ → ℝ, o =o[Filter.atTop] (1 : ℝ → ℝ) ∧
    ∀ (b : ℕ → ℂ) (_hb : ∀ n, ‖b n‖ ≤ 1) (N : ℕ) (V : ℝ) (T : ℝ) (R : ℕ) (t : Fin R → ℝ),
    N > 0 → V > 0 → T > 1 → -- these assumptions are necessary but not stated in the paper
    (∀ i j, i ≠ j → |t i - t j| ≥ 1) → (∀ i, t i ∈ Set.Icc 0 T) →
    (∀ r, ‖∑ n ∈ Finset.Icc N (2 * N), b n * n ^ (I * t r)‖ ≥ V) →
    R ≤ T ^ (o T) * bound N V T := by
  sorry
-- ANCHOR_END: annals_large_value_estimates__theorem_1_1

end ProblemAnnalsLargeValueEstimates

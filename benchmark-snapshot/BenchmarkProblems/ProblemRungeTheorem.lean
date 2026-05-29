import Mathlib

namespace ProblemRungeTheorem

open scoped Polynomial

-- ANCHOR: runge_theorem__runge
theorem runge (K : Set ℂ) (_hK : IsCompact K) (U : Set ℂ) (_hU : IsOpen U)
    (_hKU : K ⊆ U) (f : ℂ → ℂ) (_hf : AnalyticOnNhd ℂ f U)
    (ε : ℝ) (_hε : 0 < ε) :
    ∃ p q : ℂ[X], (∀ z ∈ K, q.eval z ≠ 0) ∧
      (∀ z ∈ K, ‖f z - p.eval z / q.eval z‖ < ε) := by
  sorry
-- ANCHOR_END: runge_theorem__runge

end ProblemRungeTheorem

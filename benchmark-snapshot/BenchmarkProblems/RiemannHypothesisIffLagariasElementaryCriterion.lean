import Mathlib

namespace FormalMathEval
namespace NumberTheory

open scoped ArithmeticFunction.sigma

/-!
Lagarias' elementary criterion for the Riemann hypothesis.

Mathlib already provides `RiemannHypothesis`, harmonic numbers `harmonic`, and the divisor-sum
function `σ`, so the equivalence can be stated directly.
-/

def LagariasElementaryCriterion : Prop :=
  ∀ n : ℕ,
    0 < n →
      ((σ 1 n : ℕ) : ℝ) ≤
        (harmonic n : ℝ) +
          Real.exp (harmonic n : ℝ) * Real.log (harmonic n : ℝ)



end NumberTheory
end FormalMathEval

open scoped ArithmeticFunction.sigma

-- ANCHOR: riemann_hypothesis_iff_lagarias_elementary_criterion
theorem riemann_hypothesis_iff_lagarias_elementary_criterion :
    RiemannHypothesis ↔ LagariasElementaryCriterion := by
  sorry
-- ANCHOR_END: riemann_hypothesis_iff_lagarias_elementary_criterion

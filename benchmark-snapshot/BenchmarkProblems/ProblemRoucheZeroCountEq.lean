import Mathlib.Analysis.Complex.ValueDistribution.LogCounting.Basic

namespace ProblemRoucheZeroCountEq

open MeromorphicOn

-- ANCHOR: rouche_zero_count_eq__rouche_zero_count_eq
theorem rouche_zero_count_eq {f g : ℂ → ℂ} {R : ℝ}
    (hR : 0 < R)
    (hf : MeromorphicOn f Set.univ)
    (hg : AnalyticOn ℂ g Set.univ)
    (hbound : ∀ z : ℂ, ‖z‖ = R → ‖g z‖ < ‖f z‖) :
    (∑ᶠ z, ((divisor (f + g) (Metric.closedBall 0 R))⁺) z) =
      (∑ᶠ z, ((divisor f (Metric.closedBall 0 R))⁺) z) := by
  sorry
-- ANCHOR_END: rouche_zero_count_eq__rouche_zero_count_eq

end ProblemRoucheZeroCountEq

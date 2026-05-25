import Mathlib

namespace ProblemSchoenflies

-- ANCHOR: schoenflies__schoenflies
theorem schoenflies (r : Metric.sphere (0 : EuclideanSpace ℝ (Fin 2)) 1 → EuclideanSpace ℝ (Fin 2))
    (_hcont : Continuous r) (_hinj : Function.Injective r) :
    ∃ h : EuclideanSpace ℝ (Fin 2) ≃ₜ EuclideanSpace ℝ (Fin 2),
      h '' Set.range r = Metric.sphere (0 : EuclideanSpace ℝ (Fin 2)) 1 := by
  sorry
-- ANCHOR_END: schoenflies__schoenflies

end ProblemSchoenflies

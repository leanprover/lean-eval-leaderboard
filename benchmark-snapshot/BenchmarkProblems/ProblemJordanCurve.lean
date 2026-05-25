import Mathlib

namespace ProblemJordanCurve

-- ANCHOR: jordan_curve__jordan_curve
theorem jordan_curve (r : Metric.sphere (0 : EuclideanSpace ℝ (Fin 2)) 1 → EuclideanSpace ℝ (Fin 2))
    (_hcont : Continuous r) (_hinj : Function.Injective r) :
    Nat.card
        (ConnectedComponents ((Set.range r)ᶜ : Set (EuclideanSpace ℝ (Fin 2)))) =
      2 := by
  sorry
-- ANCHOR_END: jordan_curve__jordan_curve

end ProblemJordanCurve

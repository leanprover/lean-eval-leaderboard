import Mathlib

namespace ProblemBauerExtremePointUniqueness

open MeasureTheory

variable {X : Type*} [NormedAddCommGroup X] [NormedSpace ℝ X] [CompleteSpace X]

-- ANCHOR: bauer_extreme_point_uniqueness__bauer_unique
theorem bauer_unique [MeasurableSpace X] [BorelSpace X]
    (K : Set X) (hK_cpt : IsCompact K) (hK_cvx : Convex ℝ K)
    {x : X} (hx : x ∈ K.extremePoints ℝ)
    (μ : Measure X) [IsProbabilityMeasure μ]
    (hμ : μ Kᶜ = 0) (hbar : x = ∫ y, y ∂μ) :
    μ = Measure.dirac x := by
  sorry
-- ANCHOR_END: bauer_extreme_point_uniqueness__bauer_unique

end ProblemBauerExtremePointUniqueness

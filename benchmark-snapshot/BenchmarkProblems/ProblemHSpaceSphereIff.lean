import Mathlib

namespace ProblemHSpaceSphereIff

-- ANCHOR: hSpace_sphere_iff__hSpace_sphere_iff
theorem hSpace_sphere_iff (n : ℕ) :
    Nonempty (HSpace (Metric.sphere (0 : EuclideanSpace ℝ (Fin (n + 1))) 1)) ↔
      n = 0 ∨ n = 1 ∨ n = 3 ∨ n = 7 := by
  sorry
-- ANCHOR_END: hSpace_sphere_iff__hSpace_sphere_iff

end ProblemHSpaceSphereIff

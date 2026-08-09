import Mathlib

namespace ProblemPi6SphereThreeMulEquivZmodTwelve

-- ANCHOR: pi6_sphere_three_mulEquiv_zmod_twelve__pi6_sphere_three_mulEquiv_zmod_twelve
theorem pi6_sphere_three_mulEquiv_zmod_twelve (x : Metric.sphere (0 : EuclideanSpace ℝ (Fin 4)) 1) :
    Nonempty
      (HomotopyGroup.Pi 6 (Metric.sphere (0 : EuclideanSpace ℝ (Fin 4)) 1) x ≃*
        Multiplicative (ZMod 12)) := by
  sorry
-- ANCHOR_END: pi6_sphere_three_mulEquiv_zmod_twelve__pi6_sphere_three_mulEquiv_zmod_twelve

end ProblemPi6SphereThreeMulEquivZmodTwelve

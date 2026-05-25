import Mathlib

namespace ProblemMilnorExoticSphereSeven

open scoped Manifold ContDiff
open Metric (sphere)

-- ANCHOR: milnor_exotic_sphere_seven__milnor_exotic_sphere_seven
theorem milnor_exotic_sphere_seven :
    ∃ (M : Type) (_ : TopologicalSpace M)
      (_ : ChartedSpace (EuclideanSpace ℝ (Fin 7)) M)
      (_ : IsManifold (𝓡 7) ∞ M)
      (_homeo : M ≃ₜ sphere (0 : EuclideanSpace ℝ (Fin 8)) 1),
      IsEmpty (M ≃ₘ⟮𝓡 7, 𝓡 7⟯ sphere (0 : EuclideanSpace ℝ (Fin 8)) 1) := by
  sorry
-- ANCHOR_END: milnor_exotic_sphere_seven__milnor_exotic_sphere_seven

end ProblemMilnorExoticSphereSeven

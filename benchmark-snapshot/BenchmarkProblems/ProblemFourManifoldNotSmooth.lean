import Mathlib

namespace ProblemFourManifoldNotSmooth

open scoped Manifold ContDiff

local notation "𝔼" => EuclideanSpace ℝ (Fin 4)

-- ANCHOR: four_manifold_not_smooth__four_manifold_not_smooth
theorem four_manifold_not_smooth :
    ∃ (M : Type*) (_ : TopologicalSpace M) (_ : T2Space M) (_: CompactSpace M)
      (_ : SimplyConnectedSpace M) (_ : Nonempty (ChartedSpace 𝔼 M)),
      ∀ (_ : ChartedSpace 𝔼 M), ¬ IsManifold (𝓡 4) ∞ M := by
  sorry
-- ANCHOR_END: four_manifold_not_smooth__four_manifold_not_smooth

end ProblemFourManifoldNotSmooth

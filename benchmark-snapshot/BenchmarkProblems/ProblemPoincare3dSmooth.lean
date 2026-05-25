import Mathlib

namespace ProblemPoincare3dSmooth

open scoped Manifold ContDiff
open Metric (sphere)

-- ANCHOR: poincare_3d_smooth__poincare_3d_smooth
theorem poincare_3d_smooth {M : Type*} [TopologicalSpace M] [T2Space M]
    [ChartedSpace (EuclideanSpace ℝ (Fin 3)) M] [IsManifold (𝓡 3) ∞ M]
    [SimplyConnectedSpace M] [CompactSpace M] :
    Nonempty (M ≃ₘ⟮𝓡 3, 𝓡 3⟯ sphere (0 : EuclideanSpace ℝ (Fin 4)) 1) := by
  sorry
-- ANCHOR_END: poincare_3d_smooth__poincare_3d_smooth

end ProblemPoincare3dSmooth

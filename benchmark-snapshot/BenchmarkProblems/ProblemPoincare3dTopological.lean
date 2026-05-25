import Mathlib

namespace ProblemPoincare3dTopological

open Metric (sphere)

-- ANCHOR: poincare_3d_topological__poincare_3d_topological
theorem poincare_3d_topological {M : Type*} [TopologicalSpace M] [T2Space M]
    [ChartedSpace (EuclideanSpace ℝ (Fin 3)) M]
    [SimplyConnectedSpace M] [CompactSpace M] :
    Nonempty (M ≃ₜ sphere (0 : EuclideanSpace ℝ (Fin 4)) 1) := by
  sorry
-- ANCHOR_END: poincare_3d_topological__poincare_3d_topological

end ProblemPoincare3dTopological

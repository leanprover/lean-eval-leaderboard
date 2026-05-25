import Mathlib

namespace ProblemPoincareHighDimTopological

open Metric (sphere)
open ContinuousMap

-- ANCHOR: poincare_high_dim_topological__poincare_high_dim_topological
theorem poincare_high_dim_topological {n : ℕ} (_h5 : 5 ≤ n)
    {M : Type*} [TopologicalSpace M] [T2Space M]
    [ChartedSpace (EuclideanSpace ℝ (Fin n)) M]
    (_h : M ≃ₕ sphere (0 : EuclideanSpace ℝ (Fin (n + 1))) 1) :
    Nonempty (M ≃ₜ sphere (0 : EuclideanSpace ℝ (Fin (n + 1))) 1) := by
  sorry
-- ANCHOR_END: poincare_high_dim_topological__poincare_high_dim_topological

end ProblemPoincareHighDimTopological

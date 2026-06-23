import Mathlib.Analysis.InnerProductSpace.Laplacian
import Mathlib.Topology.MetricSpace.Lipschitz

namespace ProblemSemilinearPoissonRadialSymmetry

namespace LeanEval
namespace Analysis
namespace PDE

/-!
# Radial symmetry for a semilinear Poisson equation

Suppose `u` is a positive solution to a semilinear Poisson PDE:

  `-Δ u = f(u)` in the open unit ball,
  `u = 0` on the boundary.

For Lipschitz `f`, every `C^2` solution on the closed ball is radial and
strictly decreasing as a function of the radius.
-/

open Metric
open scoped NNReal

/-- `u` solved a semilinear Poisson problem if `-Δ u = f(u)` in the open unit
ball and `u = 0` on the unit sphere. -/
def SolvesSemilinearPoisson {n : ℕ} (f : ℝ → ℝ) (u : EuclideanSpace ℝ (Fin n) → ℝ) : Prop :=
  (∀ x ∈ ball 0 1, -Laplacian.laplacian u x = f (u x)) ∧ ∀ x ∈ sphere 0 1, u x = 0



end PDE
end Analysis
end LeanEval

open LeanEval.Analysis.PDE
open Metric
open scoped NNReal

-- ANCHOR: semilinear_poisson_radial_symmetry__semilinear_poisson_radial_symmetry
theorem semilinear_poisson_radial_symmetry {n : ℕ} (hn : 0 < n)
    {f : ℝ → ℝ} (u : EuclideanSpace ℝ (Fin n) → ℝ)
    (hf_lipschitz : ∃ K : ℝ≥0, LipschitzWith K f)
    (hu_c2 : ContDiffOn ℝ 2 u (closedBall 0 1))
    (hu_solve : LeanEval.Analysis.PDE.SolvesSemilinearPoisson f u)
    (hu_positive : ∀ x ∈ ball 0 1, 0 < u x) :
    ∃ v : ℝ → ℝ≥0,
      StrictAntiOn v (Set.Icc (0 : ℝ) 1) ∧
        ∀ x ∈ closedBall 0 1, u x = v ‖x‖ := by
  sorry
-- ANCHOR_END: semilinear_poisson_radial_symmetry__semilinear_poisson_radial_symmetry

end ProblemSemilinearPoissonRadialSymmetry

import Mathlib.Analysis.Complex.Circle
import Mathlib.Data.ZMod.Basic
import Mathlib.Geometry.Manifold.Instances.Sphere
import Mathlib.Topology.Homotopy.HomotopyGroup

namespace ProblemPiSuccSphereNMulEquivZmodTwo

-- ANCHOR: pi_succ_sphere_n_mulEquiv_zmod_two__pi_succ_sphere_n_mulEquiv_zmod_two
theorem pi_succ_sphere_n_mulEquiv_zmod_two (n : ℕ) (hn : 3 ≤ n)
    (x : Metric.sphere (0 : EuclideanSpace ℝ (Fin (n + 1))) 1) :
    Nonempty
      (HomotopyGroup.Pi (n + 1) (Metric.sphere (0 : EuclideanSpace ℝ (Fin (n + 1))) 1) x ≃*
        Multiplicative (ZMod 2)) := by
  sorry
-- ANCHOR_END: pi_succ_sphere_n_mulEquiv_zmod_two__pi_succ_sphere_n_mulEquiv_zmod_two

end ProblemPiSuccSphereNMulEquivZmodTwo

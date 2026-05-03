import Mathlib.Analysis.Complex.Circle
import Mathlib.Data.ZMod.Basic
import Mathlib.Geometry.Manifold.Instances.Sphere
import Mathlib.Topology.Homotopy.HomotopyGroup

namespace ProblemPi1CircleMulEquivInt

-- ANCHOR: pi1_circle_mulEquiv_int__pi1_circle_mulEquiv_int
theorem pi1_circle_mulEquiv_int :
    Nonempty (HomotopyGroup.Pi 1 Circle (1 : Circle) ≃* Multiplicative ℤ) := by
  sorry
-- ANCHOR_END: pi1_circle_mulEquiv_int__pi1_circle_mulEquiv_int

end ProblemPi1CircleMulEquivInt

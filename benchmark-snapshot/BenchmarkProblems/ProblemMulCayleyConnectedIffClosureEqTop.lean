import Mathlib.Combinatorics.SimpleGraph.Cayley
import Mathlib.Combinatorics.SimpleGraph.Connectivity.Connected
import Mathlib.Algebra.Group.Subgroup.Lattice

namespace ProblemMulCayleyConnectedIffClosureEqTop

-- ANCHOR: mulCayley_connected_iff_closure_eq_top__mulCayley_connected_iff_closure_eq_top
theorem mulCayley_connected_iff_closure_eq_top {G : Type*} [Group G]
    (S : Set G) :
    (SimpleGraph.mulCayley S).Connected ↔ Subgroup.closure S = ⊤ := by
  sorry
-- ANCHOR_END: mulCayley_connected_iff_closure_eq_top__mulCayley_connected_iff_closure_eq_top

end ProblemMulCayleyConnectedIffClosureEqTop

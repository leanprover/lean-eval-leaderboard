import Mathlib.Analysis.Matrix.Order
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

namespace ProblemPosSemidefMapExp

open scoped MatrixOrder Matrix

-- ANCHOR: posSemidef_map_exp__posSemidef_map_exp
theorem posSemidef_map_exp {n : Type*} [Fintype n] [DecidableEq n]
    {A : Matrix n n ℝ} (hA : A.PosSemidef) :
    (A.map Real.exp).PosSemidef := by
  sorry
-- ANCHOR_END: posSemidef_map_exp__posSemidef_map_exp

end ProblemPosSemidefMapExp

import Mathlib.Analysis.Matrix.Order

namespace ProblemOppenheimInequality

open scoped MatrixOrder Matrix

-- ANCHOR: oppenheim_inequality__oppenheim_inequality
theorem oppenheim_inequality {n : Type*} [Fintype n] [DecidableEq n]
    {A B : Matrix n n ℝ} (hA : A.PosSemidef) (hB : B.PosSemidef) :
    A.det * ∏ i, B i i ≤ (A ⊙ B).det := by
  sorry
-- ANCHOR_END: oppenheim_inequality__oppenheim_inequality

end ProblemOppenheimInequality

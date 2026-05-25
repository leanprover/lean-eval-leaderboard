import Mathlib

namespace ProblemLidskiiInequality

open Matrix

-- ANCHOR: lidskii_inequality__lidskii_inequality
theorem lidskii_inequality {n : Type*} [Fintype n] [DecidableEq n]
    {A B : Matrix n n ℂ} (hA : A.IsHermitian) (hB : B.IsHermitian)
    {p : ℝ} (_hp : 1 ≤ p) :
    ∑ j, |hA.eigenvalues₀ j - hB.eigenvalues₀ j| ^ p ≤
      ∑ j, |(hB.sub hA).eigenvalues₀ j| ^ p := by
  sorry
-- ANCHOR_END: lidskii_inequality__lidskii_inequality

end ProblemLidskiiInequality

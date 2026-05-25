import Mathlib

namespace ProblemLidskiiLast

open Matrix

-- ANCHOR: lidskii_last__lidskii_last
theorem lidskii_last {n : Type*} [Fintype n] [DecidableEq n]
    {A B : Matrix n n ℂ} (hA : A.IsHermitian) (hB : B.IsHermitian) :
    ∑ j, |hA.eigenvalues₀ j - hB.eigenvalues₀ j| ≤
      ∑ i, ∑ j, ‖A i j - B i j‖ := by
  sorry
-- ANCHOR_END: lidskii_last__lidskii_last

end ProblemLidskiiLast

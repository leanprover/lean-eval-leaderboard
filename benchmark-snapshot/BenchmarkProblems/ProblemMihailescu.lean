import Mathlib

namespace ProblemMihailescu

-- ANCHOR: mihailescu__mihailescu
theorem mihailescu {x y m n : ℕ}
    (hx : 0 < x) (hy : 0 < y) (hm : 1 < m) (hn : 1 < n)
    (h : x ^ m = y ^ n + 1) :
    x = 3 ∧ y = 2 ∧ m = 2 ∧ n = 3 := by
  sorry
-- ANCHOR_END: mihailescu__mihailescu

end ProblemMihailescu

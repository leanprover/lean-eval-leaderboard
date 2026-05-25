import Mathlib

namespace ProblemFeitThompson

-- ANCHOR: feit_thompson__feit_thompson
theorem feit_thompson {G : Type*} [Group G] [Finite G]
    (_h : Odd (Nat.card G)) : IsSolvable G := by
  sorry
-- ANCHOR_END: feit_thompson__feit_thompson

end ProblemFeitThompson

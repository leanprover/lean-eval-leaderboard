import Mathlib

namespace ProblemVariableBinderExample

variable {n : Type*} [Fintype n] [DecidableEq n]

-- ANCHOR: variable_binder_example__variable_binder_example
theorem variable_binder_example (A : Matrix n n ℚ) (hA : A.IsHermitian) :
    A.trace = ∑ i, A i i := by
  sorry
-- ANCHOR_END: variable_binder_example__variable_binder_example

end ProblemVariableBinderExample

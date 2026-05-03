import Mathlib.Analysis.Calculus.IteratedDeriv.Defs
import Mathlib.Analysis.Complex.Basic

namespace ProblemDeBrangesTheorem

open Metric

-- ANCHOR: deBranges_theorem__deBranges
theorem deBranges (f : ℂ → ℂ) (diff : DifferentiableOn ℂ f (ball 0 1)) (inj : (ball 0 1).InjOn f)
    (h0 : f 0 = 0) (h1 : deriv f 0 = 1) (n : ℕ) : ‖iteratedDeriv n f 0 / n.factorial‖ ≤ n := by
  sorry
-- ANCHOR_END: deBranges_theorem__deBranges

end ProblemDeBrangesTheorem

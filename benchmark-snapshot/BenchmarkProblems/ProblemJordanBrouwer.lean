import Mathlib

namespace ProblemJordanBrouwer

-- ANCHOR: jordan_brouwer__jordan_brouwer
theorem jordan_brouwer (d : ℕ) (_hd : 2 ≤ d)
    (r : Metric.sphere (0 : EuclideanSpace ℝ (Fin d)) 1 → EuclideanSpace ℝ (Fin d))
    (_hcont : Continuous r) (_hinj : Function.Injective r) :
    Nat.card
        (ConnectedComponents ((Set.range r)ᶜ : Set (EuclideanSpace ℝ (Fin d)))) =
      2 := by
  sorry
-- ANCHOR_END: jordan_brouwer__jordan_brouwer

end ProblemJordanBrouwer

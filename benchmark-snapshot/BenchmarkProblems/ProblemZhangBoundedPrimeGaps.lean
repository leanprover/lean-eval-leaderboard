import Mathlib

namespace ProblemZhangBoundedPrimeGaps

open Filter Finset MeasureTheory
open scoped BigOperators Topology

-- ANCHOR: zhang_bounded_prime_gaps__zhang_bounded_prime_gaps
theorem zhang_bounded_prime_gaps :
    ∀ n : ℕ, ∃ p q : ℕ, n ≤ p ∧ p.Prime ∧ q.Prime ∧ p < q ∧ q - p ≤ 246 := by
  sorry
-- ANCHOR_END: zhang_bounded_prime_gaps__zhang_bounded_prime_gaps

end ProblemZhangBoundedPrimeGaps

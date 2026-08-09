import Mathlib

namespace ProblemWeakGoldbach

-- ANCHOR: weak_goldbach__weak_goldbach
theorem weak_goldbach (n : ℕ) (hn : 5 < n) (hodd : Odd n) :
    ∃ p q r : ℕ, p.Prime ∧ q.Prime ∧ r.Prime ∧ n = p + q + r := by
  sorry
-- ANCHOR_END: weak_goldbach__weak_goldbach

end ProblemWeakGoldbach

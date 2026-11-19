import Mathlib

namespace ProblemZelmanovRestrictedBurnside

-- ANCHOR: zelmanov_restricted_burnside__zelmanov_restricted_burnside
theorem zelmanov_restricted_burnside {m n : ℕ} (hm : 1 ≤ m) (hn : 1 ≤ n) :
    ∃ B : ℕ, ∀ (Q : Type) [Group Q] [Finite Q],
      (∃ g : Fin m → Q, Subgroup.closure (Set.range g) = ⊤) →
      (∀ x : Q, x ^ n = 1) →
      Nat.card Q ≤ B := by
  sorry
-- ANCHOR_END: zelmanov_restricted_burnside__zelmanov_restricted_burnside

end ProblemZelmanovRestrictedBurnside

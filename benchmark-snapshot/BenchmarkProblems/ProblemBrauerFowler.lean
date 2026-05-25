import Mathlib

namespace ProblemBrauerFowler

-- ANCHOR: brauer_fowler__brauer_fowler
theorem brauer_fowler :
    ∃ f : ℕ → ℕ, ∀ (G : Type) [Group G] [Finite G],
      IsSimpleGroup G → (∃ a b : G, a * b ≠ b * a) →
      ∀ t : G, orderOf t = 2 →
        Nat.card G ≤ f (Nat.card (Subgroup.centralizer ({t} : Set G))) := by
  sorry
-- ANCHOR_END: brauer_fowler__brauer_fowler

end ProblemBrauerFowler

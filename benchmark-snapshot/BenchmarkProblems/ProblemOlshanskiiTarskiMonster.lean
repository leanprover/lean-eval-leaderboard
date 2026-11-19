import Mathlib

namespace ProblemOlshanskiiTarskiMonster

-- ANCHOR: olshanskii_tarski_monster__olshanskii_tarski_monster
theorem olshanskii_tarski_monster {p : ℕ} (hp : p.Prime) (hgt : 10 ^ 75 < p) :
    ∃ (G : Type) (_ : Group G),
      Infinite G ∧
      ∀ H : Subgroup G, H ≠ ⊥ → H ≠ ⊤ → IsCyclic H ∧ Nat.card H = p := by
  sorry
-- ANCHOR_END: olshanskii_tarski_monster__olshanskii_tarski_monster

end ProblemOlshanskiiTarskiMonster

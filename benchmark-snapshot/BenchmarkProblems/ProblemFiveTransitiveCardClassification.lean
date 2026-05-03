import Mathlib

namespace ProblemFiveTransitiveCardClassification

-- ANCHOR: five_transitive_card_classification__five_transitive_card_classification
theorem five_transitive_card_classification (G X : Type) [Group G] [Fintype G] [Fintype X]
    [MulAction G X] [FaithfulSMul G X]
    (hcard : 5 ≤ Fintype.card X)
    (h5 : ∀ a b : Fin 5 → X, Function.Injective a → Function.Injective b →
      ∃ g : G, ∀ i, g • a i = b i) :
    let n := Fintype.card X
    Fintype.card G = n.factorial ∨
    (7 ≤ n ∧ Fintype.card G = n.factorial / 2) ∨
    (n = 12 ∧ Fintype.card G = 95040) ∨
    (n = 24 ∧ Fintype.card G = 244823040) := by
  sorry
-- ANCHOR_END: five_transitive_card_classification__five_transitive_card_classification

end ProblemFiveTransitiveCardClassification

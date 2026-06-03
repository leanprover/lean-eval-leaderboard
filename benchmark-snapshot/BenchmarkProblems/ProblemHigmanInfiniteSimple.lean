import Mathlib

namespace ProblemHigmanInfiniteSimple

-- ANCHOR: higman_infinite_simple__higman_infinite_simple
theorem higman_infinite_simple :
    ∃ (n : ℕ) (rels : Set (FreeGroup (Fin n))),
      rels.Finite ∧ IsSimpleGroup (PresentedGroup rels) ∧
        Infinite (PresentedGroup rels) := by
  sorry
-- ANCHOR_END: higman_infinite_simple__higman_infinite_simple

end ProblemHigmanInfiniteSimple

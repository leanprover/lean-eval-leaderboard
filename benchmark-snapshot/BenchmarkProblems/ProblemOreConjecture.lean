import Mathlib.Data.Finite.Defs
import Mathlib.GroupTheory.Commutator.Basic
import Mathlib.GroupTheory.Subgroup.Simple

namespace ProblemOreConjecture

-- ANCHOR: ore_conjecture__ore_conjecture
theorem ore_conjecture (G : Type*) [Group G] [Finite G] [IsSimpleGroup G]
    (hG : ¬ IsMulCommutative G) :
    commutatorSet G = Set.univ := by
  sorry
-- ANCHOR_END: ore_conjecture__ore_conjecture

end ProblemOreConjecture

import TauCeti.GroupTheory.SpecificGroups.CFSG.Classification

namespace ProblemClassificationFiniteSimpleGroups

-- ANCHOR: classification_finite_simple_groups__classification_finite_simple_groups
theorem classification_finite_simple_groups (G : Type) [Group G] [Finite G] [IsSimpleGroup G] :
    ∃ i : TauCeti.CFSGIndex, Nonempty (G ≃* i.Group) := by
  sorry
-- ANCHOR_END: classification_finite_simple_groups__classification_finite_simple_groups

end ProblemClassificationFiniteSimpleGroups

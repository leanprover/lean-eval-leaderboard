import Mathlib

namespace ProblemCompactGroupSemisimple

open Representation

-- ANCHOR: compact_group_semisimple__compact_group_semisimple
theorem compact_group_semisimple {G V : Type*} [Group G] [TopologicalSpace G] [IsTopologicalGroup G] [CompactSpace G]
    [NormedAddCommGroup V] [NormedSpace ℝ V] [FiniteDimensional ℝ V]
    (ρ : Representation ℝ G V)
    (hρ : Continuous fun p : G × V => ρ p.1 p.2) :
    ρ.IsSemisimpleRepresentation := by
  sorry
-- ANCHOR_END: compact_group_semisimple__compact_group_semisimple

end ProblemCompactGroupSemisimple

import Mathlib

namespace ProblemShafarevichSolvableGalois

-- ANCHOR: shafarevich_solvable_galois__shafarevich_solvable_galois
theorem shafarevich_solvable_galois (G : Type*) [Group G] [Finite G] [Group.IsSolvable G] :
    ∃ (K : Type) (_ : Field K) (_ : Algebra ℚ K) (_ : FiniteDimensional ℚ K) (_ : IsGalois ℚ K),
      Nonempty (G ≃* (K ≃ₐ[ℚ] K)) := by
  sorry
-- ANCHOR_END: shafarevich_solvable_galois__shafarevich_solvable_galois

end ProblemShafarevichSolvableGalois

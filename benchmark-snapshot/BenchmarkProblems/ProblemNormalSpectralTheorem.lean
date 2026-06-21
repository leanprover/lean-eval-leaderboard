import Mathlib

namespace ProblemNormalSpectralTheorem

open Matrix

variable {n : Type*} [Fintype n] [DecidableEq n]

-- ANCHOR: normal_spectral_theorem__normal_spectral_theorem
theorem normal_spectral_theorem (A : Matrix n n ℂ) :
    IsStarNormal A ↔
      ∃ U ∈ unitary (Matrix n n ℂ), ∃ d : n → ℂ,
        A = U * diagonal d * star U := by
  sorry
-- ANCHOR_END: normal_spectral_theorem__normal_spectral_theorem

end ProblemNormalSpectralTheorem

import Mathlib

namespace ProblemMartinetTotallyRealTowers

open NumberField

-- ANCHOR: martinet_totally_real_towers__exists_totallyReal_discr_le
theorem exists_totallyReal_discr_le :
    ∃ C : ℝ, 0 < C ∧ ∀ N : ℕ, ∃ d : ℕ, N ≤ d ∧
      ∃ (K : Type) (_ : Field K) (_ : NumberField K) (_ : NumberField.IsTotallyReal K),
        Module.finrank ℚ K = d ∧ |(NumberField.discr K : ℝ)| ≤ C ^ d := by
  sorry
-- ANCHOR_END: martinet_totally_real_towers__exists_totallyReal_discr_le

end ProblemMartinetTotallyRealTowers

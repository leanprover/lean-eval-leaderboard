import Mathlib.NumberTheory.WellApproximable

namespace ProblemDuffinSchaeffer

open MeasureTheory

-- ANCHOR: duffin_schaeffer__duffin_schaeffer
theorem duffin_schaeffer (δ : ℕ → ℝ) (hδ : ∀ n, 0 ≤ δ n) :
    volume (addWellApproximable UnitAddCircle δ) = 1 ↔
      ¬ Summable fun n : ℕ => n.totient * δ n := by
  sorry
-- ANCHOR_END: duffin_schaeffer__duffin_schaeffer

end ProblemDuffinSchaeffer
